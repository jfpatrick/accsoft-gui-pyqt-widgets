import operator
import pytest
from unittest import mock
from pyccda.models import PropertyField, PropertyFieldEnum, DeviceClassProperty
from accwidgets.property_edit.propedit import (PropertyEdit, PropertyEditField, _NUM_MAX_KEY,
                                               _NUM_MIN_KEY, _ENUM_OPTIONS_KEY, _NUM_UNITS_KEY)
from accwidgets.property_edit.designer.ccda_resolver import (_user_data_for_type, _get_type, _map_fields_sorted,
                                                             _resolve_from_param)
from ..async_shim import AsyncMock


@pytest.mark.asyncio
@pytest.mark.parametrize("param,expected_error", [
    ("", 'Invalid parameter name ""'),
    ("asd", 'Invalid parameter name "asd"'),
    ("dev/prop/field", 'Invalid parameter name "dev/prop/field"'),
])
async def test_resolve_from_param_invalid_param(param, expected_error):
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver._map_fields_sorted") as map_fields_sorted:
        with pytest.raises(ValueError, match=expected_error):
            await _resolve_from_param(param)
        map_fields_sorted.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("lookup_prop,expected_error", [
    ("prop1", None),
    ("prop2", r'Device "dev" does not have a property "prop2"'),
])
async def test_resolve_from_param_no_property_exists(lookup_prop, expected_error):
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.CCDA") as CCDA:
        with mock.patch("accwidgets.property_edit.designer.ccda_resolver._map_fields_sorted") as map_fields_sorted:
            device_mock = mock.MagicMock()
            CCDA.return_value.Device.find = AsyncMock(return_value=device_mock)
            class_mock = mock.MagicMock()
            device_mock.device_class = AsyncMock(return_value=class_mock)
            class_mock.device_class_properties = [DeviceClassProperty(name="prop1")]

            param_name = f"dev/{lookup_prop}"
            if expected_error is None:
                await _resolve_from_param(param_name)
                map_fields_sorted.assert_called_once()
            else:
                with pytest.raises(ValueError, match=expected_error):
                    await _resolve_from_param(param_name)
                map_fields_sorted.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("param_name", ["dev/prop1", "dev/prop1#field"])
async def test_resolve_from_param_succeeds(param_name):
    with mock.patch("accwidgets.property_edit.designer.ccda_resolver.CCDA") as CCDA:
        with mock.patch("accwidgets.property_edit.designer.ccda_resolver._map_fields_sorted") as map_fields_sorted:
            device_mock = mock.MagicMock()
            CCDA.return_value.Device.find = AsyncMock(return_value=device_mock)
            class_mock = mock.MagicMock()
            device_mock.device_class = AsyncMock(return_value=class_mock)
            data_field = PropertyField(name="field1")
            class_mock.device_class_properties = [DeviceClassProperty(name="prop1", data_fields=[data_field])]

            await _resolve_from_param(param_name)
            map_fields_sorted.assert_called_once_with([data_field])


def test_map_field_sorted_skips_unsupported_types():
    fields = [
        PropertyField(name="prop1", data_type="array", primitive_data_type="STRING"),
        PropertyField(name="prop2", data_type="array2D", primitive_data_type="INT"),
        PropertyField(name="prop3", data_type="scalar", primitive_data_type="FLOAT"),
        PropertyField(name="prop4", data_type="function", primitive_data_type="DISCRETE_FUNCTION"),
        PropertyField(name="prop5", data_type="scalar", primitive_data_type="DISCRETE_FUNCTION"),
    ]
    mapped_fields, skipped = _map_fields_sorted(fields)
    assert skipped == {"prop1", "prop2", "prop4", "prop5"}
    assert list(map(operator.attrgetter("field"), mapped_fields)) == ["prop3"]


def test_map_field_sorted_sorts_results():
    fields = [
        PropertyField(name="prop1", data_type="scalar", primitive_data_type="STRING"),
        PropertyField(name="prop3", data_type="bit_enum", property_field_enums=[PropertyFieldEnum(enum_symbol="ONE", value=1)]),
        PropertyField(name="prop4", data_type="scalar", primitive_data_type="INT"),
        PropertyField(name="prop2", data_type="scalar", primitive_data_type="FLOAT", min_value=32, max_value=64),
    ]
    mapped_fields, _ = _map_fields_sorted(fields)
    names = list(map(operator.attrgetter("field"), mapped_fields))
    assert names == ["prop1", "prop2", "prop3", "prop4"]


