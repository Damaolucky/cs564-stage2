import csv
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from load_data import ROOT, EXPECTED_COUNTS, load_database
from run_queries import run_queries


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = self.folder / "test.db"

    def load(self):
        report = load_database(ROOT / "data", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        return report, con

    def query(self, con, number):
        return con.execute((ROOT / f"q{number}.sql").read_text()).fetchall()

    def test_load_counts_nulls_and_constraints(self):
        report, con = self.load()
        self.assertEqual(report["integrity_check"], "ok")
        self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        self.assertEqual(tables, set(EXPECTED_COUNTS))
        for table, count in EXPECTED_COUNTS.items():
            self.assertEqual(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], count)
        self.assertIsNone(con.execute("SELECT manager_id FROM employees WHERE employee_id=100").fetchone()[0])
        con.execute("PRAGMA foreign_keys=ON")
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("UPDATE employees SET manager_id=99999 WHERE employee_id=100")

    def test_actual_query_results(self):
        _, con = self.load()
        self.assertEqual({r[0] for r in self.query(con, 1)}, {
            "Administration Assistant", "Human Resources Representative", "Programmer",
            "Marketing Representative", "Purchasing Clerk", "Shipping Clerk", "Stock Clerk"})
        self.assertEqual(self.query(con, 2), [
            ("Shipping", 7), ("Finance", 6), ("Purchasing", 6), ("Sales", 6),
            ("IT", 5), ("Executive", 3), ("Accounting", 2), ("Marketing", 2),
            ("Administration", 1), ("Human Resources", 1), ("Public Relations", 1)])
        expected = {"Accounting": 12500, "Executive": 100000 / 3,
                    "Finance": 61000 / 6, "Human Resources": 9000,
                    "IT": 10000, "Marketing": 12000,
                    "Public Relations": 10500, "Sales": 88000 / 6}
        actual = dict(self.query(con, 3))
        self.assertEqual(set(actual), set(expected))
        for name, value in expected.items():
            self.assertAlmostEqual(actual[name], value)

    def test_query_boundaries_duplicates_and_employee_weighting(self):
        con = sqlite3.connect(":memory:")
        self.addCleanup(con.close)
        con.executescript("""
            CREATE TABLE jobs (job_id INTEGER, job_title TEXT, min_salary REAL, max_salary REAL);
            CREATE TABLE departments (department_id INTEGER, department_name TEXT);
            CREATE TABLE employees (employee_id INTEGER, department_id INTEGER, job_id INTEGER);
            INSERT INTO jobs VALUES (1,'Boundary',4000,5000),(2,'Boundary',4000,5000),
                (3,'Too high minimum',4001,9000),(4,'Too low maximum',4000,4999),
                (5,'High',9000,20000),(6,'Threshold',5000,8000);
            INSERT INTO departments VALUES (1,'Weighted'),(2,'Threshold'),(3,'Empty');
            INSERT INTO employees VALUES (1,1,1),(2,1,1),(3,1,5),(4,2,6);
        """)
        self.assertEqual(self.query(con, 1), [("Boundary",)])
        self.assertEqual(self.query(con, 2), [("Weighted",3),("Threshold",1),("Empty",0)])
        self.assertEqual(self.query(con, 3), [("Weighted",10000.0)])

    def test_existing_database_is_preserved(self):
        self.db.write_bytes(b"existing file")
        with self.assertRaises(FileExistsError):
            load_database(ROOT / "data", self.db)
        self.assertEqual(self.db.read_bytes(), b"existing file")

    def test_invalid_input_never_publishes_database(self):
        data = self.folder / "data"
        shutil.copytree(ROOT / "data", data)
        path = data / "employees.csv"
        original = path.read_text()
        for changed in [original.replace("24000,,9", "24000,99999,9"),
                        original.replace("employee_id,", "wrong_header,", 1),
                        original[:original.rfind("206,William")]]:
            with self.subTest(change=changed[-40:]):
                path.write_text(changed)
                with self.assertRaises((ValueError, sqlite3.IntegrityError)):
                    load_database(data, self.db)
                self.assertFalse(self.db.exists())

    def test_manager_can_appear_later_in_csv(self):
        data = self.folder / "data"
        shutil.copytree(ROOT / "data", data)
        path = data / "employees.csv"
        lines = path.read_text().splitlines()
        path.write_text("\n".join([lines[0]] + list(reversed(lines[1:]))) + "\n")
        self.assertEqual(load_database(data, self.db)["foreign_key_violations"], [])

    def test_query_exports(self):
        self.load()
        result_dir = self.folder / "results"
        run_queries(self.db, result_dir)
        for number, count in [(1,7),(2,11),(3,8)]:
            with (result_dir / f"q{number}.csv").open(newline="") as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(len(rows), count + 1)


if __name__ == "__main__":
    unittest.main()
