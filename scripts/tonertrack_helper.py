#!/usr/bin/env python3
"""
TonerTrack office helper — run on a PC on the office LAN.

Automatically:
  - pulls listed printers + poll interval from the server
  - checks each IP from THIS machine (ping + SNMP toner + web fallback)
  - posts online/offline + toner_level to the shared dashboard

  set TONERTRACK_URL=https://tonertrack.onrender.com
  set TONERTRACK_AGENT_TOKEN=tt_...
  python tonertrack_helper.py
  python tonertrack_helper.py --once

No network scan. Only IPs from /agent/fleet.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import ssl

# Printer-MIB marker supplies (black / first cartridge commonly .1.1)
OID_SUPPLY_LEVEL = (1, 3, 6, 1, 2, 1, 43, 11, 1, 1, 9, 1, 1)
OID_SUPPLY_MAX = (1, 3, 6, 1, 2, 1, 43, 11, 1, 1, 8, 1, 1)
OID_SYS_DESCR = (1, 3, 6, 1, 2, 1, 1, 1, 0)


def api(url: str, token: str, method: str = "GET", body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Agent-Token": token,
            "User-Agent": "TonerTrackHelper/1.1",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def ping_host(ip: str, timeout_sec: int = 2) -> bool:
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout_sec * 1000), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout_sec), ip]
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout_sec + 2)
        return r.returncode == 0
    except Exception:
        return False


# --- minimal SNMPv1 GET (no pysnmp required on the office PC) ---

def _encode_length(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    out = []
    x = n
    while x:
        out.append(x & 0xFF)
        x >>= 8
    out.reverse()
    return bytes([0x80 | len(out)]) + bytes(out)


def _encode_oid(oid: tuple) -> bytes:
    body = bytearray([oid[0] * 40 + oid[1]])
    for part in oid[2:]:
        if part < 0x80:
            body.append(part)
        else:
            stack = []
            val = part
            stack.append(val & 0x7F)
            val >>= 7
            while val:
                stack.append(0x80 | (val & 0x7F))
                val >>= 7
            body.extend(reversed(stack))
    return bytes([0x06]) + _encode_length(len(body)) + bytes(body)


def _encode_string(s: str) -> bytes:
    b = s.encode("ascii")
    return bytes([0x04]) + _encode_length(len(b)) + b


def _encode_null() -> bytes:
    return b"\x05\x00"


def _encode_int(n: int) -> bytes:
    if n == 0:
        body = b"\x00"
    else:
        neg = n < 0
        n = abs(n)
        body = bytearray()
        while n:
            body.insert(0, n & 0xFF)
            n >>= 8
        if not neg and body[0] & 0x80:
            body.insert(0, 0)
    return bytes([0x02]) + _encode_length(len(body)) + bytes(body)


def _encode_seq(content: bytes) -> bytes:
    return bytes([0x30]) + _encode_length(len(content)) + content


def snmp_get_v1(ip: str, oid: tuple, community: str = "public", timeout: float = 2.0):
    """Return Python int/str or None."""
    req_id = random.randint(1, 0x7FFFFFFF)
    pdu = _encode_seq(
        _encode_int(req_id)
        + _encode_int(0)
        + _encode_int(0)
        + _encode_seq(_encode_seq(_encode_oid(oid) + _encode_null()))
    )
    msg = _encode_seq(_encode_int(0) + _encode_string(community) + bytes([0xA0]) + _encode_length(len(pdu)) + pdu)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(msg, (ip, 161))
        data, _ = sock.recvfrom(4096)
    except Exception:
        return None
    finally:
        sock.close()
    # Find INTEGER (0x02) or OCTET STRING near the end — enough for supply levels
    i = 0
    values = []
    while i < len(data) - 2:
        tag = data[i]
        ln = data[i + 1]
        if ln & 0x80:
            i += 1
            continue
        if tag == 0x02 and ln <= 8:
            val = 0
            for b in data[i + 2 : i + 2 + ln]:
                val = (val << 8) | b
            values.append(val)
            i += 2 + ln
            continue
        if tag == 0x04 and ln < 200:
            try:
                values.append(data[i + 2 : i + 2 + ln].decode("utf-8", errors="replace"))
            except Exception:
                pass
            i += 2 + ln
            continue
        i += 1
    # Last integer in varbind is usually the value
    ints = [v for v in values if isinstance(v, int)]
    if len(ints) >= 2:
        return ints[-1]
    if ints:
        return ints[-1]
    strs = [v for v in values if isinstance(v, str)]
    return strs[-1] if strs else None


def snmp_toner_percent(ip: str, community: str = "public") -> int | None:
    level = snmp_get_v1(ip, OID_SUPPLY_LEVEL, community)
    maximum = snmp_get_v1(ip, OID_SUPPLY_MAX, community)
    if level is None or not isinstance(level, int):
        return None
    # Some devices report -1 / -2 / -3 for unknown / low / empty
    if level < 0:
        if level in (-2, -3):
            return 0
        return None
    if maximum is not None and isinstance(maximum, int) and maximum > 0:
        return max(0, min(100, int(round(100.0 * level / maximum))))
    # Already a percentage on some firmwares
    if 0 <= level <= 100:
        return level
    return None


def web_toner_percent(ip: str) -> int | None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for url in (f"http://{ip}/", f"https://{ip}/", f"http://{ip}/hp/device/this.LCDispatcher"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TonerTrackHelper/1.1"})
            with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
            # common patterns
            for pat in (
                r"(\d+)\s*%\s*(?:black|toner|cartridge)",
                r"(?:black|toner|cartridge)[^%]{0,40}?(\d+)\s*%",
                r"supply[^%]{0,40}?(\d+)\s*%",
                r"toner[^%]{0,40}?(\d+)",
            ):
                m = re.search(pat, text, re.I)
                if m:
                    n = int(m.group(1))
                    if 0 <= n <= 100:
                        return n
        except Exception:
            continue
    return None


def probe_printer(ip: str, community: str = "public") -> dict:
    """
    Automatic online + toner from the LAN.
    Priority: SNMP toner → web toner → ping-only online.
    """
    online = ping_host(ip)
    toner = snmp_toner_percent(ip, community)
    if toner is None:
        toner = web_toner_percent(ip)

    # SNMP response without ping (some devices block ICMP)
    if toner is not None:
        status = "low" if toner <= 20 else "online"
        return {"ok": True, "status": status, "toner_level": toner}

    if online:
        # Reachable but no toner metric — still automatic online, no fake %
        return {"ok": True, "status": "online"}

    # Try SNMP sysDescr as reachability if ping failed
    descr = snmp_get_v1(ip, OID_SYS_DESCR, community)
    if descr is not None:
        return {"ok": True, "status": "online"}

    return {"ok": False, "status_detail": "unreachable"}


def report(base: str, token: str, printer_id: int, result: dict) -> dict:
    body = {"printer_id": printer_id, **result}
    return api(f"{base}/agent/report", token, method="POST", body=body)


def cycle(base: str, token: str, community: str) -> int:
    cfg = api(f"{base}/agent/config", token)
    interval = int(cfg.get("poll_interval_seconds") or 900)
    fleet = api(f"{base}/agent/fleet", token)
    printers = fleet.get("printers") or []
    print(f"Poll interval: {interval}s · targets: {len(printers)}", flush=True)
    for p in printers:
        pid = p["id"]
        ip = p.get("ip_address")
        name = p.get("name") or str(pid)
        if not ip:
            continue
        result = probe_printer(ip, community)
        try:
            out = report(base, token, pid, result)
            status = out.get("status") or result.get("status") or result.get("status_detail")
            toner = out.get("toner_level")
            extra = f" toner={toner}%" if toner is not None else ""
            print(f"  [{pid}] {name} ({ip}) -> {status}{extra}", flush=True)
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            print(f"  [{pid}] {name} report failed HTTP {e.code}: {err}", flush=True)
        except Exception as e:
            print(f"  [{pid}] {name} error: {e}", flush=True)
    return interval


def main() -> int:
    parser = argparse.ArgumentParser(description="TonerTrack LAN helper (auto online + toner)")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--url", default=os.environ.get("TONERTRACK_URL", "https://tonertrack.onrender.com"))
    parser.add_argument("--token", default=os.environ.get("TONERTRACK_AGENT_TOKEN", ""))
    parser.add_argument(
        "--community",
        default=os.environ.get("TONERTRACK_SNMP_COMMUNITY", "public"),
        help="SNMP community (default public)",
    )
    args = parser.parse_args()
    if not args.token:
        print("Set TONERTRACK_AGENT_TOKEN or pass --token", file=sys.stderr)
        return 2
    base = args.url.rstrip("/")
    print(f"TonerTrack helper → {base} (auto online + toner)", flush=True)
    try:
        while True:
            interval = cycle(base, args.token, args.community)
            if args.once:
                break
            print(f"Sleeping {interval}s …", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopped.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
