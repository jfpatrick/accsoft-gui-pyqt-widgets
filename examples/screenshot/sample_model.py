from pylogbook import NamedServer
from accwidgets.screenshot import LogbookModel, ScreenshotAction


class SampleLogbookModel(LogbookModel):

    def __init__(self):
        super().__init__(server_url=NamedServer.TEST, activities="LOGBOOK_TESTS_Long_Name Testing")


class SampleScreenshotAction(ScreenshotAction):

    def __init__(self):
        super().__init__(model=SampleLogbookModel())
