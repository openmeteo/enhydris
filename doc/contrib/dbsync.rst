.. _dbsync:

:mod:`dbsync` --- Enhydris Database Syncing
===========================================

.. module:: dbsync
   :synopsis: Enhydris Databasy Synchronization Details
.. moduleauthor:: Seraphim Mellos <mellos@indifex.com>
.. sectionauthor:: Seraphim Mellos <mellos@indifex.com>

The dbsync module implements the database replication and synchronization
features. The core part of this module is the syncdb management command which
takes care of fetching and installing remote objects from JSON files using the
:ref:`Webservice API <webservice-api>`.

.. admonition:: Note

   The dbsync application is currently entirely broken, because of
   changes made to the api. See the "Backwards compatibility"
   admonition of :ref:`Webservice API <webservice-api>` for more
   information.

DBSync Objects
--------------

Each instance of the :class:`Database` class represents a remote enhydris
instance. Once such an object has been added to the local database, then the
remote instance it refers to can be used in the replication routine. 

.. class:: Database(name, ip_address, hostname, descr) 

	.. attribute:: name

		This is the name of the database. It's not mandatory that it's the
		same to the actual name of the database. This is only used for local
		reference.

	.. attribute:: ip_address

		This field should contain the ip of the host that holds the remote
		enhydris instance.

	.. attribute:: hostname

		This field must contain the FQDN from which the enhydris instance is
		accessible (this is especially required when using vhosts on a server
		so that the replication script knows which vhost uses which database).

		.. note::

			A fully qualified domain name (FQDN), sometimes referred to as an
			absolute domain name, is a domain name that specifies its exact
			location in the tree hierarchy of the Domain Name System (DNS). It
			specifies all domain levels, including the top-level domain,
			relative to the root domain. A fully qualified domain name is
			distinguished by this absoluteness in the name space.

	.. attribute:: descr
	
			This is a textfield that holds the description for the specific
			database.


DBSync Management Command
-------------------------

The core functionality of the DBSync module is to provide a management command
with which one can replicate completely a remote instance (or multiple remote
instances) of the enhydris web application. The replication script can also
update existing entries with changes when run multiple consecutive times but
doesn't handle item deletion.

The code for the replication scripts resides under the
``enhydris/dbsync/management/commands/`` directory, inside the
``hcore_remotesyncdb.py`` file. You can check out the available options for
the script by issuing the following command:: 

	# ./manage.py hcore_remotesyncdb -h

	Usage: ./manage.py hcore_remotesyncdb [options] 

	This command is used to synchronize the local database using data from a
	remote instance

	Options:
	  -v VERBOSITY, --verbosity=VERBOSITY
	                        Verbosity level; 0=minimal output, 1=normal output,
	                        2=all output
	  --settings=SETTINGS   The Python path to a settings module, e.g.
	                        "myproject.settings.main". If this isn't provided, the
	                        DJANGO_SETTINGS_MODULE environment variable will be
	                        used.
	  --pythonpath=PYTHONPATH
	                        A directory to add to the Python path, e.g.
	                        "/home/djangoprojects/myproject".
	  --traceback           Print traceback on exception
	  -r REMOTE, --remote=REMOTE
	                        Remote instance to sync from
	  -p PORT, --port=PORT  Specify custom port. Default is 80.
	  -a APP, --app=APP     Application which should be synced
	  -e EXCLUDE, --exclude=EXCLUDE
	                        State which models of the apps you want excluded from
	                        the sync
	  -f, --fetch-only      Doesn't actually submit any changes, just fetches
	                        remote dumps and saves them locally.
	  -w CWD, --work-dir=CWD
	                        Define the tmp dir in which all temporary files will
	                        be stored
	  -N, --no-backups      Default behaviour is to take a backup of the local db
	                        before doing any changes. This overrides this
	                        behavior.
	  -s, --skip            If skip is specified, then syncing will skip any
	                        problems continue execution. Default behavior is to
	                        halt on all errors.
	  -R, --resume          With resume, no files are fetched but the local ones
	                        are used.
	  -S, --silent          Suppress all log messages
	  --version             show program's version number and exit
	  -h, --help            show this help message and exit

