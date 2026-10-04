import argparse
import csv
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent


def run_queries(db_path, results_dir):
    db_path, results_dir = Path(db_path), Path(results_dir)
    con = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        for number in range(1, 4):
            cursor = con.execute((ROOT / f"q{number}.sql").read_text(encoding="utf-8"))
            header = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            with (results_dir / f"q{number}.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerows(rows)
            print(f"Query {number}: {len(rows)} rows")
            print(" | ".join(header))
            for row in rows:
                print(" | ".join(map(str, row)))
            print()
    finally:
        con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run q1-q3 against an existing database and export CSV results.")
    parser.add_argument("--db", type=Path, default=ROOT / "cs564_stage2.db")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    run_queries(args.db, args.results_dir)
