from unittest import mock
from accwidgets.lsa_selector import LsaSelectorModel
from accwidgets.lsa_selector._model import sample_contexts_for_accelerator, sorted_row_models


class SampleLsaSelectorModel(LsaSelectorModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, lsa=mock.MagicMock(), **kwargs)

    def simulate_error(self, message: str):
        self._last_error = message
        self.lsa_error_received.emit(message)

    @property
    def _row_models(self):
        if self._rows is None:
            self._rows = sorted_row_models(sample_contexts_for_accelerator(accelerator=self._acc,
                                                                           categories=self._fetch_categories,
                                                                           resident_only=self._fetch_resident_only))
        return self._rows