The most important command line options are the ``-a`` and ``-r`` which are
used to specify which application you want to replicate (in our case
``hcore``) and which is the remote instance from which the data should be
pulled. A sample execution of the replication script from the command line
should look something like this::

	   # ./manage.py hcore_remotesyncdb -a hcore -r itia.hydroscope.gr -e UserProfile  
	   /usr/local/lib/python2.6/dist-packages/django_registration-0.7-py2.6.egg/registration/models.py:4:
	   DeprecationWarning: the sha module is deprecated; use the hashlib module instead
	   Checking port availability on host 147.102.160.28, port 80
	   Remote host is up. Continuing with the sync.
	   The following models will be synced: ['EventType', 'FileType', 'Garea',
	   'Gentity', 'GentityAltCode', 'GentityAltCodeType', 'GentityEvent',
	   'GentityFile', 'Gline', 'Gpoint', 'Instrument', 'InstrumentType', 'Lentity',
	   'Organization', 'Overseer', 'Person', 'PoliticalDivision', 'Station',
	   'StationType', 'TimeStep', 'TimeZone', 'Timeseries', 'UnitOfMeasurement',
	   'Variable', 'WaterBasin', 'WaterDivision']
	   The following models will be excluded ['UserProfile']
	   Syncing model EventType
		- Downloading EventType fixtures : done
	   Syncing model FileType
		- Downloading FileType fixtures : done
	   Syncing model Garea
		- Downloading Garea fixtures : done
	   Syncing model Gentity
		- Downloading Gentity fixtures : done
	   Syncing model GentityAltCode
		- Downloading GentityAltCode fixtures : done
	   Syncing model GentityAltCodeType
		- Downloading GentityAltCodeType fixtures : done
	   Syncing model GentityEvent
		- Downloading GentityEvent fixtures : done
	   Syncing model GentityFile
		- Downloading GentityFile fixtures : done
	   Syncing model Gline
		- Downloading Gline fixtures : done
	   Syncing model Gpoint
		- Downloading Gpoint fixtures : done
	   Syncing model Instrument
		- Downloading Instrument fixtures : done
	   Syncing model InstrumentType
		- Downloading InstrumentType fixtures : done
	   Syncing model Lentity
		- Downloading Lentity fixtures : done
	   Syncing model Organization
		- Downloading Organization fixtures : done
	   Syncing model Overseer
		- Downloading Overseer fixtures : done
	   Syncing model Person
		- Downloading Person fixtures : done
	   Syncing model PoliticalDivision
		- Downloading PoliticalDivision fixtures : done
	   Syncing model Station
		- Downloading Station fixtures : done
	   Syncing model StationType
		- Downloading StationType fixtures : done
	   Syncing model TimeStep
		- Downloading TimeStep fixtures : done
	   Syncing model TimeZone
		- Downloading TimeZone fixtures : done
	   Syncing model Timeseries
		- Downloading Timeseries fixtures : done
	   Syncing model UnitOfMeasurement
		- Downloading UnitOfMeasurement fixtures : done
	   Syncing model Variable
		- Downloading Variable fixtures : done
	   Syncing model WaterBasin
		- Downloading WaterBasin fixtures : done
	   Syncing model WaterDivision
		- Downloading WaterDivision fixtures : done
	   Creating Generic objects
	   Finished with Generic objects
	   Installing fixtures from file EventType.json
	   Installing fixtures from file FileType.json
	   Installing fixtures from file Gentity.json
	   Installing fixtures from file Garea.json
	   Installing fixtures from file GentityAltCode.json
	   Installing fixtures from file GentityAltCodeType.json
	   Installing fixtures from file GentityEvent.json
	   Installing fixtures from file GentityFile.json
	   Installing fixtures from file Gline.json
	   Installing fixtures from file Gpoint.json
	   Installing fixtures from file Instrument.json
	   Installing fixtures from file InstrumentType.json
	   Installing fixtures from file Lentity.json
	   Installing fixtures from file Organization.json
	   Installing fixtures from file Overseer.json
	   Installing fixtures from file Person.json
	   Installing fixtures from file PoliticalDivision.json
	   Installing fixtures from file Station.json
	   Installing fixtures from file StationType.json
	   Installing fixtures from file TimeStep.json
	   Installing fixtures from file TimeZone.json
	   Installing fixtures from file Timeseries.json
	   Installing fixtures from file UnitOfMeasurement.json
	   Installing fixtures from file Variable.json
	   Installing fixtures from file WaterBasin.json
	   Installing fixtures from file WaterDivision.json
	   Reinitializing foreign keys: done
	   Successfully installed 7319 objects from 26 fixtures.

