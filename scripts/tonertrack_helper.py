#!/usr/bin/env python3
"""
TonerTrack office helper — run on a PC inside the office LAN.

Automatically checks each listed printer for:
  - online / unreachable
  - toner level (%) when the device exposes it (SNMP Printer MIB)

  pip install pysnmp
  set TONERTRACK_URL=https://tonertrack.onrender.com
  set TONERTRACK_AGENT_TOKEN=tt_...
  python tonertrack_helper.py
  python tonertrack_helper.py --once

Only contacts IPs returned by /agent/fleet. Does not scan the subnet.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

# Printer-MIB marker supplies (toner/ink)
OID_SUPPLY_TYPE = "1.3.6.1.2.1.43.11.1.1.5.1"       # prtMarkerSuppliesType
OID_SUPPLY_DESC = "1.3.6.1.2.1.43.11.1.1.6.1"       # description
OID_SUPPLY_MAX = "1.3.6.1.2.1.43.11.1.1.8.1"        # max capacity
OID_SUPPLY_LEVEL = "1.3.6.1.2.1.43.11.1.1.9.1"      # level (-1 / -2 / -3 special)
OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"


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
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def ping_host(ip: str, timeout_sec: int = 2) -> bool:
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout_sec * 1000), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout_sec), ip]
    try:
        r = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_sec + 2,
        )
        return r.returncode == 0
    except Exception:
        return False


def snmp_get(ip: str, oid: str, community: str = "public", timeout: int = 2):
    """Single SNMP GET via pysnmp (sync). Returns Python value or None."""
    try:
        from pysnmp.hlapi import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )
    except ImportError:
        return None

    try:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),  # SNMPv2c
            UdpTransportTarget((ip, 161), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )
        error_indication, error_status, _error_index, var_binds = next(iterator)
        if error_indication or error_status:
            return None
        for var_bind in var_binds:
            return var_bind[1]
    except Exception:
        return None
    return None


def snmp_walk(ip: str, oid_prefix: str, community: str = "public", timeout: int = 2) -> dict:
    """Walk SNMP table; return {index: value}."""
    try:
        from pysnmp.hlapi import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            nextCmd,
        )
    except ImportError:
        return {}

    out: dict = {}
    try:
        for (error_indication, error_status, _error_index, var_binds) in nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid_prefix)),
            lexicographicMode=False,
        ):
            if error_indication or error_status:
                break
            for var_bind in var_binds:
                name, val = var_bind
                oid_str = name.prettyPrint()
                # last numeric sub-id as index
                parts = oid_str.strip(".").split(".")
                idx = parts[-1] if parts else "0"
                out[idx] = val
    except Exception:
        return out
    return out


def _to_int(val) -> int | None:
    try:
        return int(val)
    except Exception:
        try:
            return int(str(val))
        except Exception:
            return None


def read_toner_percent(ip: str, community: str = "public") -> int | None:
    """
    Read toner/ink from Printer-MIB supplies table.
    Prefers black / toner cartridges; returns 0-100 or None.
    """
    levels = snmp_walk(ip, OID_SUPPLY_LEVEL, community)
    maxes = snmp_walk(ip, OID_SUPPLY_MAX, community)
    descs = snmp_walk(ip, OID_SUPPLY_DESC, community)

    if not levels:
        return None

    candidates: list[tuple[int, int]] = []  # (priority, percent)

    for idx, level_v in levels.items():
        level = _to_int(level_v)
        if level is None:
            continue
        # RFC 1759: -1 unknown, -2 unknown but not empty, -3 some remaining
        if level < 0:
            continue
        max_c = _to_int(maxes.get(idx)) if maxes else None
        if max_c is not None and max_c > 0:
            pct = int(round(100.0 * level / max_c))
        elif 0 <= level <= 100:
            pct = level  # some devices already report percent
        else:
            continue
        pct = max(0, min(100, pct))

        desc = str(descs.get(idx, "")).lower() if descs else ""
        # Prefer black toner
        priority = 50
        if "black" in desc or "k " in desc or desc.strip() == "k":
            priority = 0
        elif "toner" in desc:
            priority = 10
        elif "cyan" in desc or "magenta" in desc or "yellow" in desc:
            priority = 80
        candidates.append((priority, pct))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def probe_printer(ip: str, community: str = "public") -> dict:
    """
    Automatic probe from office LAN:
      1) SNMP toner when available
      2) SNMP sysDescr / ping for online
    """
    # Quick reachability
    reachable = ping_host(ip)

    # Try SNMP even if ping filtered (some networks block ICMP)
    sys_descr = snmp_get(ip, OID_SYS_DESCR, community)
    toner = read_toner_percent(ip, community)

    if toner is not None:
        status = "low" if toner <= 20 else "online"
        return {
            "ok": True,
            "status": status,
            "toner_level": toner,
        }

    if sys_descr is not None or reachable:
        # Online but no toner reading — still automatic status, no fake %
        return {
            "ok": True,
            "status": "online",
        }

    return {
        "ok": False,
        "status_detail": "unreachable",
    }


def report(base: str, token: str, printer_id: int, result: dict) -> dict:
    body = {"printer_id": printer_id, **result}
    return api(f"{base}/agent/report", token, method="POST", body=body)


def cycle(base: str, token: str, community: str) -> int:
    cfg = api(f"{base}/agent/config", token)
    interval = int(cfg.get("poll_interval_seconds") or 900)
    fleet = api(f"{base}/agent/fleet", token)
    printers = fleet.get("printers") or []
    print(f"Poll interval: {interval}s · targets: {len(printers)}", flush=True)

    # Detect pysnmp once
    try:
        import pysnmp  # noqa: F401
        snmp_ok = True
    except ImportError:
        snmp_ok = False
        print(
            "WARNING: pysnmp not installed — toner auto-read disabled. "
            "Run: pip install pysnmp",
            flush=True,
        )

    for p in printers:
        pid = p["id"]
        ip = p.get("ip_address")
        name = p.get("name") or str(pid)
        if not ip:
            continue
        if snmp_ok:
            result = probe_printer(ip, community)
        else:
            # ping-only degraded mode
            if ping_host(ip):
                result = {"ok": True, "status": "online"}
            else:
                result = {"ok": False, "status_detail": "unreachable"}
        try:
            out = report(base, token, pid, result)
            toner = out.get("toner_level")
            status = out.get("status") or result.get("status") or result.get("status_detail")
            extra = f" toner={toner}%" if toner is not None else ""
            print(f"  [{pid}] {name} ({ip}) -> {status}{extra}", flush=True)
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            print(f"  [{pid}] {name} report failed HTTP {e.code}: {err}", flush=True)
        except Exception as e:
            print(f"  [{pid}] {name} error: {e}", flush=True)
    return interval


def main() -> int:
    parser = argparse.ArgumentParser(description="TonerTrack LAN helper (auto status + toner)")
    parser.add_argument("--once", action="store_true", help="Single poll cycle then exit")
    parser.add_argument(
        "--url",
        default=os.environ.get("TONERTRACK_URL", "https://tonertrack.onrender.com"),
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("TONERTRACK_AGENT_TOKEN", ""),
    )
    parser.add_argument(
        "--community",
        default=os.environ.get("TONERTRACK_SNMP_COMMUNITY", "public"),
        help="SNMP community string (default public)",
    )
    args = parser.parse_args()
    if not args.token:
        print("Set TONERTRACK_AGENT_TOKEN or pass --token", file=sys.stderr)
        return 2
    base = args.url.rstrip("/")
    print(f"TonerTrack helper → {base}", flush=True)
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
