import ldap
from django.contrib.auth.models import User, Permission
from django.contrib.auth.backends import ModelBackend

# Users and groups are read from LDAP. A user is given permission to access the
# admin for schema SCHEMA if he belongs to an LDAP group named SCHEMA.

AUTH_LDAP_SERVER = 'ldap.itia.ntua.gr'
AUTH_LDAP_USERS_BASE = 'ou=people,dc=itia,dc=ntua,dc=gr'
AUTH_LDAP_BASE_USER = "uid=guest,ou=daemons,dc=itia,dc=ntua,dc=gr"
AUTH_LDAP_BASE_PASS = "foufotos"
AUTH_LDAP_USER_ELEMENT = "uid"
AUTH_LDAP_GROUPS_BASE = "ou=groups,dc=itia,dc=ntua,dc=gr"

class LDAPBackend(ModelBackend):
    def __init__(self):
        ModelBackend.__init__(self)
        self.ldap = ldap.open(AUTH_LDAP_SERVER)
        self.ldap.protocol_version = ldap.VERSION3
        self.ldap.simple_bind_s(AUTH_LDAP_BASE_USER,AUTH_LDAP_BASE_PASS)
    def authenticate(self, username=None, password=None):
        base = AUTH_LDAP_USERS_BASE
        scope = ldap.SCOPE_SUBTREE
        filter = "(&(objectclass=person) (%s=%s))" % (AUTH_LDAP_USER_ELEMENT,
                                                    username)
        ret = ['dn', 'givenName', 'sn', 'mail']

        try:
            # Authenticate the base user and search LDAP
            result_id = self.ldap.search(base, scope, filter, ret)
            result_type, result_data = self.ldap.result(result_id, 0)

            # If the user does not exist in LDAP, Fail.
            if (len(result_data) != 1):
                return None

            (user_dn, user_attrs) = result_data[0]

            # Attempt to bind to the user's DN
            self.ldap.simple_bind_s(user_dn,password)

            # The user existed and authenticated. Get the user
            # record or create one.
            try:
                user = User.objects.get(username__exact=username)
            except:
                user = User.objects.create_user(username,
                         username + '@nonexistent.placeholder', '')

            # Fill-in user data from LDAP
            user.set_unusable_password()
            user.first_name = user_attrs['givenName'][0]
            user.last_name = user_attrs['sn'][0]
            user.email = user_attrs['mail'][0]

            # Mark user as valid
            user.is_staff = True
            user.save()
            return user
           
        except:
            return None

    def get_group_permissions(self, user_obj):
        if not hasattr(user_obj, '_group_perm_cache'):
            user_obj._group_perm_cache = set()
            schemas_allowed = set()
            schemas_disallowed = set()
            for p in Permission.objects.all():
                schema = p.content_type.app_label
                if schema in schemas_disallowed: continue
                if schema in schemas_allowed:
                    user_obj._group_perm_cache.add("%s.%s" %
                                                        (schema, p.codename))
                    continue
                result_id = self.ldap.search(AUTH_LDAP_GROUPS_BASE,
                    ldap.SCOPE_SUBTREE, "(cn=%s)" % (schema,), ['memberUid'])
                result_type, result_data = self.ldap.result(result_id, 0)
                if(len(result_data) != 1):
                    schemas_disallowed.add(schema)
                    continue
                group_members = result_data[0][1]['memberUid']
                if user_obj.username in group_members:
                    user_obj._group_perm_cache.add("%s.%s" %
                                                        (schema, p.codename))
                    schemas_allowed.add(schema)
                else:
                    schemas_disallowed.add(schema)
        return user_obj._group_perm_cache
