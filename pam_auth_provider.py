# Copyright 2017, 2021 Willem Mulder
#
# Licensed under the EUPL, Version 1.2 or - as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#
# https://joinup.ec.europa.eu/software/page/eupl
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and
# limitations under the Licence.

"""Module containing the PAM auth provider for the Synapse Matrix server."""

import logging
import pwd
from collections import namedtuple
from typing import Awaitable, Callable, Optional, Tuple

import pam

import synapse
from synapse import module_api

class PAMAuthProvider:
    """PAM auth provider for the Synapse Matrix server."""

    def __init__(self, *, config: dict, api: module_api):
        self.api = api
        self.create_users = config.create_users
        self.skip_user_check = config.skip_user_check
        api.register_password_auth_provider_callbacks(
            auth_checkers={
                                ("m.login.password", ("password",)): self.check_password,
                })

    async def check_password(
    self,
    user_id: str,
    login_type: str,
    login_dict: "synapse.module_api.JsonDict",
) -> Optional[Tuple[str, Optional[Callable[["synapse.module_api.LoginResponse"], Awaitable[None]]]]]:
        """Check user/password against PAM, optionally creating the user."""
        if login_type != "m.login.password":
            return None

        password = login_dict.get('password')
        if password is None:
            logging.debug("Password was None")
            return None

        user_id =  self.api.get_qualified_user_id(user_id)
        localpart = user_id.split(':')[0][1:]
        logging.debug(f"user_id={user_id}, localpart={localpart}")

        # check whether user even exists
        if not self.skip_user_check:
            try:
                pwd.getpwnam(localpart)
            except KeyError:
                logging.debug(f"{localpart} is not in the passwd database")
                return None

        # Now check the password
        if not pam.pam().authenticate(localpart, password):
            logging.debug(f"PAM authentication failed for {localpart}")
            return None

        # From here on, the user is authenticated

        # Create the user in Matrix if it doesn't exist yet
        if (await self.api.check_user_exists(user_id)) is None:
            # Bail if we don't want to create users in Matrix
            if not self.create_users:
                logging.info(f"{localpart} does not already exist")
                return None

            user_id = await self.api.register_user(localpart=localpart)
            logging.info(f"New user_id={user_id}")

        return (user_id, None)

    @staticmethod
    def parse_config(config):
        """Parse the configuration for use in __init__."""
        pam_config = namedtuple('_Config', 'create_users')
        pam_config.create_users = config.get('create_users', True)
        pam_config.skip_user_check = config.get('skip_user_check', False)

        return pam_config
