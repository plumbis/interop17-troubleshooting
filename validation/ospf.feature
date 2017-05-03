Feature: Troubleshoot OSPF

    Scenario: Troubleshoot OSPF Peers
    Given OSPF is configured
    then the OSPF network type should match
    and MTU should match
    and RouterIDs should not match
    and OSPF peers should ping at MTU
    and a priority should be greater than 0
