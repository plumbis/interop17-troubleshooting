Feature: Troubleshoot BGP

    Scenario: Troubleshoot BGP Peers
    Given BGP is configured
    then IP subnets should match
    and ASNs should coordinate
    and peers should ping
    and TCP port 179 should be reachable
