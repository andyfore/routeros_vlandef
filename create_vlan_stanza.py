#!/usr/bin/env python3

import ipaddress
from ipaddress import IPv4Interface
from ipaddress import IPv4Network

def confirm_prompt(question: str) -> bool:
    reply = None
    while reply not in ("", "y", "n"):
        reply = input(f"{question} (Y/n): ").lower()
    return (reply in ("", "y"))

def validate_ip_address(ip_string):
   try:
       ip_addr = ipaddress.ip_network(ip_string,False)
       return True
   except ValueError:
       return False
   
def validate_dhcp_range(target,network):
    try:
        if '-' in target:
            start_ip, end_ip = target.split('-')
            try:
                end_ip = ipaddress.ip_address(end_ip)
                try:
                    start_ip = ipaddress.ip_address(start_ip)
                    try:
                        network.supernet_of(ipaddress.IPv4Network(start_ip))
                        try:
                            network.supernet_of(ipaddress.IPv4Network(end_ip))
                            return True
                        except ValueError:
                            return False
                    except ValueError:
                        return False
                    except ValueError:
                        return False
                except ValueError:
                    return False
            except ValueError:
                return False
        else:
            return False
    except ValueError:
        return False

dictInput = {}
listOutput = []

BASE_VLAN_CIDR = "192.168.0.1"

print()
BASE_VLAN_CIDR = str(input('Base VLAN Address: [{}] '.format(BASE_VLAN_CIDR)) or BASE_VLAN_CIDR)
NEW_VLAN = input('VLAN Name: [] ')
NEW_VLAN_ID = input('VLAN ID: [] ')
NEW_VLAN_GW_IP_CIDR = input('VLAN GW Address (CIDR Format): [] ')

if not validate_ip_address(NEW_VLAN_GW_IP_CIDR):
    print("Entered VLAN GW Address is invalid. Exit Code 1")
    exit()

if "/" not in NEW_VLAN_GW_IP_CIDR:
    print("VLAN GW Address not in CIDR format. Exist Code 2")
    exit()

iface = IPv4Interface(NEW_VLAN_GW_IP_CIDR)

NEW_VLAN_GW_IP = iface.ip
NEW_VLAN_CIDR = iface.network
NEW_VLAN = NEW_VLAN.upper()

dictInput.update({"vlanName": NEW_VLAN})
dictInput.update({"vlanID": NEW_VLAN_ID})
dictInput.update({"gwIPFull": NEW_VLAN_GW_IP_CIDR})
dictInput.update({"gwIP": format(ipaddress.IPv4Address(NEW_VLAN_GW_IP))})
dictInput.update({"vlanCIDR": format(ipaddress.IPv4Network(NEW_VLAN_CIDR))})

listOutput.append(f"# {dictInput['vlanName']} VLAN interface creation and IP assignment")
listOutput.append(f"/interface vlan add interface=BR1 name= {dictInput['vlanName']}_VLAN vlan-id={dictInput['vlanID']}")
listOutput.append(f"/ip address add interface={dictInput['vlanName']}_VLAN address={dictInput['gwIPFull']}")

reply = confirm_prompt("Does VLAN need DHCP?")

if reply:
    print()
    defRangeStart = format(ipaddress.IPv4Address(NEW_VLAN_GW_IP))[:format(ipaddress.IPv4Address(NEW_VLAN_GW_IP)).rfind(".")] + ".10"
    defRangeEnd = format(ipaddress.IPv4Address(NEW_VLAN_GW_IP))[:format(ipaddress.IPv4Address(NEW_VLAN_GW_IP)).rfind(".")] + ".100"
    listOutput[0]= f"# {dictInput['vlanName']} VLAN interface creation, IP assignment, and DHCP service"
    dictInput.update({"vlanDHCPServerName": NEW_VLAN + "_VLAN"})
    dictInput.update({"vlanDHCPPool": NEW_VLAN + "_VLAN"})
    NEW_VLAN_DHCP_RANGE = str(input('VLAN DHCP Range: [{}-{}] '.format(defRangeStart, defRangeEnd)) or defRangeStart + "-" + defRangeEnd)
    try:
        validate_dhcp_range(NEW_VLAN_DHCP_RANGE.replace(" ", ""),ipaddress.IPv4Network(dictInput["vlanCIDR"]))
        dictInput.update({"vlanDHCPRange": NEW_VLAN_DHCP_RANGE})
    except ValueError:
        print("DHCP range error please check input and try again.")
        exit()
    listOutput.append(f"/ip pool add name={dictInput['vlanDHCPPool']} ranges={dictInput['vlanDHCPRange']}")
    listOutput.append(f"/ip dhcp-server add address-pool={dictInput['vlanDHCPPool']} interface={dictInput['vlanName']}_VLAN name={dictInput['vlanDHCPServerName']} disabled=no")
    listOutput.append(f"/ip dhcp-server network add address={dictInput['vlanCIDR']} dns-server={BASE_VLAN_CIDR} gateway={dictInput['gwIP']}")

for item in listOutput:
    print(item)