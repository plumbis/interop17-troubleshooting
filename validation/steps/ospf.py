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
topology = """
            leaf01:swp51 -- spine01:swp1
            leaf01:swp52 -- spine02:swp2
           """


def parse_topology(context):
    for line in topology:
        assert False, line


def check_ospf_enabled(host, context):
    ansible_command_string = ["ansible", host, "-o", "-a", "vtysh -c 'show ip ospf json'", "--become"]
    process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    if stderr:
        assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr

    if stdout.find("{") <= 0:
        assert False, "OSPF is not configured"
    else:
        return True


def get_ospf_interface(host, context):
    ansible_command_string = ["ansible", host, "-o", "-a", "vtysh -c 'show ip ospf interface json'", "--become"]
    process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    if stderr:
        assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr

    if stdout.find("{") <= 0:
        assert False, "OSPF is not configured"
    else:
        return stdout[stdout.find("{"):]


@given('OSPF is configured')
def step_impl(context):
    parse_topology(context)


@then('the OSPF network type should match')
def step_impl(context):
    assert True
