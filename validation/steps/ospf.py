from behave import *
import json
import subprocess
import ipaddress


'''
Scenario: Troubleshoot OSPF INIT Peers
    Given OSPF is configured
    then the OSPF network type should match
    and MTU should match
    and OSPF peers should ping 224.0.0.5
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
        # This is the ansible ad hoc command to run at the command line
        ansible_command_string = ["ansible", host, "-a",
                                  "vtysh -c 'show ip ospf interface json'", "--become"]

        # Run the command
        process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Get the output from the OS
        stdout, stderr = process.communicate()
        if stderr:
            assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr

        # We expect JSON output starting with {, if that isn't there, something's wrong.
        if stdout.find("{") <= 0:
            assert False, "OSPF is not configured on " + host

        ospf_interfaces[host] = json.loads(stdout[stdout.find("{"):])


def check_ospf_interfaces_match(context):
    '''
    Loop over the topology and verify that adjacent
    OSPF interfaces are configured in the same subnet
    '''
    for host in topology:
        for interface in topology[host]:
            remote_host = topology[host][interface].keys()[0]
            remote_iface = topology[host][interface][remote_host]

            # my IP address. Use ip_interface to support IP + Mask
            # also the ipaddress class only takes unicode inputs, not raw strings
            my_ip = ipaddress.ip_interface(unicode(ospf_interfaces[host][interface]["ipAddress"] + "/" + str(ospf_interfaces[host][interface]["ipAddressPrefixlen"])))
            remote_ip = ipaddress.ip_interface(unicode(ospf_interfaces[remote_host][remote_iface]["ipAddress"] + "/" + str(ospf_interfaces[remote_host][remote_iface]["ipAddressPrefixlen"])))

            if not my_ip.network == remote_ip.network:
                assert False, host + " interface " + interface + " with IP " + \
                    str(my_ip) + " not on the same subnet as " + remote_host + \
                    " " + remote_iface + " (" + str(remote_ip) + ")"


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
    '''
    Verify that the configured OSPF network type (Broadcast, point to point)
    is the same on both sides of the link.
    '''

    # Loop over every host in the topology
    for host in topology:
        # Loop over every interface that host has
        for interface in topology[host]:

            # This will give us the remote hostname on that link
            remote_host = topology[host][interface].keys()[0]

            # and the remote interface name
            remote_iface = topology[host][interface][remote_host]

            # Set my OSPF network type
            my_network = ospf_interfaces[host][interface]["networkType"]

            # And the remote OSPF network
            remote_network = ospf_interfaces[remote_host][remote_iface]["networkType"]

            if not my_network == remote_network:
                assert False, "OSPF network types do not match. \n" + host + " " + interface + \
                    " configured as " + my_network + ". " + remote_host + " " + remote_iface + \
                    " configured as " + remote_network + "."

    assert True


@then('MTU should match')
def step_impl(context):
    '''
    verify that both OSPF end points have the same MTU
    '''

    for host in topology:
            for interface in topology[host]:
                remote_host = topology[host][interface].keys()[0]
                remote_iface = topology[host][interface][remote_host]
                my_mtu = ospf_interfaces[host][interface]["mtuBytes"]
                remote_mtu = ospf_interfaces[remote_host][remote_iface]["mtuBytes"]

                if not my_mtu == remote_mtu:
                    assert False, "Interface MTUs do not match. \n" + host + " " + interface + \
                        " configured as " + str(my_mtu) + ". " + remote_host + " " + remote_iface + \
                        " configured as " + str(remote_mtu) + "."

    assert True


@then('RouterIDs should not match')
def step_impl(context):
    '''
    verify that the router IDs of the OSPF nodes DO NOT match
    '''
    for host in topology:
            for interface in topology[host]:
                remote_host = topology[host][interface].keys()[0]
                remote_iface = topology[host][interface][remote_host]
                my_rid = ospf_interfaces[host][interface]["routerId"]
                remote_rid = ospf_interfaces[remote_host][remote_iface]["routerId"]

                if my_rid == remote_rid:
                    assert False, "RouterIDs on " + host + " and " + remote_host + " are duplicates."

    assert True


@then('OSPF peers should ping at MTU')
def step_impl(context):
    for host in topology:
            for interface in topology[host]:
                remote_host = topology[host][interface].keys()[0]
                remote_iface = topology[host][interface][remote_host]
                my_ip = ospf_interfaces[host][interface]["ipAddress"]
                remote_ip = ospf_interfaces[remote_host][remote_iface]["ipAddress"]

                # We don't need to compare MTUs since we already verified they match
                my_mtu = ospf_interfaces[host][interface]["mtuBytes"]

                ansible_command_string = ["ansible", host, "-a",
                                          str("ping" + remote_ip + "-c 1 -s " + str(my_mtu)),
                                          "--become"]

                process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)

                stdout, stderr = process.communicate()
                if stderr:
                    assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr

                if not process.returncode == 0:
                    assert False, "Ping from " + host + " " + my_ip + \
                        " to " + remote_host + " " + remote_ip + " failed."
    assert True
