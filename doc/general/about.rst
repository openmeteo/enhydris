.. _about:

==============
About Enhydris
==============

General
=======

Enhydris is a system for the storage and management of hydrological
and meteorological time series.

The database is accessible through a web interface, which includes
several data representation features such as tables, graphs and
mapping capabilities. Data access is configurable to allow or to
restrict user groups and/or privileged users to contribute or to
download data. With these capabilities, Enhydris can be used either as
a public repository of free data or as a private
system for data storage. Time series can be downloaded in plain text
format that can be directly loaded to Hydrognomon_, a free
tool for analysis and processing of meteorological time series.

.. _hydrognomon: http://hydrognomon.org/

Enhydris is free software, available under the GNU Affero General
Public License, and can run on UNIX (such as GNU/Linux) or Windows.
Written in Python/Django, it can be installed on every operating
system on which Python runs, including GNU/Linux and Windows. It is
free software, available under the GNU General Public License version
3 or any later version.  It is being used by openmeteo.org_,
`Hydrological Observatory of Athens`_, Hydroscope_, the `Athens Water
Supply Company`_, and `WQ DREAMS`_.

.. _openmeteo.org: http://openmeteo.org/
.. _hydrological observatory of athens: http://hoa.ntua.gr/
.. _hydroscope: http://main.hydroscope.gr/
.. _athens water Supply Company: http://itia.ntua.gr/eydap/db/
.. _wq dreams: http://wq-dreams.eu/

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

 * It offers access to the data through a webservice API. This is the
   foundation on which the above distributing features are based, but
   it can also be used so that other systems access the data.

 * It has a security system that allows it to be used either in an
   organisational setting or in a public setting. In an organisational
   setting, there are priviliged users who have write access to all
   the data. In a public setting, users can subscribe, create
   stations, and add data for them, but they are not allowed to touch
   stations of other users.

 * It is extensible. It is possible to create new Django applications
   which define geographical entity types besides stations, and reuse
   existing Enhydris functionality.

Presentations, documents, papers
================================

`Enhydris, Filotis & openmeteo.org: Free software for environmental
management`_, by A. Christofides, S. Kozanis, G. Karavokiros, and A.
Koukouvinos; `FLOSS Conference 2011`_, Athens, 21 May 2011.

.. _`Enhydris, Filotis & openmeteo.org: Free software for environmental management`: http://itia.ntua.gr/1145/
.. _floss conference 2011: http://conferences.ellak.gr/2011/

`Enhydris: A free database system for the storage and management of
hydrological and meteorological data`_, by A. Christofides, S.
Kozanis, G.  Karavokiros, Y. Markonis, and A. Efstratiadis; European
Geosciences Union General Assembly 2011, Geophysical Research
Abstracts, Vol. 13, Vienna, 8760, 2011.

.. _`Enhydris: A free database system for the storage and management of hydrological and meteorological data`: http://itia.ntua.gr/1120/
