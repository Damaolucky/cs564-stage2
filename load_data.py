"""Load the seven course CSV files into a new, validated SQLite database."""
import argparse
import csv
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
EXPECTED_COUNTS = {
    "regions": 4, "countries": 25, "locations": 7, "departments": 11,
    "jobs": 19, "employees": 40, "dependents": 30,
}


def load_database(data_dir, db_path):
    data_dir, db_path = Path(data_dir), Path(db_path)
    if db_path.exists():
        raise FileExistsError(f"Refusing to overwrite {db_path}; choose a new --db path.")
    # Build in memory first: invalid input never leaves a partial database.
    con = sqlite3.connect(":memory:")
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        with con:
            # Employees can refer to managers later in the same CSV.
            con.execute("BEGIN")
            con.execute("PRAGMA defer_foreign_keys = ON")
            for table, expected in EXPECTED_COUNTS.items():
                columns = con.execute(f"PRAGMA table_info({table})").fetchall()
                with (data_dir / f"{table}.csv").open(newline="", encoding="utf-8-sig") as stream:
                    reader = csv.reader(stream)
                    header = next(reader, None)
                    if header != [c[1] for c in columns]:
                        raise ValueError(f"{table}: unexpected CSV header: {header!r}")
                    for line, row in enumerate(reader, start=2):
                        if len(row) != len(columns):
                            raise ValueError(f"{table}.csv:{line}: wrong number of columns")
                        values = []
                        for value, column in zip(row, columns):
                            if value == "":
                                if column[3] or column[5]:
                                    raise ValueError(f"{table}.csv:{line}: missing {column[1]}")
                                value = None
                            elif column[2].upper() == "INTEGER" and column[1] != "country_id":
                                value = int(value)
                            elif column[2].upper() == "DOUBLE":
                                value = float(value)
                            values.append(value)
                        placeholders = ",".join("?" for _ in columns)
                        con.execute(f"INSERT INTO {table} VALUES ({placeholders})", values)
                count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if count != expected:
                    raise ValueError(f"{table}: expected {expected} rows, got {count}")
            violations = con.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise ValueError(f"Foreign key violations: {violations}")
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"Integrity check failed: {integrity}")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also prevents accidentally replacing an existing file.
        with db_path.open("xb"):
            pass
        try:
            target = sqlite3.connect(db_path)
            try:
                con.backup(target)
            finally:
                target.close()
        except Exception:
            db_path.unlink()
            raise
        return {"row_counts": dict(EXPECTED_COUNTS), "integrity_check": integrity,
                "foreign_key_violations": violations, "sqlite_version": sqlite3.sqlite_version}
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--db", type=Path, default=ROOT / "cs564_stage2.db")
    args = parser.parse_args()
    report = load_database(args.data_dir, args.db)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
