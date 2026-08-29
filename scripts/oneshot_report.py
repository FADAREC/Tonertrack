#!/usr/bin/env python3
"""
One-shot LAN reporter for TonerTrack (pilot).

Run this on a machine that can reach the printers (office PC), not from the cloud.

  export TONERTRACK_URL=https://tonertrack.onrender.com
  export TONERTRACK_AGENT_TOKEN=tt_...   # from admin POST /agent/tokens - never commit
  python scripts/oneshot_report.py --printer-id 1 --toner 42
  python scripts/oneshot_report.py --printer-id 1 --unreachable
  python scripts/oneshot_report.py --printer-id 1 --device-reported

PILOT: single-tenant deployment. Token can affect any printer on that instance.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Post one printer status report to TonerTrack")
    parser.add_argument("--printer-id", type=int, required=True)
    parser.add_argument("--toner", type=int, default=None, help="0-100 on successful read")
    parser.add_argument("--status", default=None, help="online|low|offline|unknown")
    parser.add_argument("--unreachable", action="store_true", help="Probe failed to reach device")
    parser.add_argument(
        "--device-reported",
        action="store_true",
        help="Reachable; device reports offline/error",
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("TONERTRACK_URL", "https://tonertrack.onrender.com"),
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("TONERTRACK_AGENT_TOKEN", ""),
        help="Or set TONERTRACK_AGENT_TOKEN",
    )
    args = parser.parse_args()

    if not args.token:
        print("Missing token: set TONERTRACK_AGENT_TOKEN or pass --token", file=sys.stderr)
        return 2
    if args.unreachable and args.device_reported:
        print("Use only one of --unreachable or --device-reported", file=sys.stderr)
        return 2

    if args.unreachable:
        body = {
            "printer_id": args.printer_id,
            "ok": False,
            "status_detail": "unreachable",
        }
    elif args.device_reported:
        body = {
            "printer_id": args.printer_id,
            "ok": True,
            "status": args.status or "offline",
            "status_detail": "device_reported",
        }
    else:
        body = {
            "printer_id": args.printer_id,
            "ok": True,
            "status": args.status,
            "toner_level": args.toner,
        }
        # drop nulls so we don't send explicit nulls unnecessarily
        body = {k: v for k, v in body.items() if v is not None}

    url = args.url.rstrip("/") + "/agent/report"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Agent-Token": args.token,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            print(raw)
            return 0
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
