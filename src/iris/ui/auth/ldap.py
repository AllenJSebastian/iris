# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from __future__ import absolute_import
import logging
import ldap
import os

logger = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, config):
        root = os.path.abspath('./')
        if config.get('debug'):
            self.authenticate = self.debug_auth
            return
        self.authenticate = self.ldap_auth

        if 'ldap_cert_path' in config['auth']:
            self.cert_path = os.path.join(root, config['auth']['ldap_cert_path'])
            if not os.access(self.cert_path, os.R_OK):
                logger.error("Failed to read ldap_cert_path certificate")
                raise IOError
        else:
            self.cert_path = None

        self.bind_user = config['auth'].get('ldap_bind_user')
        self.bind_password = config['auth'].get('ldap_bind_password')
        self.search_filter = config['auth'].get('ldap_search_filter')

        self.ldap_url = config['auth'].get('ldap_url')
        self.base_dn = config['auth'].get('ldap_base_dn')

        self.user_suffix = config['auth'].get('ldap_user_suffix')

    def ldap_auth(self, username, password):
        if self.cert_path:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.cert_path)
        connection = ldap.initialize(self.ldap_url)
        connection.set_option(ldap.OPT_REFERRALS, 0)

        if not password:
            return False

        auth_user = username + self.user_suffix
        try:
            if self.bind_user:
                # use search filter to find DN of username
                connection.simple_bind_s(self.bind_user, self.bind_password)
                sfilter = self.search_filter % username
                result = connection.search_s(self.base_dn, ldap.SCOPE_SUBTREE, sfilter, ['dn'])
                if len(result) < 1:
                    return False
                auth_user = result[0][0]

            connection.simple_bind_s(auth_user, password)

        except ldap.INVALID_CREDENTIALS:
            return False
        except (ldap.SERVER_DOWN, ldap.INVALID_DN_SYNTAX) as err:
            logger.warn("%s", err)
            return None
        return True

    def debug_auth(self, username, password):
        return True
