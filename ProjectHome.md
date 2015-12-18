### docsis-provisioning ###
The **provisioning** project provides:
  * A complete Linux solution for booting up DOCSIS cable modems, including:
    1. a built-in TFTP server capable of generating configuration files on-the-fly,
    1. an OMAPI interface to ISC DHCP server version 3,
    1. an optional syslog server,
    1. a time server,
    1. a powerful GUI environment to manage and monitor the network,
    1. a module supporting PacketCable MTAs
  * An interface to ipset, providing scalable firewall capabilities that may be used on a gateway machine,
  * A web-proxy redirection to force end-users to read and acknowledge messages

Look at the [project modules](ProjectStructure.md), and the [project status report](ProjectStatus.md).