from fastapi import FastAPI

async def create_db(app: FastAPI) -> None:
    pool = app.state.db_pool

    async with pool.acquire() as conn:
        # metrics
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id SERIAL PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            value REAL,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        );
        """)

        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics
        ON metrics (created_at, sensor_id);
        """)

        # minute_metrics
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS minute_metrics (
            id SERIAL PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            value REAL,
            created_at TIMESTAMP NOT NULL
        );
        """)

        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_minute_metrics
        ON minute_metrics (created_at, sensor_id);
        """)

        # hour_metrics
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS hour_metrics (
            id SERIAL PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            value REAL,
            created_at TIMESTAMP NOT NULL
        );
        """)

        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hour_metrics
        ON hour_metrics (created_at, sensor_id);
        """)
