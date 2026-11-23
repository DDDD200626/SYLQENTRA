# Tests

Automated tests for Phase 02 through Phase 04 live in `backend/tests`.

From the repository root:

```powershell
.\.venv\Scripts\python -m pytest
```

The test suite uses an in-memory SQLite database so it can run before Docker is installed. PostgreSQL remains the database used by the application and by Alembic.
