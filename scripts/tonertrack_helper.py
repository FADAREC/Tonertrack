#!/usr/bin/env python3
"""
TonerTrack office helper - run on a PC on the office LAN.

Automatically:
  - pulls listed printers + poll interval from the server
  - network printers: checks IP from THIS machine (ping + SNMP + web fallback)
  - local/USB printers: checks Windows print queue on THIS machine (no IP)
  - posts online/offline + toner when available to the shared dashboard

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
            "User-Agent": "TonerTrackHelper/1.2",
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
    # Find INTEGER (0x02) or OCTET STRING near the end - enough for supply levels
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


def _toner_from_level_max(level, maximum) -> int | None:
    if level is None or not isinstance(level, int):
        return None
    if level < 0:
        if level in (-2, -3):
            return 0
        return None
    if maximum is not None and isinstance(maximum, int) and maximum > 0:
        return max(0, min(100, int(round(100.0 * level / maximum))))
    if 0 <= level <= 100:
        return level
    return None


def snmp_toner_percent(ip: str, community: str = "public") -> int | None:
    """Try common Printer-MIB supply indexes (mono + color slots)."""
    for idx in (1, 2, 3, 4):
        level_oid = (1, 3, 6, 1, 2, 1, 43, 11, 1, 1, 9, 1, idx)
        max_oid = (1, 3, 6, 1, 2, 1, 43, 11, 1, 1, 8, 1, idx)
        level = snmp_get_v1(ip, level_oid, community)
        maximum = snmp_get_v1(ip, max_oid, community)
        pct = _toner_from_level_max(level, maximum)
        if pct is not None:
            return pct
    return None


def snmp_toner_any_community(ip: str, primary: str = "public") -> int | None:
    communities = []
    for c in (primary, "public", "private"):
        if c and c not in communities:
            communities.append(c)
    for c in communities:
        pct = snmp_toner_percent(ip, c)
        if pct is not None:
            return pct
    return None


def tcp_reachable(ip: str, ports=(9100, 80, 443, 631), timeout: float = 1.5) -> bool:
    for port in ports:
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                return True
        except Exception:
            continue
    return False


def web_toner_percent(ip: str) -> int | None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for url in (f"http://{ip}/", f"https://{ip}/", f"http://{ip}/hp/device/this.LCDispatcher"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TonerTrackHelper/1.2"})
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
    Priority: SNMP toner (multi-index/community) → web → ping/tcp online.
    """
    toner = snmp_toner_any_community(ip, community)
    if toner is None:
        toner = web_toner_percent(ip)

    if toner is not None:
        status = "low" if toner <= 20 else "online"
        return {"ok": True, "status": status, "toner_level": toner, "status_detail": None}

    online = ping_host(ip) or tcp_reachable(ip)

    if online:
        return {"ok": True, "status": "online", "status_detail": None}

    # SNMP sysDescr as reachability when ICMP/TCP blocked but SNMP open
    for c in (community, "public"):
        if not c:
            continue
        descr = snmp_get_v1(ip, OID_SYS_DESCR, c)
        if descr is not None:
            return {"ok": True, "status": "online", "status_detail": None}

    return {
        "ok": False,
        "status": "unknown",
        "status_detail": "unreachable",
    }



def _powershell_json(script: str):
    """Run PowerShell and parse JSON; return None on failure."""
    if platform.system().lower() != "windows":
        return None
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (completed.stdout or "").strip()
        if completed.returncode != 0 or not out:
            return None
        return json.loads(out)
    except Exception:
        return None


def list_local_printers() -> list[dict]:
    data = _powershell_json(
        "Get-Printer | Select-Object Name, PrinterStatus, Type | ConvertTo-Json -Compress"
    )
    if data is None:
        return []
    if isinstance(data, dict):
        data = [data]
    return data if isinstance(data, list) else []


def probe_local_printer(windows_name: str) -> dict:
    """Check a USB/local queue by Windows printer name (must run on that PC)."""
    name = (windows_name or "").strip()
    if not name:
        return {"ok": False, "status": "unknown", "status_detail": "unreachable"}

    if platform.system().lower() != "windows":
        return {
            "ok": False,
            "status": "unknown",
            "status_detail": "unreachable",
        }

    # Exact match first, then case-insensitive
    safe = name.replace("'", "''")
    data = _powershell_json(
        f"Get-Printer -Name '{safe}' -ErrorAction SilentlyContinue | "
        "Select-Object Name, PrinterStatus | ConvertTo-Json -Compress"
    )
    if not data:
        # fallback: list and match
        for row in list_local_printers():
            n = str(row.get("Name") or "")
            if n.lower() == name.lower():
                data = row
                break
    if isinstance(data, list):
        data = data[0] if data else None
    if not data:
        return {"ok": False, "status": "unknown", "status_detail": "unreachable"}

    # PrinterStatus: 0 Other, 1 Unknown, 2 Idle, 3 Printing, 4 Warmup, ...
    # Also string forms on some hosts
    st = data.get("PrinterStatus")
    try:
        code = int(st)
    except (TypeError, ValueError):
        code = None
        text = str(st or "").lower()
        if any(x in text for x in ("error", "offline", "paused", "not available")):
            return {"ok": False, "status": "unknown", "status_detail": "unreachable"}
        if any(x in text for x in ("idle", "printing", "warmup", "normal", "ready")):
            return {"ok": True, "status": "online", "status_detail": None}
        return {"ok": True, "status": "online", "status_detail": None}

    # MSDN-ish: 1 unknown, 2 idle, 3 printing, 4 warmup are fine; high bits often errors
    if code in (2, 3, 4, 5, 6):
        return {"ok": True, "status": "online", "status_detail": None}
    if code in (1, 0):
        return {"ok": True, "status": "online", "status_detail": None}
    # 7+ often paused/error/offline depending on driver
    if code >= 7:
        return {"ok": False, "status": "unknown", "status_detail": "unreachable"}
    return {"ok": True, "status": "online", "status_detail": None}


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
        mode = (p.get("connection_mode") or "manual").lower()
        if mode == "local":
            win_name = (p.get("local_name") or name or "").strip()
            result = probe_local_printer(win_name)
            target_label = f"local:{win_name}"
        else:
            if not ip:
                print(f"  [{pid}] {name} skipped (no IP)", flush=True)
                continue
            result = probe_printer(ip, community)
            target_label = ip
        try:
            out = report(base, token, pid, result)
            status = out.get("status") or result.get("status") or result.get("status_detail")
            toner = out.get("toner_level")
            extra = f" toner={toner}%" if toner is not None else ""
            print(f"  [{pid}] {name} ({target_label}) -> {status}{extra}", flush=True)
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
