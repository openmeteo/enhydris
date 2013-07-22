.. _overview:

Overview
========

Enhydris is a system for the storage and management of hydrological
and meteorological time series. It is a database and a web
application. Written in Python/Django, it can be installed on every
operating system on which Python runs, including GNU/Linux and
Windows. It currently supports only PostgreSQL, but it is not
difficult to port it to another RDBMS.  It is free software, available
under the GNU General Public License version 3 or any later version.

Enhydris has several advanced features:

 * It stores time series in a clever compressed text format in the
   database, resulting in using small space and high speed retrieval.
   However, the first and last few records of each time series are
   stored uncompressed, which means that the start and end date can be
   retrieved immediately, and appending a few records at the end can
   also be done instantly.

 * It can work in a distributed way. Many organisations can install
   one instance each, but an additional instance, common to all
   organisations, can be setup as a common portal. This additional
   instance can be configured to replicate data from the databases of
   the organisations, but without the space-consuming time series,
   which it retrieves from the other databases on demand. A user can
   transparently use this portal to access the data of all
   participating organisations collectively.

 * It offers access to the data in a machine-readable format (JSON)
   through HTTP. This is the foundation on which the above
   distributing features are based, but it can also be used so that
   other systems access the data.

 * It has a security system that allows it to be used either in an
   organisational setting or in a public setting. In an organisational
   setting, there are priviliged users who have write access to all
   the data. In a public setting, users can subscribe, create
   stations, and add data for them, but they are not allowed to touch
   stations of other users.

 * It has an API that allows integration with a GIS system. It has
   successfully been tested with Google Maps and ArcGIS server.

 * It is extensible. It is possible to create new Django applications
   which define geographical entity types besides stations, and reuse
   existing Enhydris functionality.
