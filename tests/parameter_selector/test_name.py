import pytest
from accwidgets.parameter_selector._name import ParameterName


@pytest.mark.parametrize("param_name,expected_protocol,expected_service,expected_dev,expected_prop,expected_field", [
    ("device/property", None, None, "device", "property", None),
    ("device/property#field", None, None, "device", "property", "field"),
    ("protocol:///device/property", "protocol", None, "device", "property", None),
    ("protocol:///device/property#field", "protocol", None, "device", "property", "field"),
    ("protocol://service/device/property", "protocol", "service", "device", "property", None),
    ("protocol://service/device/property#field", "protocol", "service", "device", "property", "field"),
    ("device/YA.PRE.YDPLC01=CCC_KEY_ION:ON", None, None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    ("device/YA.PRE.YDPLC01=CCC_KEY_ION:ON#field", None, None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    ("protocol:///device/YA.PRE.YDPLC01=CCC_KEY_ION:ON", "protocol", None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    ("protocol:///device/YA.PRE.YDPLC01=CCC_KEY_ION:ON#field", "protocol", None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    ("protocol://service/device/YA.PRE.YDPLC01=CCC_KEY_ION:ON", "protocol", "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    ("protocol://service/device/YA.PRE.YDPLC01=CCC_KEY_ION:ON#field", "protocol", "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
])
def test_from_string_succeeds(param_name, expected_protocol, expected_service, expected_dev, expected_prop, expected_field):
    addr = ParameterName.from_string(param_name)
    assert addr is not None
    assert addr.valid
    assert addr.protocol == expected_protocol
    assert addr.service == expected_service
    assert addr.device == expected_dev
    assert addr.prop == expected_prop
    assert addr.field == expected_field


@pytest.mark.parametrize("field", [
    "#field",
    "",
])
@pytest.mark.parametrize("param_name", [
    "device/property",
    "protocol:///device/property",
    "protocol://service/device/property",
    "device/YA.PRE.YDPLC01=CCC_KEY_ION:ON",
    "protocol:///device/YA.PRE.YDPLC01=CCC_KEY_ION:ON",
    "protocol://service/device/YA.PRE.YDPLC01=CCC_KEY_ION:ON",
])
def test_from_string_repr(param_name, field):
    input_str = f"{param_name}{field}"
    addr = ParameterName.from_string(input_str)
    assert addr.valid
    assert str(addr) == input_str


@pytest.mark.parametrize("param_name", [
    "device",
    "device/",
    "device/property#",
    "/property",
    "/device/property",
    "/device/property#field",
    "property#field",
    "protocol://device",
    "protocol://device/property",
    "protocol://device/property#field",
    "protocol://device/#field",
    "protocol://service/device",
    "protocol://service/device/",
    "protocol://service/device/#",
    "protocol://service/device#field",
    "protocol://service/device/#field",
    "protocol://service//#",
    "protocol://service//#field",
    "service/device/property",
    "service/device/property#field",
    "protocol:///device",
    "protocol:///device#field",
    "///service/device/property",
    "///service/device#field",
    "///service/device/property#",
    "///service/device/#field",
])
def test_from_string_fails_invalid_address(param_name):
    addr = ParameterName.from_string(param_name)
    assert addr is None


@pytest.mark.parametrize("device,expected_device", [
    ("", ""),
    ("dev", "dev"),
])
@pytest.mark.parametrize("prop,expected_prop", [
    ("", ""),
    ("prop", "prop"),
])
@pytest.mark.parametrize("optionals,expected_field,expected_protocol,expected_service", [
    ({}, None, None, None),
    ({"field": ""}, "", None, None),
    ({"field": "field"}, "field", None, None),
    ({"field": None}, None, None, None),
    ({"protocol": ""}, None, "", None),
    ({"protocol": "rda3"}, None, "rda3", None),
    ({"protocol": None}, None, None, None),
    ({"service": ""}, None, None, ""),
    ({"service": "srv"}, None, None, "srv"),
    ({"service": None}, None, None, None),
    ({"field": "field", "protocol": "rda3"}, "field", "rda3", None),
    ({"field": "field", "protocol": None}, "field", None, None),
    ({"field": "field", "service": "srv"}, "field", None, "srv"),
    ({"field": "field", "service": None}, "field", None, None),
    ({"protocol": "rda3", "service": "srv"}, None, "rda3", "srv"),
    ({"protocol": None, "service": None}, None, None, None),
    ({"field": "field", "protocol": "rda3", "service": "srv"}, "field", "rda3", "srv"),
])
def test_init(device, expected_service, expected_protocol, expected_device, prop, expected_field, expected_prop,
              optionals):
    addr = ParameterName(device=device,
                         prop=prop,
                         **optionals)
    assert addr.device == expected_device
    assert addr.prop == expected_prop
    assert addr.field == expected_field
    assert addr.service == expected_service
    assert addr.protocol == expected_protocol


@pytest.mark.parametrize("expect_valid,protocol,service,device,prop,field", [
    (True, None, None, "device", "property", None),
    (True, None, None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, None, None, "device", "property", "field"),
    (True, None, None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (False, None, "service", "device", "property", None),
    (False, None, "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (False, None, "service", "device", "property", "field"),
    (False, None, "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (True, "protocol", None, "device", "property", None),
    (True, "protocol", None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, "protocol", None, "device", "property", "field"),
    (True, "protocol", None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (True, "protocol", "service", "device", "property", None),
    (True, "protocol", "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, "protocol", "service", "device", "property", "field"),
    (True, "protocol", "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (True, "protocol", "protocol", "device", "property", None),
    (True, "protocol", "protocol", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, "protocol", "protocol", "device", "property", "field"),
    (True, "protocol", "protocol", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (True, None, None, "device", "property", None),
    (True, None, None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, None, None, "device", "property", "field"),
    (True, None, None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (False, None, "service", "device", "property", None),
    (False, None, "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (False, None, "service", "device", "property", "field"),
    (False, None, "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (True, "protocol", None, "device", "property", None),
    (True, "protocol", None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, "protocol", None, "device", "property", "field"),
    (True, "protocol", None, "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (True, "protocol", "service", "device", "property", None),
    (True, "protocol", "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, "protocol", "service", "device", "property", "field"),
    (True, "protocol", "service", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
    (True, "protocol", "protocol", "device", "property", None),
    (True, "protocol", "protocol", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", None),
    (True, "protocol", "protocol", "device", "property", "field"),
    (True, "protocol", "protocol", "device", "YA.PRE.YDPLC01=CCC_KEY_ION:ON", "field"),
])
def test_is_valid(expect_valid, protocol, service, device, prop, field):
    # cases without device or property are not tested, because they are required arguments
    addr = ParameterName(protocol=protocol, service=service, device=device, prop=prop, field=field)
    assert addr.valid == expect_valid


@pytest.mark.parametrize("field", ["", None, "field"])
@pytest.mark.parametrize("orig_proto,orig_service,new_proto,expected_service", [
    (None, None, None, None),
    ("", None, None, None),
    ("proto", None, None, None),
    (None, "", None, None),
    ("", "", None, None),
    ("proto", "", None, None),
    (None, "srv", None, None),
    ("", "srv", None, None),
    ("proto", "srv", None, None),
    (None, None, "", None),
    ("", None, "", None),
    ("proto", None, "", None),
    (None, "", "", ""),
    ("", "", "", ""),
    ("proto", "", "", ""),
    (None, "srv", "", "srv"),
    ("", "srv", "", "srv"),
    ("proto", "srv", "", "srv"),
    (None, None, "newproto", None),
    ("", None, "newproto", None),
    ("proto", None, "newproto", None),
    (None, "", "newproto", ""),
    ("", "", "newproto", ""),
    ("proto", "", "newproto", ""),
    (None, "srv", "newproto", "srv"),
    ("", "srv", "newproto", "srv"),
    ("proto", "srv", "newproto", "srv"),
])
def test_removes_service_if_protocol_is_removed(orig_proto, orig_service, new_proto, expected_service, field):
    addr = ParameterName(protocol=orig_proto, service=orig_service, device="test", prop="prop", field=field)
    assert addr.protocol == orig_proto
    assert addr.service == orig_service
    addr.protocol = new_proto
    assert addr.protocol == new_proto
    assert addr.service == expected_service
