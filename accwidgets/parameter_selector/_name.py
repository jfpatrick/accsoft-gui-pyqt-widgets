import re
from dataclasses import dataclass, field as dataclass_field
from typing import Optional


@dataclass
class ParameterName:
    """Control system parameter name, most often represented by device-property pair and optionally field."""

    device: str
    """Name of the device recognized by the directory service."""

    prop: str
    """Name of the property in the given device."""

    field: Optional[str] = None
    """Optional field name, if referring to only one field, as opposed to the full property."""

    protocol: Optional[str] = None
    """Optional protocol, e.g. rda3"""

    service: Optional[str] = None
    """Service is the control node that resolves the device names, if the main directory service is unaware of it."""

    _protocol: Optional[str] = dataclass_field(init=False, repr=False)

    def __post_init__(self):
        # If not do it, dataclass generates protocol with the default value of the latest one assigned in this class,
        # which happens to be an unbound property, defined below after getter and setter.
        if isinstance(self._protocol, property):
            self._protocol = None

    @property  # type: ignore  # already defined deliberately for dataclass generation
    def protocol(self) -> Optional[str]:
        return self._protocol

    @protocol.setter
    def protocol(self, new_val: Optional[str]):
        if new_val is None:
            self.service = None
        self._protocol = new_val

    @property
    def valid(self) -> bool:
        """Name is complete and can be successfully resolved."""
        return (len(self.device) > 0 and len(self.prop) > 0 and (
                (self.protocol is None and self.service is None)
                or self.protocol is not None))

    @classmethod
    def from_string(cls, value: str) -> Optional["ParameterName"]:
        """
        Factory method to construct an object from string representation.

        Args:
            value: String formatted according to the device-property specification.

        Returns:
            New object or :obj:`None` if could not parse the string.
        """
        mo = re.match(NOTATION_REGEX, value)
        if mo and mo.groups():
            captures = mo.groupdict()
            return cls(**captures)
        else:
            return None

    def __str__(self):
        res = ""
        if not self.valid:
            return res

        if self.protocol:
            res += self.protocol
            res += "://"

            if self.service and self.service != self.protocol:
                res += self.service
            res += "/"
        res += self.device
        res += "/"
        res += self.prop
        if self.field:
            res += "#"
            res += self.field
        return res


NOTATION_REGEX = r"^((?P<protocol>[^:/]+)://(?P<service>[^/]+)?/)?(?P<device>[^/#\n\t]+)/" \
                 r"(?P<prop>[^/#\n\t]+)(#(?P<field>[^\n\t]+))?$"
