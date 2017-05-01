from behave import *
import yaml
import json
import subprocess
import time
import shutil
import os

'''
    Scenario: Validate Web Server Access
    Given a webserver is configured
    Then the website should be accessible
'''

server_vars_location = "roles/servers/vars/main.yml"

server_v4_dict = dict()
server_v6_dict = dict()
server_loopback_config = dict()
list_of_servers = []


def run_ansible_command(context, ansible_group_list, command):
    '''
    Takes in a list of ansible nodes and a command
    and executes an ansible ad hoc command.

    In Ansible 2.0 the Ansible API no longer uses ansible.runner()
    Ansible has also stated that the Ansible API may change at any time.
    To prevent bad things from happening this is implemented with
    ad hoc commands on the local machine.

    Also, Ansible can only return structured data for ad hoc commands with the
    --tree argument which only writes to a file.

    Consumes list and string.
    Returns dict of json output
    '''

    timestamp = time.time()

    directory_name = ".behave_ansible_" + str(timestamp)
    node_string = ":".join(ansible_group_list)
    ansible_command_string = ["ansible", node_string, "-a", command, "--become", "--tree", directory_name]
    process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    if stderr:
        assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr
    else:

        node_output = dict()

        for file in os.listdir(directory_name):

            with open(directory_name + "/" + file) as data_file:
                data = json.load(data_file)

            node_output[file] = data

        shutil.rmtree(directory_name)
        return node_output

    shutil.rmtree(directory_name)
    assert False, "Error in run_ansible_command. Not sure how we got here."


def run_ansible_module(context, ansible_group_list, module, args):
    '''
    Takes in a list of ansible nodes and leverages the ansible service
    module against them at the command line.

    In Ansible 2.0 the Ansible API no longer uses ansible.runner()
    Ansible has also stated that the Ansible API may change at any time.
    To prevent bad things from happening this is implemented with
    ad hoc commands on the local machine.

    Also, Ansible can only return structured data for ad hoc commands with the
    --tree argument which only writes to a file.

    Consumes list and string.
    Returns dict of json output
    '''

    timestamp = time.time()

    directory_name = ".behave_ansible_" + str(timestamp)
    node_string = ":".join(ansible_group_list)
    ansible_command_string = ["ansible", node_string, "-m", module, "-a", args, "--become", "--tree", directory_name]
    process = subprocess.Popen(ansible_command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()

    if stderr:
        assert False, "\nCommand: " + " ".join(ansible_command_string) + "\n" + "Ansible Error: " + stderr
    else:

        node_output = dict()

        for file in os.listdir(directory_name):

            with open(directory_name + "/" + file) as data_file:
                data = json.load(data_file)

            node_output[file] = data

        shutil.rmtree(directory_name)
        return node_output

    shutil.rmtree(directory_name)
    assert False, "Error in run_ansible_command. Not sure how we got here."


def get_server_vars(context):
    '''
    Open the Ansible vars file for leafs and load it into
    server_v4_dict and server_v6_dict
    '''

    with open(server_vars_location) as stream:
        try:
            context.server_vars = yaml.load(stream)
        except yaml.YAMLError as exc:
            assert False, "Failed to load server variables file: " + exc

    if "interfaces" in context.server_vars.keys():
        for node in context.server_vars["interfaces"]:
            found_loopback = False
            interfaces = context.server_vars["interfaces"][node]

            if "lo" in interfaces.keys():
                if "ipv4" in interfaces["lo"].keys():
                    server_v4_dict[node] = interfaces["lo"]["ipv4"]
                    found_loopback = True

                if "ipv6" in interfaces["lo"].keys():
                    server_v6_dict[node] = interfaces["lo"]["ipv6"]
                    found_loopback = True

            if found_loopback:
                list_of_servers.append(node)


def get_configured_loopbacks(context):
    '''
    Make Ansible API call to pull data directly from the node.
    Return data in json format
    '''
    global server_loopback_config

    # runner = ansible.runner.Runner(module_name='command',
    #                                module_args="netshow interface lo -j",
    #                                become=True, pattern=list_of_servers)

    ansible_output = run_ansible_command(context, list_of_servers, "netshow interface lo - j")

    if ansible_output is None:
        assert False, "Ansible is unable to contact a leaf"

    server_loopback_config = ansible_output


def check_apache_service(context):
    '''
    Make Ansible API call to validate apache2 is running
    '''

    # runner = ansible.runner.Runner(module_name='service',
    #                                module_args="name=apache2 state=started enabled=yes",
    #                                check=True, become=True, pattern=list_of_servers)

    ansible_output = run_ansible_module(context, list_of_servers, "service", "name=apache2 state=started enabled=yes")

    if ansible_output is None:
        assert False, "Ansible is unable to contact a leaf"

    for node in ansible_output.keys():
        # "msg" is the stdout from Ansible.
        # This will only exist if "service apache2 start" fails
        if "msg" in ansible_output[node]:
            # Ansible tried to start apache2 but wasn't sudo
            if "Permission denied" in ansible_output[node]["msg"]:
                assert False, "Apache configured but not running on " + node

            if (
               "no service" or
               "Error when trying to enable apache2: rc=1 Failed to execute operation"
               in ansible_output[node]["msg"]):
                assert False, "Apache not configured on " + node

            else:
                assert False, "Unknown error, Ansible dump: " + str(ansible_output[node])

        elif ansible_output[node]["state"] == "started":
            assert True

        else:
            assert False, "Unknown Apache status check error output dump: " + str(node)


def check_webserver(context):

    for node in context.loopback_dict.keys():
            list_of_loopbacks = context.loopback_dict.values()

            for ip in list_of_loopbacks:
                # runner = ansible.runner.Runner(module_name='uri',
                #                                module_args="url=http://" + ip[:ip.find("/")],
                #                                pattern=node)

                ansible_output = run_ansible_module(context, [node], "uri", "url=http://" + ip[:ip.find("/")])

                if ansible_output is None:
                    assert False, "Ansible is unable to contact a leaf"

                if ansible_output[node]["status"] != 200:
                    assert False, "Error on " + node + " trying to access http://" + ip[:ip.find("/")] + " : " + ansible_output[node]["msg"]

                if "status" not in ansible_output[node]:
                    assert False, "Unknown Ansible error trying to contact http://" + \
                                  ip[:ip.find("/")] + " from " + node + ". Ansible output: " + \
                                  ansible_output[node]

                if not ansible_output[node]["status"] == 200:
                    assert False, "Server on " + node + " did not return 200 OK code. Returned " + str(ansible_output["contacted"][node]["status"])


@given('a webserver is configured')
def step_impl(context):

    # Setup: Load Vars File
    get_server_vars(context)

    # Setup: Pull Loopback Interface Config from Device
    get_configured_loopbacks(context)

    assert True


@when('apache is running')
def step_impl(context):

    check_apache_service(context)

    assert True


@then('the website should be accessible')
def step_impl(context):
    '''
    Validate that the servers can reach each other's webservers
    '''

    if len(server_v4_dict) > 0:
        context.loopback_dict = server_v4_dict

        check_webserver(context)

    # TODO: Ansible URI module doesn't seem to like IPv6
    # if len(server_v6_dict) > 0:
    #     context.loopback_dict = server_v6_dict

        check_webserver(context)

    assert True
