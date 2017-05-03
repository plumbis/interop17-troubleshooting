Feature: Troubleshoot OSPF

    Scenario: Troubleshoot OSPF INIT Peers
    Given OSPF is configured
    then the OSPF network type should match
    and MTU should match
    and RouterIDs should not match
    and OSPF peers should ping at MTU
