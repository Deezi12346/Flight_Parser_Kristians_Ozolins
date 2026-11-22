"""Flight schedule parser and query tool.

Examples:
    python flight_parser.py -i data/db.csv -a data/airports.txt
    python flight_parser.py -d data/flights -a data/airports.txt
    python flight_parser.py -j db.json -q data/query.json
"""

import argparse
from datetime import datetime
import json
import logging
import os
import sys

from validator import load_airports
from csv_loader import parse_files
from query import run_queries

STUDENT_ID = "251RDC075"
FIRST_NAME = "Kristians"
LAST_NAME = "Ozolins"


def invalid_json_constant(value):
    """Reject NaN and Infinity, which are not valid JSON values."""
    raise ValueError(f"Invalid JSON value: {value}")


def main(argv: list[str] | None = None) -> int:
    """Read the arguments, process the files, and return an exit code."""
    parser = argparse.ArgumentParser(description="Flight schedule query tool")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="Input CSV file")
    source.add_argument("-d", metavar="FOLDER", help="Folder containing CSV files")
    source.add_argument("-j", metavar="FILE", help="Existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="Airport list")
    parser.add_argument("-o", metavar="FILE", help="Output JSON database", default=None)
    parser.add_argument("-q", metavar="FILE", help="JSON query file")
    parser.add_argument("-r", metavar="FOLDER", help="Response folder", default=".")

    # Return 2 for wrong command-line arguments, like argparse normally does.
    try:
        args = parser.parse_args(argv)
        if (args.i or args.d) and args.a is None:
            parser.error("-a is required with -i and -d")
        if args.j and args.o is not None:
            parser.error("-o cannot be used with -j")
    except SystemExit as error:
        return error.code

    logger = logging.getLogger("flight_parser")
    handler = None
    try:
        if args.j:
            with open(args.j, encoding="utf-8") as file:
                db = json.load(file, parse_constant=invalid_json_constant)
            if not isinstance(db, list) or not all(isinstance(row, dict) for row in db):
                raise ValueError("JSON database must be a list of objects")
        else:
            airports = load_airports(args.a)
            if args.i:
                paths = [args.i]
            else:
                names = sorted(os.listdir(args.d))
                paths = [os.path.join(args.d, name) for name in names
                         if name.endswith(".csv") and os.path.isfile(os.path.join(args.d, name))]
                if not paths:
                    raise ValueError("No CSV files in the input folder")

            db, errors = parse_files(paths, airports)
            db_path = args.o if args.o is not None else "db.json"
            log_path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "errors.log")

            # Write errors.log through logging, not through file.write().
            logger.setLevel(logging.INFO)
            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(handler)
            for message in errors:
                logger.warning(message)

            with open(db_path, "w", encoding="utf-8") as file:
                json.dump(db, file, indent=2)

        if args.q:
            with open(args.q, encoding="utf-8") as file:
                queries = json.load(file, parse_constant=invalid_json_constant)
            if not isinstance(queries, (dict, list)) or (isinstance(queries, list) and
                                                         not all(isinstance(q, dict) for q in queries)):
                raise ValueError("Query file must contain an object or a list of objects")

            responses = run_queries(db, queries)
            date = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{date}.json"
            path = os.path.join(args.r, filename)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(responses, file, indent=2)

        return 0
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
