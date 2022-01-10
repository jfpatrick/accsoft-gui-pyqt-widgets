import operator
from ._model import LogbookModel


def make_activities_summary(model: LogbookModel) -> str:
    return "/".join(map(operator.attrgetter("name"), model.logbook_activities))
