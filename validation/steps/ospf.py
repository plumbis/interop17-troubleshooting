from behave import *
import yaml
import json
import subprocess
import time
import shutil
import os


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


def parse_topology(context):
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


def check_ospf_enabled(host, context):
    ansible_command_string = ["ansible", host, "-o", "-a", "vtysh -c 'show ip ospf json'", "--become"]
    process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    if stderr:
        assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr

    if stdout.find("{") <= 0:
        assert False, "OSPF is not configured on " + host
    else:
        return True


def check_ospf_enabled(my_host, my_port, remote_host, remote_port):
    #get_ospf_interface(my_host)
    #get_ospf_interface(remote_host)
    pass


def get_ospf_interface(host, port, context):

    my_vtysh_command = "vtysh -c 'show ip ospf interface " + port + " json'"
    ansible_command_string = ["ansible", host, "-o", "-a", vtysh_command, "--become"]
    process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    if stderr:
        assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr

    if stdout.find("{") <= 0:
        assert False, "OSPF is not configured on " + host

@given('OSPF is configured')
def step_impl(context):
    parse_topology(context)
    assert False, topology
    for host in topology.keys():
        check_ospf_enabled(host, context)

    assert True


@then('the OSPF network type should match')
def step_impl(context):
    ospf_interface = {}
    for host in topology.keys():
        for interface in topology[host]:
            # interface is my interface (swp01)
            # topology[host][interface] is the remote interface (swp51)
            my_host = host
            my_port = interface
            remote_host = topology[host][interface].keys()  # Assumes one peer on the link
            remote_port = topology[host][interface]
            check_ospf_enabled(my_host, my_port, remote_host, remote_port, context)
