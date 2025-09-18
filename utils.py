import asyncio
import logging
import re  # Added for regex in web parsing

import httpx  # Use httpx for async web requests
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Network Scanning ---

async def scan_network(subnet: str):
    """
    Asynchronously scan a subnet with nmap for printer ports without blocking.
    Returns a list of dicts: {'ip': str, 'ports': list}
    """
    loop = asyncio.get_running_loop()
    nm = nmap.PortScanner()
    try:
        # Run the blocking nmap scan in a separate thread
        await loop.run_in_executor(
            None, nm.scan, subnet, '-p 80,161,443,9100 --open'
        )
        devices = []
        for host in nm.all_hosts():
            if nm[host].state() == 'up':
                open_ports = []
                # Check both TCP and UDP protocols
                for protocol in ['tcp', 'udp']:
                    if protocol in nm[host]:
                        open_ports.extend(list(nm[host][protocol].keys()))
                if open_ports:
                    devices.append({'ip': host, 'ports': open_ports})
        return devices
    except Exception as e:
        logger.error(f"Nmap scan error for subnet {subnet}: {e}")
        raise HTTPException(status_code=500, detail=f"Network scan failed: {e}")

# --- Printer Status Retrieval ---

# Standard Printer MIB OIDs (RFC 3805)
SYS_DESCR_OID = '1.3.6.1.2.1.1.1.0'
SYS_OBJECT_ID_OID = '1.3.6.1.2.1.1.2.0'

# Printer-specific OIDs
PRINTER_NAME_OID = '1.3.6.1.2.1.43.5.1.1.16.1'
PRINTER_STATUS_OID = '1.3.6.1.2.1.43.16.5.1.2.1.1'

# Supply level OIDs (more reliable for modern printers)
SUPPLY_DESCRIPTION_OID = '1.3.6.1.2.1.43.11.1.1.6.1'
SUPPLY_LEVEL_OID = '1.3.6.1.2.1.43.11.1.1.9.1'
SUPPLY_MAX_CAPACITY_OID = '1.3.6.1.2.1.43.11.1.1.8.1'

async def perform_snmp_get(ip: str, oid: str, community: str = "public", timeout: int = 3):
    """
    Helper function to perform SNMP GET operations with proper error handling.
    Compatible with pysnmp 6.x
    """
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        
        if errorIndication:
            logger.debug(f"SNMP error indication for {ip} OID {oid}: {errorIndication}")
            return None
        elif errorStatus:
            logger.debug(f"SNMP error status for {ip} OID {oid}: {errorStatus.prettyPrint()}")
            return None
        else:
            return varBinds[0][1] if varBinds else None
            
    except Exception as e:
        logger.debug(f"SNMP exception for {ip} OID {oid}: {e}")
        return None

async def perform_snmp_walk(ip: str, oid: str, community: str = "public", timeout: int = 3):
    """
    Helper function to perform SNMP WALK operations using nextCmd.
    Compatible with pysnmp 6.x (ensure await in caller)
    """
    results = []
    try:
        async for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False,
            maxRows=50  # Limit to prevent infinite loops
        ):
            if errorIndication:
                logger.debug(f"SNMP walk error indication for {ip}: {errorIndication}")
                break
            elif errorStatus:
                logger.debug(f"SNMP walk error status for {ip}: {errorStatus.prettyPrint()}")
                break
            else:
                for varBind in varBinds:
                    # Check if we're still in the subtree we want
                    if not str(varBind[0]).startswith(oid):
                        return results
                    results.append(varBind)
                    
    except Exception as e:
        logger.debug(f"SNMP walk exception for {ip}: {e}")
    
    return results

async def is_printer_via_snmp(ip: str, community: str = "public"):
    """
    Async SNMP check for printer: Queries sysDescr and sysObjectID.
    Returns model description if it's a printer-like device, else None.
    """
    try:
        # Get system description
        sys_descr = await perform_snmp_get(ip, SYS_DESCR_OID, community)
        
        if sys_descr is None:
            return None
            
        sys_descr_str = str(sys_descr)
        logger.debug(f"System description for {ip}: {sys_descr_str}")
        
        # Check for common printer keywords
        printer_keywords = [
            "printer", "laserjet", "officejet", "deskjet", "colorlaserjet",
            "pagewide", "envy", "designjet", "photosmart", "canon", "epson",
            "brother", "xerox", "lexmark", "ricoh", "kyocera", "mfp", "multifunction"
        ]
        
        if any(keyword in sys_descr_str.lower() for keyword in printer_keywords):
            return sys_descr_str
            
        # If system description doesn't contain printer keywords,
        # try to get printer-specific OID to confirm
        printer_name = await perform_snmp_get(ip, PRINTER_NAME_OID, community)
        if printer_name is not None:
            return f"{sys_descr_str} (Printer: {str(printer_name)})"
            
        return None
        
    except Exception as e:
        logger.error(f"Exception during SNMP printer check for {ip}: {e}")
        return None

