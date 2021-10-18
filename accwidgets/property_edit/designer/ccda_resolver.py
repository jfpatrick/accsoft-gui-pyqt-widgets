import operator
from typing import List, Tuple, Optional, Dict, Any, Set
from asyncio import Future
try:
    from asyncio import create_task
except ImportError:
    from asyncio import ensure_future as create_task  # type: ignore
from accwidgets.parameter_selector._name import ParameterName
from accwidgets.property_edit import PropertyEditField, PropertyEdit
from accwidgets.property_edit.propedit import _ENUM_OPTIONS_KEY, _NUM_MAX_KEY, _NUM_MIN_KEY, _NUM_UNITS_KEY
from pyccda import AsyncAPI as CCDA
from pyccda.models import PropertyField


def resolve_from_param(param_name: str) -> Future:
    return create_task(_resolve_from_param(param_name))


async def _resolve_from_param(param_name: str) -> Tuple[List[PropertyEditField], Set[str]]:
    param = ParameterName.from_string(param_name)
    if not param:
        raise ValueError(f'Invalid parameter name "{param_name}"')
    dev = await CCDA().Device.find(name=param.device)
    dc = await dev.device_class()
    try:
        prop = next(iter(p for p in dc.device_class_properties if p.name == param.prop))
    except StopIteration:
        raise ValueError(f'Device "{param.device}" does not have a property "{param.prop}"')
    return _map_fields_sorted(prop.data_fields)


def _map_fields_sorted(ccda_fields: List[PropertyField]) -> Tuple[List[PropertyEditField], Set[str]]:
    fields = sorted(ccda_fields, key=operator.attrgetter("name"))
    skipped_items: Set[str] = set()
    mapped_res: List[PropertyEditField] = []
    for ccda_field in fields:
        field_type = _get_type(ccda_field)
        if field_type is None:
            skipped_items.add(ccda_field.name)
            continue
        ud = _user_data_for_type(field_type, ccda_field=ccda_field)
        mapped = PropertyEditField(field=ccda_field.name,
                                   type=field_type,
                                   editable=False,
                                   user_data=ud)
        mapped_res.append(mapped)
    return mapped_res, skipped_items


def _get_type(ccda_field: PropertyEdit) -> Optional[PropertyEdit.ValueType]:
    if ccda_field.data_type == "bit_enum":
        return PropertyEdit.ValueType.ENUM
    elif ccda_field.data_type == "scalar":
        val_type_key = _DATA_TYPE_MAP.get(ccda_field.primitive_data_type, ccda_field.primitive_data_type)
        try:
            return PropertyEdit.ValueType[val_type_key]
        except KeyError:
            pass
    return None


def _user_data_for_type(field_type: PropertyEdit.ValueType, ccda_field: PropertyField) -> Optional[Dict[str, Any]]:
    if field_type == PropertyEdit.ValueType.ENUM:
        options = sorted(((o.enum_symbol, o.value) for o in ccda_field.property_field_enums),
                         key=operator.itemgetter(1)) if ccda_field.property_field_enums else []
        return {
            _ENUM_OPTIONS_KEY: options,
        }
    ud: Optional[Dict[str, Any]] = None
    if field_type in (PropertyEdit.ValueType.REAL, PropertyEdit.ValueType.INTEGER):
        if ccda_field.unit is not None:
            ud = {}
            ud[_NUM_UNITS_KEY] = ccda_field.unit
        # TODO: CCDA returns unit_exponent, but no widgets have extra config beyond "unit". Should we add it?
        if ccda_field.min_value is not None:
            ud = ud or {}
            ud[_NUM_MIN_KEY] = ccda_field.min_value
        if ccda_field.max_value is not None:
            ud = ud or {}
            ud[_NUM_MAX_KEY] = ccda_field.max_value
    return ud


_DATA_TYPE_MAP = {
    "BOOL": "BOOLEAN",
    "INT": "INTEGER",
    "LONG": "INTEGER",
    "SHORT": "INTEGER",
    "BYTE": "INTEGER",
    "FLOAT": "REAL",
    "DOUBLE": "REAL",
    "CHAR": "STRING",
}
