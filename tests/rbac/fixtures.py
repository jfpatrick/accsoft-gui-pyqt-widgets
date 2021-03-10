from typing import List, Union, Optional, cast
from unittest import mock
from datetime import datetime
from urllib.parse import quote
from pyrbac import AccountType
from accwidgets.rbac import RbaRole


def mocked_account_type_to_str(input: int):
    return AccountType(input).name


def make_token(loc_auth_reqd: bool = False,
               roles: Union[List[RbaRole], List[str], None] = None,
               auth_timestamp: Optional[datetime] = None,
               expiration_timestamp: Optional[datetime] = None,
               valid: bool = True):
    auth_timestamp = auth_timestamp or datetime.now()
    expiration_timestamp = expiration_timestamp or datetime.now()
    if roles is None:
        roles = cast(List[str], [])

    def filter_roles(r: Union[str, RbaRole]) -> bool:
        if isinstance(r, str):
            return True
        return r.active

    token = mock.MagicMock()
    token.get_user_name.return_value = "TEST_USERNAME"
    token.get_full_name.return_value = "TEST_FULL_NAME"
    token.get_user_email.return_value = "TEST_EMAIL"
    token.get_account_type.return_value = 2
    token.is_token_expired.return_value = not valid
    token.empty.return_value = False
    token.get_authentication_time.return_value = auth_timestamp.timestamp()
    token.get_expiration_time.return_value = expiration_timestamp.timestamp()
    token.get_roles.return_value = [r.name if isinstance(r, RbaRole) else r for r in filter(filter_roles, roles)]
    token.get_extra_fields.return_value.get_roles_lifetime.return_value = [r.lifetime if isinstance(r, RbaRole)
                                                                           else -1 for r in filter(filter_roles, roles)]
    token.get_application_name.return_value = "TEST_APP"
    token.get_location_name.return_value = "TEST_LOC"
    token.get_location_address.return_value = "10.10.255.255"
    token.is_location_auth_required.return_value = loc_auth_reqd
    token.get_serial_id.return_value = 3235826430  # 0xc0decafe
    role_names = "\n".join([quote(r) for r in token.get_roles])
    loc_bytes = "".join([f"{int(i):X}" for i in token.get_location_address().split(".")])
    encoded_string = "14\n" \
                     "ApplicationName\n" \
                     "string\n" \
                     f"{len(quote(token.get_application_name()))}\n" \
                     f"{quote(token.get_application_name())}\n" \
                     "UserName\n" \
                     "string\n" \
                     f"{len(quote(token.get_user_name()))}\n" \
                     f"{quote(token.get_user_name())}\n" \
                     "LocationAuthReq\n" \
                     "bool\n" \
                     "false\n" \
                     "AuthenticationTime\n" \
                     "int\n" \
                     f"{auth_timestamp.timestamp()}\n" \
                     "Roles\n" \
                     "string_array\n" \
                     f"{len(roles)}\n" \
                     f"{role_names}\n" \
                     "ExpirationTime\n" \
                     "int\n" \
                     f"{expiration_timestamp.timestamp()}\n" \
                     "UserEmail\n" \
                     "string\n" \
                     f"{len(token.get_user_email())}\n" \
                     f"{token.get_user_email()}\n" \
                     "LocationName\n" \
                     "string\n" \
                     f"{len(quote(token.get_location_name()))}\n" \
                     f"{quote(token.get_location_name())}\n" \
                     "UserAccountType\n" \
                     "string\n" \
                     "7\n" \
                     "Service\n" \
                     "ApplicationCritical\n" \
                     "bool\n" \
                     "false\n" \
                     "ApplicationTimeout\n" \
                     "int\n" \
                     "-1\n" \
                     "LocationAddress\n" \
                     "byte_array\n" \
                     f"{len(token.get_location_address())}\n" \
                     f"{loc_bytes}\n" \
                     "SerialId\n" \
                     "int\n" \
                     f"{token.get_serial_id()}\n" \
                     "UserFullName\n" \
                     "string\n" \
                     f"{len(quote(token.get_full_name()))}\n" \
                     f"{quote(token.get_full_name())}\n" \
                     "SOME_HASHSUM_BYTES_HERE"
    token.get_encoded.return_value = encoded_string.encode("utf-8")
    return token