async def get_status_via_snmp(ip: str, community: str = "public"):
    """
    Asynchronously query SNMP for supply levels and printer status.
    Uses standard Printer MIB (RFC 3805) for better compatibility.
    """
    try:
        # Get supply information using SNMP walk
        supply_descriptions = await perform_snmp_walk(ip, SUPPLY_DESCRIPTION_OID, community)
        supply_levels = await perform_snmp_walk(ip, SUPPLY_LEVEL_OID, community)
        supply_max_capacities = await perform_snmp_walk(ip, SUPPLY_MAX_CAPACITY_OID, community)
        
        # Parse supply information
        toner_levels = {}
        
        # Create mapping of supply information
        for i, desc_var in enumerate(supply_descriptions):
            try:
                supply_desc = str(desc_var[1]).lower()
                supply_index = str(desc_var[0]).split('.')[-1]
                
                # Find corresponding level and max capacity
                current_level = None
                max_capacity = None
                
                for level_var in supply_levels:
                    if str(level_var[0]).endswith(f'.{supply_index}'):
                        current_level = int(level_var[1])
                        break
                
                for max_var in supply_max_capacities:
                    if str(max_var[0]).endswith(f'.{supply_index}'):
                        max_capacity = int(max_var[1])
                        break
                
                if current_level is not None and max_capacity is not None and max_capacity > 0:
                    percentage = min(100, max(0, int((current_level / max_capacity) * 100)))
                    
                    # Map supply description to color
                    if any(keyword in supply_desc for keyword in ['black', 'bk']):
                        toner_levels['black'] = percentage
                    elif any(keyword in supply_desc for keyword in ['cyan', 'cy']):
                        toner_levels['cyan'] = percentage
                    elif any(keyword in supply_desc for keyword in ['magenta', 'mg']):
                        toner_levels['magenta'] = percentage
                    elif any(keyword in supply_desc for keyword in ['yellow', 'yl']):
                        toner_levels['yellow'] = percentage
                    elif any(keyword in supply_desc for keyword in ['toner', 'cartridge', 'ink']):
                        # Generic toner/ink - use description as key
                        clean_desc = supply_desc.replace(' ', '_').replace('-', '_')
                        toner_levels[clean_desc] = percentage
                        
            except (ValueError, IndexError) as e:
                logger.debug(f"Error parsing supply {i} for {ip}: {e}")
                continue
        
        # Get printer status
        errors = []
        printer_status = await perform_snmp_get(ip, PRINTER_STATUS_OID, community)
        if printer_status is not None:
            try:
                status_value = int(printer_status)
                # Printer status values (RFC 3805)
                if status_value != 4:  # 4 = idle
                    status_messages = {
                        1: "Other",
                        2: "Unknown", 
                        3: "Idle",
                        5: "Printing",
                        6: "Warmup",
                        7: "Stopped Printing",
                        8: "Offline"
                    }
                    status_msg = status_messages.get(status_value, f"Status Code: {status_value}")
                    if status_value in [7, 8]:  # Error states
                        errors.append(f"Printer Status: {status_msg}")
            except (ValueError, TypeError):
                pass
        
        # If no supply levels found, try alternative approach
        if not toner_levels:
            logger.info(f"No standard supply data found for {ip}, trying alternative OIDs")
            
            # Try some common vendor-specific OIDs
            alternative_oids = [
                ('1.3.6.1.2.1.43.11.1.1.9.1.1', 'black_toner'),  # Common black toner OID
                ('1.3.6.1.4.1.11.2.3.9.4.2.1.1.12.0', 'hp_toner'),  # HP-specific
                ('1.3.6.1.2.1.43.11.1.1.9.1.2', 'cyan_toner'),   # Cyan
                ('1.3.6.1.2.1.43.11.1.1.9.1.3', 'magenta_toner'), # Magenta
                ('1.3.6.1.2.1.43.11.1.1.9.1.4', 'yellow_toner'),  # Yellow
            ]
            
            for oid, name in alternative_oids:
                result = await perform_snmp_get(ip, oid, community)
                if result is not None:
                    try:
                        level = int(result)
                        if 0 <= level <= 100:
                            color = name.replace('_toner', '').replace('hp_', '')
                            toner_levels[color] = level
                    except (ValueError, TypeError):
                        continue
        
        if not toner_levels and not errors:
            raise ValueError("Could not retrieve any SNMP printer data")

        return toner_levels, errors
        
    except Exception as e:
        logger.error(f"SNMP status retrieval failed for {ip}: {e}")
        raise

