"""Read flight CSV files and collect valid flights and errors."""

import csv
import os
from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Return valid records and errors from the files in the given order."""
    records = []
    errors = []
    seen = set()

    for path in paths:
        with open(path, encoding="utf-8", newline="") as file:
            for line_number, line in enumerate(file, start=1):
                if line_number == 1:  # skip the header
                    continue

                if not line.strip() or line.lstrip().startswith("#"):
                    continue

                try:
                    fields = next(csv.reader([line], strict=True))
                    error = validate_row(fields, airports)
                except csv.Error:
                    fields = []
                    error = "WRONG_FIELD_COUNT"

                if error is None:
                    record = to_record(fields)
                    key = (record["flight_id"], record["departure_datetime"])
                    if key in seen:
                        error = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(key)
                        records.append(record)

                if error is not None:
                    filename = os.path.basename(path)
                    message = f"{filename}:{line_number}: {error} | {line.rstrip()}"
                    errors.append(message)

    return records, errors
