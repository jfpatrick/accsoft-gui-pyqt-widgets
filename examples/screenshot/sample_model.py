from pylogbook import NamedServer
from accwidgets.screenshot import LogbookModel


class SampleLogbookModel(LogbookModel):

    def __init__(self):
        super().__init__(server_url=NamedServer.TEST, activities="LOGBOOK_TESTS_Long_Name Testing")
