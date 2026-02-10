from datetime import datetime, timedelta
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

async def fetch_last_metrics(app: FastAPI, seconds: int) -> list:
    """
    Get last metrics(for page reload)
    :param app: FastAPI
    :param seconds: Period in seconds
    :return:
    """
    items = []
    pool = app.state.db_pool
    async with pool.acquire() as conn:
        to = datetime.now()
        at = to - timedelta(seconds=seconds)
        records = await conn.fetch(f"select * from metrics where created_at between '{at}' and '{to}'")
        for record in records:
            items.append({
                'ts': int(record['created_at'].timestamp() * 1000),
                'name': record['sensor_id'],
                'value': record['value'],
            })

    return items