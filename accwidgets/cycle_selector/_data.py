from dataclasses import dataclass


@dataclass(frozen=True)
class CycleSelectorValue:
    """Value that represents a cycle selector (sometimes called "timing user")."""

    domain: str
    """Machine domain that the selector belongs to."""

    group: str
    """
    Group. Most often this is set to USER for timing users (destinations). But sometimes it can
    have other signatures, such as PARTY for particle types.
    """

    line: str
    """
    Leaf of the selector identifies the item inside the group. E.g. for USER group this can be a concrete destination
    or ALL for all available users, while for particle types this can be a name of the particle, such as ION.
    """

    def __str__(self) -> str:
        return ".".join((self.domain, self.group, self.line))