The command above, replicates all remote data except for the UserProfiles (
defined using the ``-e|--exclude`` option) keeping all data and foreign keys
intact but without preserving the object ids. If run multiple times, the
script can also update existing entries along with adding new ones. It's
important to note that when replicating an enhydris database we should
*ALWAYS* exclude the UserProfile since we don't want user specific data to be
transfered along with the rest of the database.

When adding a cronjob, if you don't want a regural mail to come after every
sync, you should use the ``--silent`` option which redirects ``stdout`` to
``/dev/null`` and only prints ``stderr``. This, coupled with the ``-W`` python
flag can be used to make a cronjob send an email only whenever a problem was
encountered. A sample cronjob which runs every night would be something like
this::

	   1 0 * * * /usr/bin/python -Wignore manage.py hcore_remotesyncdb -a hcore -r itia.hydroscope.gr -e UserProfile  --silent

.. admonition:: How stuff works

	In this section, we'll analyze the replication script and see how it
	operates behind the scenes. Of course, if you want to understand how it
	works it's probably better if you looked directly into its source code. 
	Regarding the API which provides us with the database objects, it's been
        fully documented :ref:`here <webservice-api>`. Here, we'll see
        how the replication script handles that data and adds it in
        the local database. 

	One important thing that you should be familiar with before we delve into
	the code is the difficulties that we came across when trying to implement
	this feature. Postgres (and most databases by design) keep track of foreign
	keys using the primary key of an object which in all of enhydris models
	happens to be the object id. Since we want to aggregate multiple instances
	into one, it's only natural that there will be id collissions should we
	try to load the objects in the database while keeping their original id. 
	Thus, we decided that keeping the ids intact was not an option and we had
	to find a way to preserve foreign keys and many to many relations without
	counting on object ids.

	The best workaround is to add the objects without their foreign keys and
	many to many relationships and once the objects are in the database we
	could reinitialize all object relationships. To do that,  we added two
	extra fields on all top-level objects named ``original_id`` and
	``original_db`` which can be used to identify a specific object during the
	syncing process given that we know its id and the database that we're
	pulling the data from. Now the only thing was to somehow store the foreign
	relations in a way that could be parsed easily and quite fast after the
	object initialization. This was achieved using a multilevel dictionary
	which stores all object foreign relations and parsing this would be a
	breeze using python's optimized dictionary parsing routines. 

	Of course, that's when the real problems surfaced. Many objects have
	``Null=false`` in some foreign keys which caused the replication to fail
	when trying to save objects with null foreign keys. In order to circumvent
	that, when firing up the replication script we create a set of 
	``Dummy Objects`` aka objects that have null values and are used to
	fill-in the not-Null foreign key dependencies of the to-be-installed
	objects. Once the replication objects are into the database, we delete the
	Dummy Objects and update the foreign relations to the original ones which
	we have stored in the dictionary mentioned above. This may be a slow
	process but is the only feasible solution that we came up with at the
	time.

	Having said all that, we can see what the workflow of the script looks
	like. First of all, given the application name, it tries to import the
	specified app and list all available models in it. Using a multipass
	bubblesort algorithm, it sorts all models using their dependencies as
	specified in the ``f_dependencies`` model field and given that there are
	no circular dependencies, the final list contains the models in the
	correct replication order.

	Using the model list, the script asks from the remote instance the JSON
	fixture of each model in the list which is fetched and saved in a temporary
	dir (by default this is ``/tmp``). Once all JSON fixtures have been
	fetched, the script creates the generic objects and then deserializes
	each JSON file in the same order it was fetched. For each object within
	the fixture, it first strips all foreign relations and reinitializes the
	not-null ones using the generic objects. Also, the fields original_id and
	original_db are filled in and the foreign keys and 	many to many relations 
	are saved in a multilevel dictionary for future reference. 

	Once the deserialization of all fixtures has been completed, all objects
	are saved under the same transaction management because we don't want to
	have any objects left out from the replication routine.	If everything has
	been completed successfully, the script reinitializes all foreign keys and
	many to many relations from the dictionary and exits after cleaning up. If
	a problem occurs all transactions are rolled back and the database is
	exactly as it was before the replication attempt.

	**Note**:
		
	The generic objects which are used to fill temporary `Not Null`
	foreign relations are handcrafted. This means that should the Enhydris
	database schema	change drastically, this would probably require an update
	as well. 
