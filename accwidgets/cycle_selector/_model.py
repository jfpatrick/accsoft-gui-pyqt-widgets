import pyccda
import functools
from asyncio import CancelledError
from collections import defaultdict
from typing import Optional, List, Mapping, DefaultDict, cast
from qtpy.QtCore import QObject


class CycleSelectorConnectionError(Exception):
    """
    Error raised when querying CCDB fails.
    """
    pass


class CycleSelectorModel(QObject):

    def __init__(self, ccda: Optional[pyccda.AsyncAPI] = None, parent: Optional[QObject] = None):
        """
        Model handles the communication with CCDB in order to retrieve available selectors.

        Args:
            ccda: Custom :mod:`pyccda` instance to fetch data from CCDB.
            parent: Owning object.
        """
        super().__init__(parent)
        self._ccda = ccda or pyccda.AsyncAPI()

    async def fetch(self) -> Mapping[str, Mapping[str, List[str]]]:
        """
        This method fetches data from CCDB and formats it in a tree that is
        decoupled from the data model of :mod:`pyccda`.

        Returns:
            Tree of depth 3, with domain -> group -> line structure.
        """
        try:
            pagination = await self._ccda.SelectorDomain.search()
        except CancelledError:
            raise
        except Exception as e:  # noqa: B902
            # TODO: When PyCCDA fixes its exception to abstract it away from urllib3 implementation, we should catch it instead of general one
            raise CycleSelectorConnectionError(e) from e

        domains = [d async for d in pagination]
        dict_data = cast(DefaultDict[str, DefaultDict[str, List[str]]], defaultdict(functools.partial(defaultdict, dict)))
        for domain in domains:
            for group in domain.selector_groups:
                dict_data[domain.name][group.name] = [line.name for line in group.selector_values]
        return dict_data
