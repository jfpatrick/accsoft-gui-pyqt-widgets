import asyncio
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Union, Tuple, List, Callable, TYPE_CHECKING
from datetime import datetime, timedelta
from qtpy.QtCore import Signal, QObject
from pyrbac import Token
from pylogbook import Client, ActivitiesClient, NamedServer
from pylogbook.models import Activity, ActivitiesType, Event


if TYPE_CHECKING:
    FutureType = Future
else:
    FutureType = Union


class LogbookModel(QObject):

    rbac_token_changed = Signal()
    """Notifies when the RBAC token has been changed."""

    activities_changed = Signal()
    """Notifies when the e-logbook activities have been changed."""

    activities_failed = Signal(str)
    """Notifies when the e-logbook activities setting has failed. The argument is the error message."""

    def __init__(self,
                 server_url: Union[str, NamedServer, None] = None,
                 rbac_token: Optional[Token] = None,
                 activities: Optional[ActivitiesType] = None,
                 logbook: Optional[Tuple[Client, ActivitiesClient]] = None,
                 parent: Optional[QObject] = None):
        """
        Model manages the connections to :mod:`pylogbook` and keeps track of corresponding RBAC tokens.

        Args:
            server_url: e-logbook server URL. This argument is mutually exclusive with ``logbook``. In the later case,
                        given clients must be set up with the proper server URL.
            rbac_token: Pre-existing RBAC token if user has already been authorized. This argument is mutually
                        exclusive with ``logbook``. In the later case, given clients must be set up with the proper
                        RBAC token.
            activities: Logbook activities to log into. Empty activities will prevent the model from
                        issuing requests. It can be later changed via :attr:`logbook_activities` property.
            logbook: Tuple of client library objects that will be used to communicate with the server. If :obj:`None`
                     is given, new clients will be instantiated. This argument is mutually exclusive with both
                     ``server_url`` and ``rbac_token``.
            parent: Owning object.
        """
        super().__init__(parent)
        self._activities_cache = activities
        self._last_activity_error: Optional[str] = None
        self._client: Client
        self._activities_client: ActivitiesClient
        if logbook is not None:
            if server_url is not None or rbac_token is not None:
                raise ValueError('"logbook" argument is mutually exclusive with "server_url" or "rbac_token"')
            self._client, self._activities_client = logbook
        else:
            if server_url is None:
                server_url = NamedServer.PRO
            self._client = Client(server_url=server_url, rbac_token=normalize_token(rbac_token))
            # Initial activities must be empty. If given, and RBAC token is not valid, it produces LogbookError immediately
            self._activities_client = ActivitiesClient(client=self._client, activities=[])
        # if given RBAC token is already valid, populate activities into the activities_client
        self._flush_activities_cache(emit_signal=False)
        self._thread_pool = ThreadPoolExecutor(max_workers=1)

    def reset_rbac_token(self, token: Optional[Token] = None):
        """
        Set or delete the existing RBAC token.

        Args:
            token: RBAC token or :obj:`None` if it should be removed.
        """
        new_token = normalize_token(token)
        if new_token != self._client.rbac_b64_token:
            self._client.rbac_b64_token = new_token
            self.rbac_token_changed.emit()
            self._flush_activities_cache()

    def _get_logbook_activities(self) -> Tuple[Activity, ...]:
        return self._activities_client.activities

    def _set_logbook_activities(self, new_val: ActivitiesType):
        self._activities_cache = [] if new_val is None else new_val
        # Activities cannot always be applied immediately,
        # then need a valid RBAC token before propagating into the client,
        # otherwise a LogbookError is produced.
        self._flush_activities_cache()

    logbook_activities = property(fget=_get_logbook_activities, fset=_set_logbook_activities)
    """Current e-logbook activities."""

    async def create_logbook_event(self, message: str) -> FutureType[Event]:
        """
        Create a new e-logbook event with the given message.

        Args:
            message: Message for the event.

        Returns:
            Newly created event.

        Raises:
            ~pylogbook.exceptions.LogbookError: If there was a problem creating the event.
        """
        return await self._dispatch_runnable(self._activities_client.add_event, message)

    async def get_logbook_event(self, event_id: int) -> FutureType[Event]:
        """
        Retrieve an existing e-logbook event. This is alternative to :meth:`create_logbook_event`.

        Args:
            event_id: ID of the e-logbook event.

        Returns:
            Retrieved event.

        Raises:
            ~pylogbook.exceptions.LogbookError: If there was a problem retrieving the event.
        """
        return await self._dispatch_runnable(self._client.get_event, event_id)

    async def attach_screenshot(self, event: Event, screenshot: bytes, seq: int):
        """
        Attach a screenshot to an existing e-logbook event.

        Args:
            event: E-logbook event object.
            screenshot: Bytes encoded in \\*.png format to attach to the event.
            seq: Sequence number useful when multiple sources are being screenshotted.

        Raises:
            ~pylogbook.exceptions.LogbookError: If there was a problem interacting with e-logbook.
        """
        await self._dispatch_runnable(event.attach_content,
                                      screenshot,
                                      "image/png",
                                      f"capture_{seq}.png")

    async def get_logbook_events(self, past_days: int, max_events: int) -> FutureType[List[Event]]:
        """
        Retrieve existing e-logbook event in the given range.

        Args:
            past_days: Number of days up till now to collect events for.
            max_events: Upper limit of how many events to return.

        Returns:
            Array of retrieved event objects.

        Raises:
            ~pylogbook.exceptions.LogbookError: If there was a problem retrieving the events.
        """
        activities_client = self._activities_client

        def fn():
            start = datetime.now() - timedelta(days=past_days)
            # Specifying a `from_date` improves performance
            events_pages = activities_client.get_events(from_date=start)
            events_pages.page_size = max_events
            return list(events_pages.get_page(0))

        return await self._dispatch_runnable(fn)

    def validate(self):
        """
        Validate the model to check if it can communicate with e-logbook.

        Raises:
            ValueError: If communication is not possible. Error message will be the reason for validation failure.
        """
        if self._last_activity_error:
            raise ValueError(self._last_activity_error)
        if not self._rbac_token_valid:
            raise ValueError("RBAC login is required to write to the e-logbook")
        if not self.logbook_activities:
            raise ValueError("No e-logbook activity is defined")

    def __del__(self):
        self._thread_pool.shutdown()

    def _flush_activities_cache(self, emit_signal: bool = True):
        if not self._rbac_token_valid or self._activities_cache is None:
            return
        prev_activities = self._activities_client.activities
        try:
            self._activities_client.activities = self._activities_cache
        except ValueError as e:
            error = str(e)
            self._last_activity_error = error
            self.activities_failed.emit(error)
        else:
            self._last_activity_error = None
            if emit_signal and prev_activities != self._activities_cache:
                self.activities_changed.emit()
            self._activities_cache = None

    @property
    def _rbac_token_valid(self) -> bool:
        return len(self._client.rbac_b64_token) > 0

    async def _dispatch_runnable(self, fn: Callable, *args) -> Future:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._thread_pool, fn, *args)


def normalize_token(token: Optional[Token]) -> Union[str, Token]:
    return "" if token is None else token
