# cldemo-vxlan

This demonstrates using LNV in the reference topology with Active-Active VxLAN.

Each server has a bond to each local switch pair.

There are two VxLAN Domains (VNIs):
 Server01, Server03, Internet in VLAN 13, VNI13
 Server02, Server04, Internet in VLAN 24, VNI24

BGP Unnumbered is used in the fabric.

Spine01 and Spine02 are anycast LNV Service Nodes.

To configure the lab use
`ansible-playbook main.yml`

This lab also contains post-deploy validation playbooks.
To validate the lab after deploy, run
`ansible-playbook tests/test.yml`