def test_map_field_sorted_maps_data_structures():
    fields = [
        PropertyField(name="prop1", data_type="scalar", primitive_data_type="STRING"),
        PropertyField(name="prop2", data_type="scalar", primitive_data_type="FLOAT", min_value=32, max_value=64),
        PropertyField(name="prop3", data_type="bit_enum", property_field_enums=[PropertyFieldEnum(enum_symbol="ONE", value=1)]),
        PropertyField(name="prop4", data_type="scalar", primitive_data_type="INT"),
    ]
    mapped_fields, skipped = _map_fields_sorted(fields)
    assert not skipped
    assert mapped_fields == [
        PropertyEditField(field="prop1",
                          type=PropertyEdit.ValueType.STRING,
                          editable=False,
                          user_data=None),
        PropertyEditField(field="prop2",
                          type=PropertyEdit.ValueType.REAL,
                          editable=False,
                          user_data={_NUM_MIN_KEY: 32, _NUM_MAX_KEY: 64}),
        PropertyEditField(field="prop3",
                          type=PropertyEdit.ValueType.ENUM,
                          editable=False,
                          user_data={_ENUM_OPTIONS_KEY: [("ONE", 1)]}),
        PropertyEditField(field="prop4",
                          type=PropertyEdit.ValueType.INTEGER,
                          editable=False,
                          user_data=None),
    ]


@pytest.mark.parametrize("ccda_field,expected_type", [
    (PropertyField(data_type="bit_enum"), PropertyEdit.ValueType.ENUM),
    (PropertyField(data_type="scalar"), None),
    (PropertyField(), None),
    (PropertyField(data_type="bit_enum", property_field_enums=[]), PropertyEdit.ValueType.ENUM),
    (PropertyField(data_type="bit_enum", property_field_enums=[PropertyFieldEnum(enum_symbol="ONE", value=1)]), PropertyEdit.ValueType.ENUM),
    (PropertyField(data_type="bit_enum", property_field_enums=[], primitive_data_type="INT"), PropertyEdit.ValueType.ENUM),
    (PropertyField(data_type="bit_enum", property_field_enums=[], primitive_data_type="STRING"), PropertyEdit.ValueType.ENUM),
    (PropertyField(data_type="scalar", primitive_data_type="BOOL"), PropertyEdit.ValueType.BOOLEAN),
    (PropertyField(data_type="scalar", primitive_data_type="INT"), PropertyEdit.ValueType.INTEGER),
    (PropertyField(data_type="scalar", primitive_data_type="LONG"), PropertyEdit.ValueType.INTEGER),
    (PropertyField(data_type="scalar", primitive_data_type="SHORT"), PropertyEdit.ValueType.INTEGER),
    (PropertyField(data_type="scalar", primitive_data_type="FLOAT"), PropertyEdit.ValueType.REAL),
    (PropertyField(data_type="scalar", primitive_data_type="DOUBLE"), PropertyEdit.ValueType.REAL),
    (PropertyField(data_type="scalar", primitive_data_type="STRING"), PropertyEdit.ValueType.STRING),
    (PropertyField(data_type="scalar", primitive_data_type="BYTE"), PropertyEdit.ValueType.INTEGER),
    (PropertyField(data_type="scalar", primitive_data_type="CHAR"), PropertyEdit.ValueType.STRING),
    (PropertyField(data_type="scalar", primitive_data_type="DISCRETE_FUNCTION_LIST"), None),
    (PropertyField(data_type="scalar", primitive_data_type="DISCRETE_FUNCTION"), None),
    (PropertyField(data_type="array", primitive_data_type="DISCRETE_FUNCTION_LIST"), None),
    (PropertyField(data_type="function", primitive_data_type="DISCRETE_FUNCTION"), None),
    (PropertyField(data_type="array", primitive_data_type="BOOL"), None),
    (PropertyField(data_type="array", primitive_data_type="INT"), None),
    (PropertyField(data_type="array", primitive_data_type="LONG"), None),
    (PropertyField(data_type="array", primitive_data_type="SHORT"), None),
    (PropertyField(data_type="array", primitive_data_type="FLOAT"), None),
    (PropertyField(data_type="array", primitive_data_type="DOUBLE"), None),
    (PropertyField(data_type="array", primitive_data_type="STRING"), None),
    (PropertyField(data_type="array", primitive_data_type="BYTE"), None),
    (PropertyField(data_type="array", primitive_data_type="CHAR"), None),
    (PropertyField(data_type="array2D", primitive_data_type="BOOL"), None),
    (PropertyField(data_type="array2D", primitive_data_type="INT"), None),
    (PropertyField(data_type="array2D", primitive_data_type="LONG"), None),
    (PropertyField(data_type="array2D", primitive_data_type="SHORT"), None),
    (PropertyField(data_type="array2D", primitive_data_type="FLOAT"), None),
    (PropertyField(data_type="array2D", primitive_data_type="DOUBLE"), None),
    (PropertyField(data_type="array2D", primitive_data_type="STRING"), None),
    (PropertyField(data_type="array2D", primitive_data_type="BYTE"), None),
    (PropertyField(data_type="array2D", primitive_data_type="CHAR"), None),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="INTEGER", property_field_enums=None), PropertyEdit.ValueType.INTEGER),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="REAL", property_field_enums=None), PropertyEdit.ValueType.REAL),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="INVALID", property_field_enums=None), None),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="BOOLEAN", property_field_enums=None), PropertyEdit.ValueType.BOOLEAN),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="double", property_field_enums=None), None),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="Double", property_field_enums=None), None),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="int", property_field_enums=None), None),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="Int", property_field_enums=None), None),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="UINT", property_field_enums=None), None),
    (mock.MagicMock(spec=PropertyField, data_type="scalar", primitive_data_type="STR", property_field_enums=None), None),
])
def test_get_type(ccda_field, expected_type):
    res = _get_type(ccda_field)
    assert res == expected_type


