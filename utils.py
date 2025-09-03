from pysnmp.hlapi import *
import nmap
import logging
import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRINTER_MODEL_OID = '1.3.6.1.2.1.25.3.2.1.3.1'  # Or use sysDescr
TONER_LEVEL_OIDS = {
    'black': '1.3.6.1.2.1.43.11.1.1.9.1.1',  # Max capacity example; actual % = current/max *100
    # Add cyan/magenta/yellow for color printers: .2, .3, .4
}
ERROR_OID = '1.3.6.1.2.1.43.18.1.1.8.1.1'  # Alert description

def is_printer_via_snmp(ip: str, community: str = "public"):
    """
    Quick SNMP check for printer: Query sysDescr OID (1.3.6.1.2.1.1.1.0)
    Returns model if it's a printer-like device, else None.
    """
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community, mpModel=0),
                   UdpTransportTarget((ip, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')))
        )
        if errorIndication:
            logger.error(f"SNMP error for {ip}: {errorIndication}")
            return None
        elif errorStatus:
            logger.error(f"SNMP status error for {ip}")
            return None
        else:
            sys_descr = str(varBinds[0][1])
            if "printer" in sys_descr.lower() or "hp" in sys_descr.lower():  # Basic heuristic; improve later
                return sys_descr  # e.g., "HP LaserJet MFP M426fdw"
            return None
    except Exception as e:
        logger.error(f"SNMP exception for {ip}: {e}")
        return None

def scan_network(subnet: str):
    """
    Scan subnet with nmap for printer ports.
    Returns list of dicts: {'ip': str, 'ports': list}
    """
    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=subnet, arguments='-p 80,161,443,9100 --open')
        devices = []
        for host in nm.all_hosts():
            open_ports = [port for port in nm[host]['tcp'] if nm[host]['tcp'][port]['state'] == 'open']
            if open_ports:
                devices.append({'ip': host, 'ports': open_ports})
        return devices
    except Exception as e:
        logger.error(f"Scan error: {e}")
        raise

async def get_status_via_web(ip: str):
    """
    Scrape HP EWS web interface for status.
    Returns (toner_levels, errors) or raises exception.
    """
    try:
        url = f"http://{ip}"  # Or https if supported; add toggle later
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HP EWS parsing: Adapt based on model (inspect page source)
        toner_section = soup.find('div', class_='tonerGauge')  # Example class; may vary
        toner_levels = {}
        if toner_section:
            # Parse gauges, e.g., find spans with % text
            gauges = toner_section.find_all('span', class_='level')
            colors = ['black', 'cyan', 'magenta', 'yellow']
            for i, gauge in enumerate(gauges):
                if i < len(colors):
                    level_text = gauge.text.strip().rstrip('%')
                    toner_levels[colors[i]] = int(level_text) if level_text.isdigit() else 0
        
        errors = []
        error_section = soup.find('div', id='alerts')  # Example
        if error_section:
            errors = [err.text.strip() for err in error_section.find_all('li')]
        
        if not toner_levels and not errors:
            raise ValueError("No data parsed")
        
        return toner_levels, errors
    except Exception as e:
        logger.error(f"Web scrape failed for {ip}: {e}")
        raise

async def get_status_via_snmp(ip: str, community: str = "public"):
    """
    Query SNMP for status.
    Returns (toner_levels, errors)
    """
    try:
        toner_levels = {}
        for color, oid in TONER_LEVEL_OIDS.items():
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       CommunityData(community, mpModel=0),
                       UdpTransportTarget((ip, 161), timeout=2, retries=1),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid)))
            )
            if not errorIndication and not errorStatus:
                level = int(varBinds[0][1])
                toner_levels[color] = level if level >= 0 else 0  # -3 often means unknown
        
        errors = []
        # Query error OID (multi-row table; simplify to first)
        iterator = getCmd(SnmpEngine(),
                          CommunityData(community, mpModel=0),
                          UdpTransportTarget((ip, 161)),
                          ContextData(),
                          ObjectType(ObjectIdentity(ERROR_OID)))
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        if not errorIndication and not errorStatus and varBinds:
            errors = [str(varBinds[0][1])]
        
        return toner_levels, errors
    except Exception as e:
        logger.error(f"SNMP query failed for {ip}: {e}")
        raise

async def get_printer_status(ip: str, connection_mode: str, community: str = "public"):
    try:
        if connection_mode == "web":
            return await get_status_via_web(ip)
        else:
            return await get_status_via_snmp(ip, community)
    except:
        # Fallback to the other mode
        fallback_mode = "snmp" if connection_mode == "web" else "web"
        if fallback_mode == "snmp":
            return await get_status_via_snmp(ip, community)
        else:
            return await get_status_via_web(ip)