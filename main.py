import asyncio
import logging
import logging.config
import os
from dotenv import load_dotenv
import yaml
from prometheus_client import start_http_server
from src.core.sinks_pg import PGSink
from src.core.sinks_kafka import KafkaSink

from src.core.bus import EventBus
from src.core.sinks import fanout_for_dashboard
from src.ingestion.pandascore_client import PandaScoreClient
from src.ingestion.lol_schedule_stream import LolScheduleStream
from src.ingestion.lol_results_stream import LolResultsStream
from src.ingestion.lolesports_client import LoLEsports
from src.ingestion.lol_live_stream import LolLiveStream

load_dotenv()


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


async def consumer_loop(bus: EventBus):
    # init sinks
    pg = PGSink(os.getenv("PG_DSN"))
    await pg.init()

    kafka = KafkaSink(os.getenv("KAFKA_BOOTSTRAP"))
    await kafka.start()

    try:
        async for ev in bus.subscribe():
            # Fan out in parallel; if one fails, log and continue
            await asyncio.gather(
                pg.write_event(ev),
                kafka.write_event(ev),
                return_exceptions=True,
            )
    finally:
        await kafka.stop()


async def run_ingestion():
    cfg = load_yaml("config/pandascore.yaml")
    lolcfg = load_yaml("config/lolesports.yaml")["lolesports"]

    logging.config.dictConfig(load_yaml("config/logging.yaml"))

    bus = EventBus()
    client = PandaScoreClient(
        base_url=cfg["pandascore"]["base_url"],
        requests_per_hour=cfg["pandascore"]["requests_per_hour"],
    )

    leagues = cfg["pandascore"].get("leagues_whitelist") or None
    pagesize = int(cfg["pandascore"].get("pagesize", 50))

    schedule = LolScheduleStream(
        client,
        bus,
        poll_seconds=cfg["pandascore"]["poll"]["schedule_seconds"],
        leagues=leagues,
        pagesize=pagesize,
    )
    results = LolResultsStream(
        client,
        bus,
        poll_seconds=cfg["pandascore"]["poll"]["results_seconds"],
        pagesize=pagesize,
    )
    # add lolesports as well
    lec = LoLEsports(lolcfg["gw_base"], lolcfg["feed_base"], hl=lolcfg["hl"])
    live = LolLiveStream(
        lec,
        bus,
        discover_s=lolcfg["poll"]["discover_seconds"],
        window_s=lolcfg["poll"]["window_seconds"],
        details_s=lolcfg["poll"]["details_seconds"],
    )

    # Prometheus on :9108
    start_http_server(int(os.getenv("PROM_PORT", "9108")))

    await asyncio.gather(consumer_loop(bus), schedule.run(), results.run(), live.run())


if __name__ == "__main__":
    try:
        asyncio.run(run_ingestion())
    except KeyboardInterrupt:
        pass
