#/usr/bin/env python3

from behave import *
import yaml
import json
import subprocess
import time
import shutil
import os
import ipaddress


'''
Scenario: Troubleshoot OSPF INIT Peers
    Given OSPF is configured
    then the OSPF network type should match
    and OSPF authentication should match
    and OSPF peers should ping
'''
topology_string = """
            leaf01:swp51 -- spine01:swp1
           """
           # leaf01:swp52 -- spine02:swp2

topology = {}
ospf_interfaces = {}


def parse_topology(context):
    '''
    Consumes a string of a .dot format topology file.
    host01:eth0 -- host02:eth0

    Returns nothing, due to behave limitations, but
    populates the global topology dict variable.
    '''

    lines = topology_string.split("\n")

    for line in lines:
        if len(line.strip()) > 1:
            left_side = line[:line.find("--")].strip()
            right_side = line[line.find("--") + 2:].strip()

            left_host_port = left_side[left_side.find(":") + 1:].strip()
            left_hostname = left_side[:left_side.find(":")].strip()

            right_host_port = right_side[right_side.find(":") + 1:].strip()
            right_hostname = right_side[:right_side.find(":")].strip()

            # hosts["leaf01"] = {"swp51": {"spine01": "swp1"}}
            if left_hostname not in topology:
                topology[left_hostname] = {left_host_port: {right_hostname: right_host_port}}
            else:
                # We are adding an additional port to the host
                topology[left_hostname][left_host_port] = {right_hostname: right_host_port}

            if right_hostname not in topology:
                topology[right_hostname] = {right_host_port: {left_hostname: left_host_port}}
            else:
                topology[right_hostname][right_host_port] = {right_host_port: {left_hostname: left_host_port}}


def get_ospf_interfaces(context):
    '''
    Connects to every host in the topology
    and pulls JSON data about all OSPF interfaces

    Populates the ospf_interfaces dict
    '''
    for host in topology.keys():
        ansible_command_string = ["ansible", host, "-o", "-a",
                                  "vtysh -c 'show ip ospf interface json'", "--become"]
        process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        if stderr:
            assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr

        if stdout.find("{") <= 0:
            assert False, "OSPF is not configured on " + host

        ospf_data[host] = json.loads(stdout[stdout.find("{"):])


def check_ospf_interfaces_match(context):
    for host in topology:
        for interface in topology[host]:
            remote_host = topology[host][interface].keys()[0]
            remote_iface = topology[host][interface][remote_host]
            my_ip = ipaddress.ip_address(ospf_interfaces[host][interface]["ipAddress"] + "/" + ospf_interfaces[host][interface]["ipAddressPrefixlen"])
            remote_ip = ipAddress.ipAddress(ospf_interfaces[remote_host][remote_iface]["ipAddress"] + "/" + ospf_interfaces[remote_host][remote_iface]["ipAddressPrefixlen"])

            assert False, my_ip + remote_ip



@given('OSPF is configured')
def step_impl(context):
    # Turn the .dot topology into a dictionary
    parse_topology(context)

    # Get ospf interface data for all hosts.
    # This also will check if OSPF is even enabled.
    get_ospf_interfaces(context)

    # Check that OSPF is enabled on all relevant interfaces
    check_ospf_interfaces_match(context)

    assert True


@then('the OSPF network type should match')
def step_impl(context):
    assert True
