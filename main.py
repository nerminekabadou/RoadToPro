import asyncio
import logging
import logging.config
import os
import yaml
from prometheus_client import start_http_server

from src.core.bus import EventBus
from src.core.sinks import fanout_for_dashboard
from src.ingestion.pandascore_client import PandaScoreClient
from src.ingestion.lol_schedule_stream import LolScheduleStream
from src.ingestion.lol_results_stream import LolResultsStream


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


async def consumer_loop(bus: EventBus):
    log = logging.getLogger(__name__)
    async for ev in bus.subscribe():
        log.info(f"Consumed event: {ev.get('type')}")
        # Single place to fan out (files, sockets, DB, Kafka…)
        await fanout_for_dashboard(ev)


async def run_ingestion():
    cfg = load_yaml("config/pandascore.yaml")
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

    # Prometheus on :9108
    start_http_server(int(os.getenv("PROM_PORT", "9108")))

    await asyncio.gather(
        consumer_loop(bus),
        schedule.run(),
        results.run(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(run_ingestion())
    except KeyboardInterrupt:
        pass
