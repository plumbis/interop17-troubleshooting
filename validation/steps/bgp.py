from behave import *
import yaml
import json
import subprocess
import time
import shutil
import os


'''
Feature: Troubleshoot BGP

    Scenario: Troubleshoot BGP Peers
    Given BGP is configured
    then IP subnets should match
    and ASNs should coordinate
    and peers should ping
    and TCP port 179 should be reachable
'''


def check_bgp_enabled(host, context):
    ansible_command_string = ["ansible", host, "-o", "-a", "vtysh -c 'show ip bgp sum'", "--become"]
    process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    if stderr:
        assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr
    else:
        # I'm lazy, let's just start at the opening { of json output
        json_output = stdout[stdout.find("{"):]
        assert False, json_output


@given('BGP is configured')
def step_impl(context):
    hosts = ["leaf01", "spine01"]

    for host in hosts:
        if not check_bgp_enabled(host, context):
            assert False, "BGP not configured on " + host
