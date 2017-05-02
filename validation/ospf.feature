Feature: Troubleshoot OSPF

    Scenario: Troubleshoot OSPF INIT Peers
    Given OSPF is configured
    then the OSPF network type should match
    and OSPF authentication should match
    and OSPF peers should ping
