"""JSON persistence with one lock shared by response and score writes."""

import json
import os
import threading
from pathlib import Path

_RESPONSE_READ_ERRORS = (json.JSONDecodeError, OSError)
# Preserve the original score loader's broader fallback until a separate change.
_SCORE_READ_ERRORS = (Exception,)


class JsonStore:
    def __init__(self, data_dir: Path):
        self.responses_path = data_dir / "responses.json"
        self.scores_path = data_dir / "scores.json"
        self._lock = threading.Lock()

    @staticmethod
    def _load(path: Path, read_errors: tuple) -> list:
        if not os.path.exists(path):
            return []
        try:
            with open(path, encoding="utf-8") as file:
                return json.load(file)
        except read_errors:
            return []

    def load_responses(self) -> list:
        return self._load(self.responses_path, _RESPONSE_READ_ERRORS)

    def load_scores(self) -> list:
        return self._load(self.scores_path, _SCORE_READ_ERRORS)

    def _append(self, path: Path, row: dict, read_errors: tuple) -> list:
        with self._lock:
            rows = self._load(path, read_errors)
            rows.append(row)
            temporary = str(path) + ".tmp"
            with open(temporary, "w", encoding="utf-8") as file:
                json.dump(rows, file, ensure_ascii=False)
            os.replace(temporary, path)
        return rows

    def append_response(self, row: dict) -> list:
        return self._append(self.responses_path, row, _RESPONSE_READ_ERRORS)

    def append_score(self, row: dict) -> list:
        return self._append(self.scores_path, row, _SCORE_READ_ERRORS)
