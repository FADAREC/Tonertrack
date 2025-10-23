import asyncio
import logging
import re
import subprocess
import platform

import httpx
import nmap
from bs4 import BeautifulSoup
from fastapi import HTTPException

from pysnmp.hlapi.asyncio import (
    getCmd,
    nextCmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity
)

try:
    import cups
except ImportError:
    cups = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------- NETWORK SCAN Mechs ------------------------

async def scan_network(subnet: str):
    """
    Asynchronously scan a subnet for devices with open printer ports.
    """
    loop = asyncio.get_running_loop()
    nm = nmap.PortScanner()
    try:
        await loop.run_in_executor(None, nm.scan, subnet, '-p 80,161,443,9100 --open')
        devices = []
        for host in nm.all_hosts():
            if nm[host].state() == 'up':
                open_ports = []
                for proto in ['tcp', 'udp']:
                    if proto in nm[host]:
                        open_ports.extend(list(nm[host][proto].keys()))
                if open_ports:
                    devices.append({'ip': host, 'ports': open_ports})
        return devices
    except Exception as e:
        logger.error(f"Nmap scan error for subnet {subnet}: {e}")
        raise HTTPException(status_code=500, detail=f"Network scan failed: {e}")

# ------------------------- SNMP HELPERS -----------------------------

SYS_DESCR_OID = '1.3.6.1.2.1.1.1.0'
PRINTER_NAME_OID = '1.3.6.1.2.1.43.5.1.1.16.1'
PRINTER_STATUS_OID = '1.3.6.1.2.1.43.16.5.1.2.1.1'

async def perform_snmp_get(ip, oid, community="public", timeout=3):
    try:
        errorIndication, errorStatus, _, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        if errorIndication or errorStatus:
            return None
        return varBinds[0][1] if varBinds else None
    except Exception:
        return None

async def is_printer_via_snmp(ip, community="public"):
    sys_descr = await perform_snmp_get(ip, SYS_DESCR_OID, community)
    if sys_descr:
        text = str(sys_descr).lower()
        for kw in ["printer", "laserjet", "deskjet", "canon", "epson", "brother"]:
            if kw in text:
                return text
    return None

# ----------------------- PING MODE ------------------------------

async def is_device_online(ip: str) -> bool:
    """
    Simple async ping check to confirm if device is reachable.
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    cmd = ["ping", param, "1", "-W", "2", ip]

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(None, subprocess.run, cmd, capture_output := True)
        return result.returncode == 0
    except Exception:
        return False

# ---------------------- WEB SCRAPING MODE ---------------------------

async def get_status_via_web(ip: str):
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        for proto in ["https", "http"]:
            for port in ["", ":443", ":80"]:
                if proto == "https" and port == ":80": continue
                if proto == "http" and port == ":443": continue

                url = f"{proto}://{ip}{port}"
                try:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")

                    toner_levels = {}
                    errors = []

                    for sel in [
                        {'toner': 'div.tonerGauge span.level', 'error': 'div#alerts li'},
                        {'toner': '.supply-level', 'error': '.alert-message'},
                        {'toner': '[class*="toner"] [class*="level"]', 'error': '[class*="error"]'}
                    ]:
                        toner_elems = soup.select(sel['toner'])
                        error_elems = soup.select(sel['error'])

                        for e in toner_elems:
                            match = re.search(r'(\d+)%', e.get_text())
                            if match:
                                toner_levels[len(toner_levels)] = int(match.group(1))

                        for e in error_elems:
                            txt = e.get_text().strip()
                            if txt and txt not in errors:
                                errors.append(txt)

                        if toner_levels or errors:
                            return toner_levels, errors
                except Exception:
                    continue
    raise ValueError("No accessible web interface found")

# --- MAIN STATUS RETRIEVAL---

async def get_printer_status(ip: str, connection_mode: str, community: str = "public"):
    """
    Tries SNMP, WEB, or PING depending on connection_mode.
    """
    try:
        if connection_mode == "snmp":
            info = await is_printer_via_snmp(ip, community)
            if info: return {"method": "snmp", "status": "online", "details": info}
            return await get_status_via_web(ip)
        elif connection_mode == "web":
            return await get_status_via_web(ip)
        elif connection_mode == "ping":
            online = await is_device_online(ip)
            return {"method": "ping", "status": "online" if online else "offline"}
        else:
            raise ValueError(f"Invalid mode: {connection_mode}")
    except Exception as e:
        # fallback chain
        if connection_mode != "ping":
            online = await is_device_online(ip)
            if online:
                return {"method": "ping", "status": "online", "fallback_error": str(e)}
        raise HTTPException(status_code=500, detail=f"All methods failed: {e}")

# ---- CUPS PRINT JOB HELPERS ---

async def get_print_jobs():
    if not cups:
        raise HTTPException(status_code=501, detail="CUPS not installed on server")
    conn = cups.Connection()
    return conn.getJobs()

async def simulate_job(printer_id: int, user: str, document: str, pages: int):
    if not cups:
        raise HTTPException(status_code=501, detail="CUPS not installed")
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = list(printers.keys())[0]
    job_id = conn.printFile(printer_name, document, "Simulated Job", {})
    return job_id
