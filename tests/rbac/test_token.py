import pytest
import pyrbac
from datetime import datetime
from unittest import mock
from ipaddress import IPv4Address
from accwidgets.rbac import RbaRole, RbaToken
from .fixtures import make_token


@pytest.mark.parametrize("name,critical", [
    ("AAA", False),
    ("XXX", False),
    ("MCS-", True),
    ("mcs-", False),
    ("MCS-smth", True),
    ("mcs-smth", False),
    ("AAA-MCS-XXX", False),
])
def test_rbac_role_critical(name, critical):
    assert RbaRole(name=name).is_critical == critical


@pytest.mark.parametrize("second_obj_type,equal_by_type", [
    (RbaRole, True),
    (mock.MagicMock, False),
])
@pytest.mark.parametrize("lifetime1", [None, -1, 0, 10])
@pytest.mark.parametrize("lifetime2", [None, -1, 0, 10])
@pytest.mark.parametrize("active1", [True, False])
@pytest.mark.parametrize("active2", [True, False])
@pytest.mark.parametrize("name1,name2,equal_by_name", [
    ("AAA", None, False),
    ("AAA", "", False),
    ("AAA", "AAA-", False),
    ("AAA", "MCS-AAA", False),
    ("AAA", "AAA", True),
    ("AAA", "aaa", False),
])
def test_rbac_role_equality(second_obj_type, equal_by_name, equal_by_type,
                            lifetime1, lifetime2, active1, active2, name1, name2):
    role1 = RbaRole(name=name1, lifetime=lifetime1, active=active1)
    role2 = second_obj_type(name=name2, lifetime=lifetime2, active=active2)
    assert (role1 == role2) == (equal_by_type and equal_by_name)


@pytest.mark.parametrize("src_acc_type,expected_acc_str", [
    (pyrbac.AccountType.AT_PRIMARY, "Primary"),
    (pyrbac.AccountType.AT_SECONDARY, "Secondary"),
    (pyrbac.AccountType.AT_SERVICE, "Service"),
    (pyrbac.AccountType.AT_UNKNOWN, "Unknown"),
])
@pytest.mark.parametrize("src_is_expired,expected_valid", [
    (True, False),
    (False, True),
])
@pytest.mark.parametrize("login_method", [RbaToken.LoginMethod.UNKNOWN, RbaToken.LoginMethod.LOCATION, RbaToken.LoginMethod.EXPLICIT])
@pytest.mark.parametrize("auto_renewable", [True, False])
@pytest.mark.parametrize("empty", [True, False])
@pytest.mark.parametrize("valid", [True, False])
@pytest.mark.parametrize("loc_auth_required", [True, False])
@pytest.mark.parametrize("src_lifetimes,expected_lifetimes", [
    (None, [-1, -1, -1, -1, -1, -1, -1, -1]),  # Assume extra_fields == None for this
    ([], [-1, -1, -1, -1, -1, -1, -1, -1]),
    ([1, 2, 3, 4], [1, 2, -1, -1, 3, 4, -1, -1]),
])
def test_token_wrapper(src_acc_type, expected_acc_str, src_is_expired, expected_valid, empty, loc_auth_required,
                       src_lifetimes, expected_lifetimes, auto_renewable, login_method, valid):
    ll_token = make_token(loc_auth_reqd=loc_auth_required,
                          valid=valid,
                          roles=["Role1", "Role2", "MCS-Role1", "MCS-Role2"],
                          auth_timestamp=datetime(2020, 1, 1, 12, 53, 23),
                          expiration_timestamp=datetime(2020, 1, 1, 13, 0, 0))
    ll_token.get_account_type.return_value = src_acc_type
    ll_token.is_token_expired.return_value = src_is_expired
    ll_token.empty.return_value = empty
    if src_lifetimes is None:
        ll_token.get_extra_fields.return_value = None
    else:
        ll_token.get_extra_fields.return_value.get_roles_lifetime.return_value = src_lifetimes

    all_roles = ["Role1",
                 "Role2",
                 "Role3",
                 "Role4",
                 "MCS-Role1",
                 "MCS-Role2",
                 "MCS-Role3",
                 "MCS-Role4"]
    active_roles = [True, True, False, False, True, True, False, False]

    token = RbaToken(original_token=ll_token,
                     available_roles=all_roles,
                     login_method=login_method,
                     auto_renewable=auto_renewable)
    assert token.username == "TEST_USERNAME"
    assert token.user_email == "TEST_EMAIL"
    assert token.user_full_name == "TEST_FULL_NAME"
    assert token.account_type == expected_acc_str
    assert token.valid == expected_valid
    assert token.empty == empty
    assert token.auto_renewable == auto_renewable
    assert token.login_method == login_method
    assert token.auth_timestamp == datetime(2020, 1, 1, 12, 53, 23)
    assert token.expiration_timestamp == datetime(2020, 1, 1, 13, 0, 0)
    assert token.roles == [RbaRole(name=name, lifetime=lifetime, active=active)
                           for name, lifetime, active in zip(all_roles, expected_lifetimes, active_roles)]
    assert token.app_name == "TEST_APP"
    assert token.location is not None
    assert token.location.name == "TEST_LOC"
    assert token.location.address == IPv4Address("10.10.255.255")
    assert token.location.auth_required == loc_auth_required
    assert token.serial_id == "0xc0decafe"


@pytest.mark.parametrize("login_method", [RbaToken.LoginMethod.LOCATION, RbaToken.LoginMethod.EXPLICIT, RbaToken.LoginMethod.UNKNOWN])
@pytest.mark.parametrize("auto_renewable", [True, False])
@pytest.mark.parametrize("valid", [True, False])
@pytest.mark.parametrize("token_encoded,expected_result", [
    (b"AQIFBgc=", b"AQIFBgc="),
    (b"BwQGCAUGBAYIBAM=", b"BwQGCAUGBAYIBAM="),
])
def test_token_get_encoded(token_encoded, expected_result, login_method, auto_renewable, valid):
    ll_token = make_token(valid=valid,
                          roles=["Role1", "Role2", "MCS-Role1", "MCS-Role2"],
                          auth_timestamp=datetime(2020, 1, 1, 12, 53, 23),
                          expiration_timestamp=datetime(2020, 1, 1, 13, 0, 0))
    ll_token.get_encoded.return_value = token_encoded

    all_roles = ["Role1",
                 "Role2",
                 "Role3",
                 "Role4",
                 "MCS-Role1",
                 "MCS-Role2",
                 "MCS-Role3",
                 "MCS-Role4"]
    token = RbaToken(original_token=ll_token,
                     available_roles=all_roles,
                     login_method=login_method,
                     auto_renewable=auto_renewable)

    assert token.get_encoded() == expected_result