async def get_status_via_web(ip: str):
    """
    Asynchronously scrape printer web interface for status using httpx.
    """
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        for protocol in ["https", "http"]:
            for port in ["", ":443", ":80"]:
                if protocol == "https" and port == ":80":
                    continue
                if protocol == "http" and port == ":443":
                    continue
                    
                url = f"{protocol}://{ip}{port}"
                try:
                    logger.debug(f"Trying web interface at {url}")
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    toner_levels = {}
                    errors = []

                    # Try multiple selectors for different printer interfaces
                    selectors_to_try = [
                        # HP EWS selectors
                        {'toner': 'div.tonerGauge span.level', 'error': 'div#alerts li'},
                        {'toner': '.supply-level', 'error': '.alert-message'},
                        {'toner': '[class*="toner"] [class*="level"]', 'error': '[class*="error"]'},
                        # Generic selectors
                        {'toner': '[class*="supply"] [class*="percent"]', 'error': '[class*="alert"]'},
                    ]

                    for selector_set in selectors_to_try:
                        # Try to find toner levels
                        toner_elements = soup.select(selector_set['toner'])
                        if toner_elements:
                            colors = ['black', 'cyan', 'magenta', 'yellow']
                            for i, element in enumerate(toner_elements):
                                try:
                                    text = element.get_text().strip()
                                    # Extract percentage from text
                                    percentage_match = re.search(r'(\d+)%?', text)
                                    if percentage_match:
                                        level = int(percentage_match.group(1))
                                        color = colors[i] if i < len(colors) else f'supply_{i+1}'
                                        toner_levels[color] = level
                                except (ValueError, IndexError):
                                    continue
                        
                        # Try to find errors
                        error_elements = soup.select(selector_set['error'])
                        for element in error_elements:
                            error_text = element.get_text().strip()
                            if error_text and error_text not in errors:
                                errors.append(error_text)
                        
                        if toner_levels or errors:
                            break

                    # If standard selectors don't work, try text parsing
                    if not toner_levels and not errors:
                        page_text = soup.get_text().lower()
                        
                        # Look for percentage patterns in text
                        percentage_patterns = re.findall(r'(\w+)[:\s]*(\d+)%', page_text)
                        for color, percentage in percentage_patterns:
                            if any(keyword in color for keyword in ['black', 'cyan', 'magenta', 'yellow', 'toner']):
                                toner_levels[color] = int(percentage)

                    if toner_levels or errors:
                        logger.info(f"Successfully retrieved web data from {url}")
                        return toner_levels, errors

                except httpx.HTTPStatusError as e:
                    logger.debug(f"HTTP error for {url}: {e.response.status_code}")
                    continue
                except httpx.RequestError as e:
                    logger.debug(f"Request error for {url}: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Parsing error for {url}: {e}")
                    continue

    raise ValueError(f"Web scraping failed for {ip} - no accessible web interface found")

async def get_printer_status(ip: str, connection_mode: str, community: str = "public"):
    """
    Main function to get printer status with a fallback mechanism.
    """
    methods = {
        "snmp": lambda: get_status_via_snmp(ip, community),
        "web": lambda: get_status_via_web(ip)
    }
    
    primary_method = methods.get(connection_mode)
    fallback_mode = "web" if connection_mode == "snmp" else "snmp"
    fallback_method = methods.get(fallback_mode)
    
    if not primary_method:
        raise ValueError(f"Invalid connection mode: {connection_mode}")

    try:
        logger.info(f"Attempting to get status for {ip} via {connection_mode}")
        return await primary_method()
    except Exception as e:
        logger.warning(f"Primary method ({connection_mode}) failed for {ip}: {e}")
        
        if fallback_method:
            try:
                logger.info(f"Attempting fallback method ({fallback_mode}) for {ip}")
                return await fallback_method()
            except Exception as final_e:
                logger.error(f"All methods failed for {ip}. Primary: {e}, Fallback: {final_e}")
                raise ValueError(f"Could not retrieve status for printer at {ip}. Tried {connection_mode} and {fallback_mode}")
        else:
            raise ValueError(f"Could not retrieve status for printer at {ip}")

# Test function to validate the fixes
async def test_printer_discovery(subnet: str, test_ip: str = None):
    """
    Test function to validate the printer discovery and status retrieval.
    """
    try:
        if test_ip:
            # Test specific IP
            print(f"Testing specific IP: {test_ip}")
            
            # Test SNMP printer detection
            printer_info = await is_printer_via_snmp(test_ip)
            if printer_info:
                print(f"✓ Detected printer via SNMP: {printer_info}")
                
                # Test SNMP status retrieval
                try:
                    toner, errors = await get_status_via_snmp(test_ip)
                    print(f"✓ SNMP Status - Toner: {toner}, Errors: {errors}")
                except Exception as e:
                    print(f"✗ SNMP status failed: {e}")
                    
                # Test web status retrieval
                try:
                    toner, errors = await get_status_via_web(test_ip)
                    print(f"✓ Web Status - Toner: {toner}, Errors: {errors}")
                except Exception as e:
                    print(f"✗ Web status failed: {e}")
            else:
                print(f"✗ No printer detected at {test_ip}")
        
        # Test network scanning
        print(f"Scanning network: {subnet}")
        devices = await scan_network(subnet)
        print(f"✓ Found {len(devices)} devices with open ports")
        
        for device in devices[:3]:  # Test first 3 devices
            ip = device['ip']
            printer_info = await is_printer_via_snmp(ip)
            if printer_info:
                print(f"✓ Found printer at {ip}: {printer_info}")
                
    except Exception as e:
        print(f"Test failed: {e}")

# Example usage
if __name__ == "__main__":
    # Test with your network
    asyncio.run(test_printer_discovery("192.168.1.0/24", "192.168.1.100"))