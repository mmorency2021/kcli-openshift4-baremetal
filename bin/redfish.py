#!/usr/bin/env python3

import re
import requests
import sys
import yaml
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


action = sys.argv[1] if len(sys.argv) > 1 else 'status'
custom_host = sys.argv[2] if len(sys.argv) > 2 else None
installfile = "/root/install-config.yaml"
with open(installfile) as f:
    data = yaml.safe_load(f)
    uri = data['platform']['baremetal']['libvirtURI']
    hosts = data['platform']['baremetal']['hosts']
    for host in hosts:
        name = host['name']
        if custom_host is not None and name != custom_host:
            continue
        address = host['bmc']['address']
        user, password = host['bmc'].get('username'), host['bmc'].get('password')
        if user is None or password is None:
            print("Missing creds for %s. Skipping" % name)
            continue
        if 'ipmi' in address:
            continue
        else:
            match = re.match(".*(http.*|idrac-virtualmedia.*|ilo5-virtualmedia.*|redfish-virtualmedia.*)", address)
            address = match.group(1)
            for _type in ['idrac', 'redfish', 'ilo5']:
                address = address.replace(f'{_type}-virtualmedia', 'https')
            print(address)
            info = requests.get(address, verify=False, auth=(user, password)).json()
            print("running %s for %s" % (action, name))
            if action == 'status':
                status = info['PowerState']
                print("%s: %s" % (name, status))
            elif action in ['off', 'on']:
                actions = {'off': 'ForceOff', 'on': 'On'}
                currentaction = actions[action]
                actionaddress = "%s/Actions/ComputerSystem.Reset" % address
                headers = {'Content-type': 'application/json'}
                requests.post(actionaddress, json={"ResetType": currentaction}, headers=headers, auth=(user, password),
                              verify=False)
