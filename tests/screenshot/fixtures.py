import pytest
from unittest import mock
from pylogbook import ActivitiesClient, Client, NamedServer
from accwidgets.screenshot import LogbookModel


@pytest.fixture(scope="function")
def logbook():
    client = mock.MagicMock(spec=Client)
    client.server_url = NamedServer.PRO
    client.rbac_b64_token = ""
    activities_client = mock.MagicMock(spec=ActivitiesClient)
    activities_client.activities = ()
    return client, activities_client


@pytest.fixture(scope="function")
def logbook_model():
    model = mock.MagicMock(spec=LogbookModel)
    return model
