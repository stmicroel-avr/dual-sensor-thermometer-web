from fastapi import FastAPI

async def create_db(app: FastAPI) -> None:
    """
    Creates the database tables
    :param app: FastAPI app
    :return: None
    """
    # Metrics table
    await app.state.db.execute("""
CREATE TABLE IF NOT EXISTS metrics (
   id INTEGER PRIMARY KEY,
   sensor_id TEXT NOT NULL,
   value REAL,
   created_at INTEGER DEFAULT (strftime('%s','now'))
);""")
    await app.state.db.execute("CREATE INDEX IF NOT EXISTS idx_metrics ON metrics(created_at, sensor_id);")
    await app.state.db.commit()

    # Minute metrics table
    await app.state.db.execute("""
    CREATE TABLE IF NOT EXISTS minute_metrics (
        id INTEGER PRIMARY KEY,
        sensor_id TEXT NOT NULL,
        value REAL,
        created_at INTEGER
);""")
    await app.state.db.execute("CREATE INDEX IF NOT EXISTS idx_minute_metrics ON minute_metrics(created_at, sensor_id);")
    await app.state.db.commit()

    # Hour metrics table
    await app.state.db.execute("""
    CREATE TABLE IF NOT EXISTS hour_metrics (
        id INTEGER PRIMARY KEY,
        sensor_id TEXT NOT NULL,
        value REAL,
        created_at INTEGER
    );""")
    await app.state.db.execute("CREATE INDEX IF NOT EXISTS idx_hour_metrics ON hour_metrics(created_at, sensor_id);")
    await app.state.db.commit()