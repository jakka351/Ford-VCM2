#!/usr/bin/env python3
# VCM II telnet driver. Talks to the user's own device at 192.168.171.2.
# Read-only by default: run() executes commands, dump() pulls data via base64.
import socket, time, telnetlib, base64, hashlib, sys

HOST = "192.168.171.2"
PORT = 23
TAG  = "7f3a91"

def _split(tok):
    # Build an echo whose ON-WIRE command text does NOT contain the printed token,
    # so read-until never matches the terminal echo of the command itself.
    return tok[:3] + '""' + tok[3:]

START = f"VCMSTART_{TAG}"
END   = f"VCMEND_{TAG}="

def reachable(timeout=5):
    try:
        s = socket.create_connection((HOST, PORT), timeout)
        s.close()
        return True
    except OSError as e:
        print("UNREACHABLE:", e)
        return False

class VCM:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tn = telnetlib.Telnet(HOST, PORT, timeout=20)
        self.banner = self._drain(2.0)
        b = self.banner.lower()
        if b"login:" in b:
            self.tn.write(b"root\n")
            time.sleep(0.8)
            self.banner += self._drain(1.5)
            if b"password:" in self.banner.lower():
                # stock test-mode is passwordless; try empty line
                self.tn.write(b"\n")
                time.sleep(0.8)
                self.banner += self._drain(1.5)
        # wake the prompt
        self.tn.write(b"\n")
        self._drain(0.6)

    def _drain(self, secs):
        end = time.time() + secs
        buf = b""
        while time.time() < end:
            try:
                chunk = self.tn.read_very_eager()
            except EOFError:
                break
            if chunk:
                buf += chunk
            else:
                time.sleep(0.05)
        return buf

    def _read_to(self, token, overall=120, idle=8):
        """Read until token (bytes) seen; stop on idle-timeout or overall cap."""
        token = token.encode() if isinstance(token, str) else token
        buf = bytearray()
        deadline = time.time() + overall
        last = time.time()
        while time.time() < deadline:
            try:
                chunk = self.tn.read_very_eager()
            except EOFError:
                break
            if chunk:
                buf += chunk
                last = time.time()
                if token in buf:
                    break
            else:
                if time.time() - last > idle:
                    break
                time.sleep(0.05)
        return bytes(buf)

    def run(self, cmd, overall=120, idle=8):
        pre  = f'echo "{_split(START)}"'
        post = f'echo "{_split(END)}$?="'
        line = f'{pre} ; {cmd} ; {post}\n'
        self.tn.write(line.encode())
        raw = self._read_to(END, overall=overall, idle=idle)
        s = raw.find(START.encode())
        e = raw.find(END.encode())
        rc = None
        if e != -1:
            tail = raw[e+len(END):e+len(END)+8]
            digits = b""
            for c in tail:
                if 48 <= c <= 57:
                    digits += bytes([c])
                else:
                    break
            rc = int(digits) if digits else None
        if s == -1 or e == -1:
            out = raw
        else:
            nl = raw.find(b"\n", s)
            out = raw[nl+1:e] if nl != -1 else raw[s+len(START):e]
        text = out.replace(b"\r\n", b"\n").decode("utf-8", "replace").rstrip("\n")
        if self.verbose:
            print(f"$ {cmd}\n{text}\n[rc={rc}]")
        return text, rc

    def dump(self, remote_producer, local_path, expect_md5=None, overall=1800, idle=30):
        """remote_producer: shell cmd whose stdout is base64 of the payload."""
        pre  = f'echo "{_split(START)}"'
        post = f'echo "{_split(END)}$?="'
        line = f'{pre} ; {remote_producer} ; {post}\n'
        self.tn.write(line.encode())
        raw = self._read_to(END, overall=overall, idle=idle)
        s = raw.find(START.encode())
        e = raw.find(END.encode())
        if s == -1 or e == -1:
            raise RuntimeError(f"markers not found (got {len(raw)} bytes); tail={raw[-200:]!r}")
        nl = raw.find(b"\n", s)
        blob = raw[nl+1:e]
        b64 = bytes(c for c in blob if c not in b"\r\n \t")
        data = base64.b64decode(b64, validate=False)
        with open(local_path, "wb") as f:
            f.write(data)
        md5 = hashlib.md5(data).hexdigest()
        return len(data), md5

    def close(self):
        try:
            self.tn.write(b"exit\n")
            time.sleep(0.2)
            self.tn.close()
        except Exception:
            pass
