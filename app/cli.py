import asyncio
import statistics
from argparse import ArgumentParser
from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List, Tuple

import asyncpg


RowT = Tuple[int, str, float, datetime]
# (id, sensor_id, value, created_at_datetime)


class CLI:
    """
    CLI utility for aggregating raw metrics from the `metrics` table
    into aggregated tables (minute_metrics / hour_metrics).

    Notes about time:
    - `metrics.created_at` is a datetime (timestamp/timestamptz)
    - interval grouping is done by converting created_at to epoch seconds
      and dividing by interval size (60 / 3600)
    - aggregated created_at is the median timestamp of the interval,
      converted back to datetime
    """

    allowed_modes = ["fill_minute", "fill_hour"]

    def __init__(self, mode: str, pool: asyncpg.Pool):
        self.mode = mode
        self.pool = pool

    @classmethod
    async def create(cls, dsn: str, mode: str) -> "CLI":
        pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
        return cls(mode, pool)

    async def close(self) -> None:
        await self.pool.close()

    def _mode_config(self) -> Tuple[int, str]:
        if self.mode == "fill_minute":
            return 60, "minute_metrics"
        if self.mode == "fill_hour":
            return 3600, "hour_metrics"
        raise ValueError(f"Unknown mode: {self.mode}")

    async def dispatch(self) -> None:
        """
        Reads medians and inserts them one-by-one into target table.
        """
        div, table = self._mode_config()

        # created_at is datetime now, so we pass it directly as $3
        insert_sql = f"""
            INSERT INTO {table} (sensor_id, value, created_at)
            VALUES ($1, $2, $3)
        """

        async with self.pool.acquire() as conn:
            async for sensor_id, value, dt in self.get_medians(conn, div):
                await conn.execute(insert_sql, sensor_id, float(value), dt)

    async def get_medians(
        self,
        conn: asyncpg.Connection,
        div: int,
    ) -> AsyncIterator[Tuple[str, float, datetime]]:
        """
        Yields (sensor_id, median_value, median_created_at_datetime) per interval.
        """
        buffer: Dict[str, List[float]] = {}
        times_epoch: Dict[str, List[int]] = {}
        last_div_time: Dict[str, int] = {}
        tzinfo_by_sensor: Dict[str, timezone | None] = {}

        async for rows in self.fetch_chunks(conn):
            for _id, sensor_id, value, created_at in rows:
                # asyncpg returns datetime for timestamp/timestamptz
                epoch = int(created_at.timestamp())
                div_time = epoch // div

                if sensor_id not in buffer:
                    buffer[sensor_id] = [value]
                    times_epoch[sensor_id] = [epoch]
                    last_div_time[sensor_id] = div_time
                    tzinfo_by_sensor[sensor_id] = created_at.tzinfo
                    continue

                if last_div_time[sensor_id] != div_time:
                    yield (
                        sensor_id,
                        statistics.median(buffer[sensor_id]),
                        self._median_datetime(times_epoch[sensor_id], tzinfo_by_sensor[sensor_id]),
                    )

                    # start new interval with current point
                    buffer[sensor_id] = [value]
                    times_epoch[sensor_id] = [epoch]
                    last_div_time[sensor_id] = div_time
                    tzinfo_by_sensor[sensor_id] = created_at.tzinfo
                else:
                    buffer[sensor_id].append(value)
                    times_epoch[sensor_id].append(epoch)

        # flush remaining intervals
        for sensor_id in buffer:
            yield (
                sensor_id,
                statistics.median(buffer[sensor_id]),
                self._median_datetime(times_epoch[sensor_id], tzinfo_by_sensor[sensor_id]),
            )

    @staticmethod
    def _median_datetime(epoch_seconds: List[int], tzinfo) -> datetime:
        """
        Converts median(epoch_seconds) back to datetime.
        - If source datetimes were tz-aware (timestamptz), preserves tzinfo (typically UTC).
        - If source datetimes were naive (timestamp without tz), returns naive datetime.
        """
        med_epoch = int(statistics.median(epoch_seconds))

        if tzinfo is None:
            # naive datetime
            return datetime.fromtimestamp(med_epoch).replace(tzinfo=None)

        # tz-aware: build in UTC then convert to original tzinfo if needed
        dt_utc = datetime.fromtimestamp(med_epoch, tz=timezone.utc)
        return dt_utc.astimezone(tzinfo)

    async def fetch_chunks(
        self,
        conn: asyncpg.Connection,
        *,
        chunk_size: int = 10_000,
    ) -> AsyncIterator[List[RowT]]:
        """
        Reads metrics in chunks using id-based pagination (no OFFSET).
        """
        last_id = 0
        sql = """
            SELECT id, sensor_id, value, created_at
            FROM metrics
            WHERE id > $1
            ORDER BY id ASC
            LIMIT $2
        """

        while True:
            rows = await conn.fetch(sql, last_id, chunk_size)
            if not rows:
                break

            out: List[RowT] = []
            for r in rows:
                out.append((r["id"], r["sensor_id"], r["value"], r["created_at"]))
                last_id = r["id"]

            yield out


async def main(mode: str, dsn: str) -> None:
    cli = await CLI.create(dsn, mode)
    try:
        await cli.dispatch()
    finally:
        await cli.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=CLI.allowed_modes,
        required=True,
        help="Command: fill_minute | fill_hour",
    )
    parser.add_argument(
        "--dsn",
        default="postgresql://app:63gS2&f|3umA@localhost:5432/app",
        help="PostgreSQL DSN",
    )
    args = parser.parse_args()

    asyncio.run(main(args.mode, args.dsn))
