.. _permissions:

:mod:`permissions` --- Permissions
==================================

.. module:: permissions
   :synopsis: Enhydris Permission Implementation
.. moduleauthor:: Seraphim Mellos <mellos@indifex.com>
.. sectionauthor:: Seraphim Mellos <mellos@indifex.com>

This module implements row level permission handling to use along with
django's generic permissions provided by the django.contrib.auth module. More
precissely, this module extends the User and Group models with a couple of
methods which take care of adding,deleting and checking of permissions. The
:class:`Permission` class keeps log of all existing permissions in the
database.

Permission Objects
------------------

Each instance of the :class:`Permission` class represents a relationship
between a user and an object and it is identified by its name. The permission
name can be any string like 'edit', 'read' or 'delete' and usually describes
the kind of permission it implements. 


.. class:: Permission(name, content_type, object_id, content_object[,User, Group]) 


	.. attribute:: name

		The name of the permission. Usually it's a string denoting the meaning
		of the permission ( eg 'edit', 'read', 'delete', etc)

	.. attribute:: content_type

		This attribute stores the content type of the object over which this
		permission is effective.

	.. attribute:: object_id
		
		This is the id of the related object.

 	.. attribute:: content_object

		This is a foreign key to the actual object (object instance) over
		this permission is effective.

 	.. attribute:: user

		If the permission is effective for a single user, this field points
		to this user otherwise it is null.

	.. attribute:: group 
		
		If the permission is effective for a whole group, this field points to
		this group otherwise it is null. 


User/Group methods
------------------

As told before, the row level permissions add various methods to the User and
Group models with which one can add/edit/delete permissions over various
objects and/or QuerySets.

class User_:
	
.. _User: http://docs.djangoproject.com/en/1.1/topics/auth/#django.contrib.auth.models.User   

	.. method:: add_row_perm(instance, perm) 
		
		This method takes an object instance and the name of the permission
		and adds this permission for the calling user over the object instance
		given. For example: ::
			
			>>> station = Station.objects.get(id='10001')
			>>> user = User.objects.get(username='testuser')
			>>> user.add_row_perm(station, 'edit')			 

			
	.. method:: del_row_perm(instance, perm) 

		This method takes an object instance and a permission name and if the
		user has that permission over the object, the method deletes it. If
		the user doesn't have that permisssion, nothing happens. ::

			>>> station = Station.objects.get(id='10001')
			>>> user = User.objects.get(username='testuser')
			>>> user.del_row_perm(station, 'edit')			 

	.. method:: has_row_perm(instance, perm) 

		This method takes an object instance and a permission name and checks
		whether the calling user has that permission over the object instance.
		If this method is called from a superuser, it always returns
		:const:`True`. For example: ::

			>>> station = Station.objects.get(id='10001')
			>>> user = User.objects.get(username='testuser')
			>>> user.has_row_perm(station, 'edit')			 
			False

	.. method:: get_rows_with_permission(instance, perm) 

		This method is used to return all instances of the same conten type as
		the given instance over which the user has the *perm* permission.
		For example: ::

			>>> user = User.objects.get(username='testuser')
			>>> user.get_rows_with_permission(Station,'edit')

		This will return all Stations that the user can 'edit'. 

class Group_:
	
.. _Group: http://docs.djangoproject.com/en/1.1/topics/auth/#django.contrib.auth.models.Group 

		All methods and their usage are the same as with User. However, it's
		worth noting that once a user inherits a permission from a group, the
		only way to remove that permission is to leave the group since using
		`del_row_perm()` from the user won't affect the group
		permissions.

	.. method:: add_row_perm(instance, perm) 
	.. method:: del_row_perm(instance, perm) 
	.. method:: has_row_perm(instance, perm) 
	.. method:: get_rows_with_permission(instance, perm) 
