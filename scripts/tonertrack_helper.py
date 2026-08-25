#!/usr/bin/env python3
"""
TonerTrack office helper — run on a PC inside the office LAN.

Pulls the printer list and poll interval from the server, checks each listed
IP from this machine, and posts results to the shared dashboard.

  set TONERTRACK_URL=https://tonertrack.onrender.com
  set TONERTRACK_AGENT_TOKEN=tt_...
  python tonertrack_helper.py
  python tonertrack_helper.py --once

Does not scan the network. Only contacts IPs returned by /agent/fleet.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request


def api(url: str, token: str, method: str = "GET", body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Agent-Token": token,
            "User-Agent": "TonerTrackHelper/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def ping_host(ip: str, timeout_sec: int = 2) -> bool:
    """Return True if host responds to a single ping."""
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


def probe_printer(ip: str) -> dict:
    """
    LAN probe from this PC only.
    v1: reachability via ping. Toner still often needs SNMP/vendor later;
    when reachable without toner we report online without a fake %.
    """
    if ping_host(ip):
        return {"ok": True, "status": "online"}
    return {"ok": False, "status_detail": "unreachable"}


def report(base: str, token: str, printer_id: int, result: dict) -> dict:
    body = {"printer_id": printer_id, **result}
    return api(f"{base}/agent/report", token, method="POST", body=body)


def cycle(base: str, token: str) -> int:
    cfg = api(f"{base}/agent/config", token)
    interval = int(cfg.get("poll_interval_seconds") or 900)
    fleet = api(f"{base}/agent/fleet", token)
    printers = fleet.get("printers") or []
    print(f"Poll interval: {interval}s · targets: {len(printers)}", flush=True)
    for p in printers:
        pid = p["id"]
        ip = p.get("ip_address")
        name = p.get("name") or pid
        if not ip:
            continue
        result = probe_printer(ip)
        try:
            out = report(base, token, pid, result)
            status = out.get("status") or result.get("status") or result.get("status_detail")
            print(f"  [{pid}] {name} ({ip}) -> {status}", flush=True)
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            print(f"  [{pid}] {name} report failed HTTP {e.code}: {err}", flush=True)
        except Exception as e:
            print(f"  [{pid}] {name} error: {e}", flush=True)
    return interval


def main() -> int:
    parser = argparse.ArgumentParser(description="TonerTrack LAN helper")
    parser.add_argument("--once", action="store_true", help="Single poll cycle then exit")
    parser.add_argument(
        "--url",
        default=os.environ.get("TONERTRACK_URL", "https://tonertrack.onrender.com"),
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("TONERTRACK_AGENT_TOKEN", ""),
    )
    args = parser.parse_args()
    if not args.token:
        print("Set TONERTRACK_AGENT_TOKEN or pass --token", file=sys.stderr)
        return 2
    base = args.url.rstrip("/")
    print(f"TonerTrack helper → {base}", flush=True)
    try:
        while True:
            interval = cycle(base, args.token)
            if args.once:
                break
            print(f"Sleeping {interval}s …", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopped.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
