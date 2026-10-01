def apply_sqlite_migrations(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES(1)")
    conn.commit()
