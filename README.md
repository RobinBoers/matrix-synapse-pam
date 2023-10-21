# PAM auth provider for Synapse

Allows Synapse to use UNIX accounts through PAM.

## Installation

```shell
git clone https://github.com/RobinBoers/matrix-synapse-pam
sudo cp ./matrix-synapse-pam/pam_auth_provider.py /opt/venvs/matrix-synapse/lib/python3.11/site-packages
```

This auth provider depends on [`pwauth`](https://manpages.debian.org/stretch/pwauth/pwauth.8.en.html).

## Usage

Example Synapse config:

```yaml
modules:
  - module: "pam_auth_provider.PAMAuthProvider"
    config:
      create_users: true
      skip_user_check: false
```

The `create_users` key specifies whether to create Matrix accounts
for valid system accounts.

The `skip_user_check` key can be used to skip verifying the existence of the user
with NSS, in case PAM uses a different user database.

## Copyright

This software is copyright 2017-2023 by Willem Mulder and licensed under the [EUPL](https://joinup.ec.europa.eu/software/page/eupl).
