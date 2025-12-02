## Backend quickstart

1. Create the database and load schema/data:
   ```sh
   createdb fitness_club
   psql fitness_club -f ../SQL/DDL.sql
   psql fitness_club -f ../SQL/DML.sql
   ```
2. Install deps (Python 3.12+):
   ```sh
   pip install -e .
   ```
3. Run the API:
   ```sh
   python app.py
   ```

The Flask API now uses SQLAlchemy ORM models (`models.py`) for all endpoints and serves member, trainer, and admin flows. CORS is enabled for localhost:5173 and localhost:3000. Key endpoints: member registration/profile/goals/metrics/classes/PT sessions/billing, trainer availability/schedule, and admin room/class/equipment/maintenance/billing management.

### Authentication
- HTTP Basic Auth is required on all endpoints except `/members/register`. Use `Authorization: Basic <base64(username:password)>`.
- Default admin credentials: `admin` / `admin` (configurable via env).
- Seeded demo users: members `alice|bob|carol` with password `password`; trainers `tom|lisa|mark` with password `password`.
- Member registration payloads must include `username` and `password` along with profile fields.
- If you already had a database, drop/recreate (or run `python main.py`) to pick up the new auth columns.