@pytest.mark.parametrize("field_type,ccda_field,expected_ud", [
    (PropertyEdit.ValueType.ENUM, PropertyField(), {_ENUM_OPTIONS_KEY: []}),
    (PropertyEdit.ValueType.ENUM, PropertyField(min_value=23), {_ENUM_OPTIONS_KEY: []}),
    (PropertyEdit.ValueType.ENUM, PropertyField(property_field_enums=[]), {_ENUM_OPTIONS_KEY: []}),
    (PropertyEdit.ValueType.ENUM, PropertyField(property_field_enums=[PropertyFieldEnum(enum_symbol="LABEL", value=23)]), {_ENUM_OPTIONS_KEY: [("LABEL", 23)]}),
    (PropertyEdit.ValueType.ENUM, PropertyField(property_field_enums=[PropertyFieldEnum(enum_symbol="ONE", value=1), PropertyFieldEnum(enum_symbol="TWO", value=2)]), {_ENUM_OPTIONS_KEY: [("ONE", 1), ("TWO", 2)]}),
    (PropertyEdit.ValueType.BOOLEAN, PropertyField(), None),
    (PropertyEdit.ValueType.BOOLEAN, PropertyField(property_field_enums=[]), None),
    (PropertyEdit.ValueType.BOOLEAN, PropertyField(property_field_enums=[], min_value=23), None),
    (PropertyEdit.ValueType.STRING, PropertyField(), None),
    (PropertyEdit.ValueType.STRING, PropertyField(property_field_enums=[]), None),
    (PropertyEdit.ValueType.STRING, PropertyField(property_field_enums=[], min_value=23), None),
    (PropertyEdit.ValueType.INTEGER, PropertyField(), None),
    (PropertyEdit.ValueType.INTEGER, PropertyField(property_field_enums=[]), None),
    (PropertyEdit.ValueType.INTEGER, PropertyField(unit_exponent=23), None),
    (PropertyEdit.ValueType.INTEGER, PropertyField(unit="W"), {_NUM_UNITS_KEY: "W"}),
    (PropertyEdit.ValueType.INTEGER, PropertyField(max_value=46, unit="W"), {_NUM_UNITS_KEY: "W", _NUM_MAX_KEY: 46}),
    (PropertyEdit.ValueType.INTEGER, PropertyField(min_value=23, max_value=46, unit="W"), {_NUM_MIN_KEY: 23, _NUM_MAX_KEY: 46, _NUM_UNITS_KEY: "W"}),
    (PropertyEdit.ValueType.INTEGER, PropertyField(min_value=23, unit="W"), {_NUM_MIN_KEY: 23, _NUM_UNITS_KEY: "W"}),
    (PropertyEdit.ValueType.INTEGER, PropertyField(max_value=46), {_NUM_MAX_KEY: 46}),
    (PropertyEdit.ValueType.INTEGER, PropertyField(min_value=23, max_value=46), {_NUM_MIN_KEY: 23, _NUM_MAX_KEY: 46}),
    (PropertyEdit.ValueType.INTEGER, PropertyField(min_value=23), {_NUM_MIN_KEY: 23}),
    (PropertyEdit.ValueType.REAL, PropertyField(), None),
    (PropertyEdit.ValueType.REAL, PropertyField(property_field_enums=[]), None),
    (PropertyEdit.ValueType.REAL, PropertyField(unit_exponent=23), None),
    (PropertyEdit.ValueType.REAL, PropertyField(unit="W"), {_NUM_UNITS_KEY: "W"}),
    (PropertyEdit.ValueType.REAL, PropertyField(max_value=46, unit="W"), {_NUM_UNITS_KEY: "W", _NUM_MAX_KEY: 46}),
    (PropertyEdit.ValueType.REAL, PropertyField(min_value=23, max_value=46, unit="W"), {_NUM_MIN_KEY: 23, _NUM_MAX_KEY: 46, _NUM_UNITS_KEY: "W"}),
    (PropertyEdit.ValueType.REAL, PropertyField(min_value=23, unit="W"), {_NUM_MIN_KEY: 23, _NUM_UNITS_KEY: "W"}),
    (PropertyEdit.ValueType.REAL, PropertyField(max_value=46), {_NUM_MAX_KEY: 46}),
    (PropertyEdit.ValueType.REAL, PropertyField(min_value=23, max_value=46), {_NUM_MIN_KEY: 23, _NUM_MAX_KEY: 46}),
    (PropertyEdit.ValueType.REAL, PropertyField(min_value=23), {_NUM_MIN_KEY: 23}),
])
def test_user_data_for_type(field_type, ccda_field, expected_ud):
    res = _user_data_for_type(field_type, ccda_field=ccda_field)
    assert res == expected_ud
