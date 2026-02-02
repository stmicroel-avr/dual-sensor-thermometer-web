import asyncio
import aiosqlite
import statistics
from argparse import ArgumentParser


class CLI:
    allowed_modes = ["fill_minute", "fill_hour"]

    @classmethod
    async def create(cls, dsn: str, cmd: str):
        conn = await aiosqlite.connect(dsn)
        await conn.execute("PRAGMA journal_mode=WAL;")
        return cls(cmd, conn)

    def __init__(self, cmd, conn):
        self.cmd = cmd
        self.db = conn

    async def dispatch(self):
        div = 0
        table = ""
        if self.cmd == "fill_minute":
            div = 60
            table = "minute_metrics"
        elif self.cmd == "fill_hour":
            div = 3600
            table = "hour_metrics"

        if not div:
            raise asyncio.CancelledError()

        async for median in self.get_median(div):
            (name, value, time) = median
            await self.db.execute(f"""insert into {table}(sensor_id, value, created_at) values ('{name}', {value}, {time})""")
            await self.db.commit()

    async def get_median(self, div: int):
        buffer = {}
        times = {}
        last_div_time = {}
        async for rows in self.fetch_chunks():
            async for row in rows:
                (id, name, value, time) = row
                if name not in buffer:
                    times[name] = [time]
                    buffer[name] = [value]
                    last_div_time[name] = time // div
                    continue

                div_time = time // div
                buffer[name].append(value)
                times[name].append(time)
                if last_div_time[name] != div_time:
                    yield name, statistics.median(buffer[name]), int(statistics.median(times[name]))
                    del times[name]
                    del buffer[name]
                    del last_div_time[name]

    async def fetch_chunks(self, chunk_size: int = 100):
        offset = 0
        while True:
            offset = offset + chunk_size
            rows = await self.db.execute(f"""select * from metrics 
            order by id asc
            limit {chunk_size} offset {offset} 
            """)
            if not rows:
                break
            yield rows

async def main(cmd: str):
    cli = await CLI.create("app.db", cmd)
    await cli.dispatch()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        choices=CLI.allowed_modes,
        required=True,
        help="Команда: fill_minute | fill_hour"
    )
    args = parser.parse_args()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main(args.mode))

