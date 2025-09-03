from pysnmp.hlapi import *
import nmap
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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