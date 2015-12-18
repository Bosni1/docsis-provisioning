# Modules #

## Persistant storage ##
The project uses an RDBMS to store all its data. PostgreSQL 8.3 was chosen, and some of its unique features were used, so at this moment it is the only RDBMS that may be used.

Look at the [database structure here](DatabaseStructure.md).

## DataProxy ##
DataProxy is a server used by other modules to access the database backend. It's purpose is to provide a higher level abstraction (no SQL), and avoid opening too many connections to the backend when the system is under heavy load.

The DataProxy includes a TasksGenerator, which listens for changes to data and creates  tasks to be henadled by submodules.

## ProvisioningDaemon ##
The [provisioning daemon](ProvisioningDaemon.md) controls all tasks that take part in the provisioning process:
  * [TFTP](TftpServer.md),
  * [Logging backend](LoggerProcess.md),
  * [OMAPI-based ISC DHCP interface](DhcpOMAPI.md)

The ProvisioningDaemon is supposed to be run on a dedicated machine, preferably one where the database engine is hosted.

## GatewayDaemon ##
The GatewayDaemon is a task that runs on a gateway machine, its job is to update firewall rules when data changes, and the TasksGenerator signals it.

## [DOCSIS config file compiler](DocsisCompiler.md) ##
A module which generates DOCSIS configuration files for cable modems and MTAs.

## TrafficLogger ##
A task that should be run on a seperate machine which logs all end-user connections.

## TrafficStatisticsGenerator ##
A task supplementary to the TrafficLogger which generates network-wide statistics, detects abnormal behaviour, graphs network vital signs etc.

## [GUI](GuiFrontend.md) ##
A multi-platform GUI used to manage and monitor the network.

## Other software used ##
  * [ISC DHCP](http://www.isc.org/index.pl?/sw/dhcp/)
  * [ipset](http://ipset.netfiler.org)
  * [syslog](http://www.syslog.org/)