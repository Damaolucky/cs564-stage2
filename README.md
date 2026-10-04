# CS564 Project Stage 2 — Data Loading and Queries 1–3

Local SQLite implementation of data loading and the first three queries only.
The seven course CSV files must be placed in `data/`. They are retained locally and
excluded from this public repository. No third-party Python packages are needed.

## Run locally

Download and extract CS564_stage2.zip from the course materials. Copy countries.csv,
departments.csv, dependents.csv, employees.csv, jobs.csv, locations.csv, and regions.csv
into `data/`. On the original local project, these files are already in place.
With Python 3 installed, run from this directory:

```sh
python load_data.py
python run_queries.py
python -m unittest discover -s tests -v
```

The loader creates `cs564_stage2.db`, verifies all seven row counts, checks foreign keys
and database integrity, and prints a JSON verification report. It skips CSV headers
and converts empty nullable fields (including the top-level manager) to SQL NULL.
Employee self-references are checked after all employees are loaded.
It refuses to overwrite an existing database. For another run, choose a new path:

```sh
python load_data.py --db another_run.db
python run_queries.py --db another_run.db
```

Custom input: `python load_data.py --data-dir /path/to/CS564_stage2 --db new.db`.
Expected dataset counts: regions 4, countries 25, locations 7, departments 11,
jobs 19, employees 40, dependents 30.

## Files and query meaning

- `schema.sql`: all seven table definitions from the assignment.
- `load_data.py`: validated import using Python's built-in SQLite library.
- `q1.sql`: distinct job titles with max_salary >= 5000 and min_salary <= 4000.
- `q2.sql`: every department and its employee count, descending by count.
  A LEFT JOIN includes empty departments, and COUNT(employee_id) returns zero for them.
  Alphabetical ordering breaks ties.
- `q3.sql`: average of each employee's job max_salary, grouped by department,
  retaining averages strictly greater than 8000. Repeated jobs count once per employee;
  this is neither actual salary nor an average over distinct jobs.
- `run_queries.py`: runs the three SQL files read-only and exports `results/q1.csv`–`q3.csv`.
- `results/verification.json`: recorded checks for the supplied dataset.

Each q*.sql file contains only its query, ready to copy into the group's submission.
Queries 4–14 and group member information are outside this project's scope.

If the SQLite command-line client is installed, open the generated database with
`sqlite3 cs564_stage2.db`, then use `.tables`, `.schema`, or `.read q1.sql`.

## Source-data fidelity

CSV files are copied unchanged from the supplied course dataset. The schema keeps
`locations.country_id INTEGER` exactly as provided in the assignment; SQLite stores
the supplied alphabetic country codes as text under its normal type-affinity rules.
The supplied locations.csv row 2500 has unusual address/postal/city field placement;
its fields are imported as supplied, without guessing corrections. It does not affect
queries 1–3. Empty nullable fields are normalized to SQL NULL for referential integrity.
The generated database is local and ignored by Git; recreate it with the loader.
