#!/usr/bin/env python2.7
import json
import subprocess

'''
The output from "bridge -j vlan show" is difficult to parse as an Ansible one-liner.

This script will pull the list of vlans out of the bridge output and return a dict
in the form of:

{<interface_name>: [vlan_list]}

Take the following example:
cumulus@leaf01:~$ bridge -j vlan show
{
    "peerlink": [{
            "vlan": 1,
            "flags": ["PVID","Egress Untagged"
            ]
        },{
            "vlan": 13
        },{
            "vlan": 24
        }
    ],
    "bond01": [{
            "vlan": 13,
            "flags": ["PVID","Egress Untagged"
            ]
        }
    ]
}

This will return {"peerlink": [1, 13, 24], "bond01": [13]}
'''

stdout, stderr = subprocess.Popen(["bridge", "-j", "vlan", "show"], stdout=subprocess.PIPE).communicate()

if stderr:
    print "Unexpected output from CLI command"
    exit(1)

bridge_output = json.loads(stdout)

vlan_dict = dict()


for iface in bridge_output:
    vlan_list = []
    for vlan in bridge_output[iface]:
        vlan_list.append(vlan["vlan"])
    vlan_dict[str(iface)] = vlan_list

print json.dumps(vlan_dict)

exit(0)
