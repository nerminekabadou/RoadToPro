from prometheus_client import Counter, Histogram

requests_total = Counter(
    "ps_requests_total", "Total PandaScore REST requests", ["endpoint"]
)
requests_errors = Counter(
    "ps_requests_errors_total", "PandaScore REST errors", ["endpoint", "status"]
)
latency = Histogram(
    "ps_request_latency_seconds", "PandaScore REST latency", ["endpoint"]
)
events_out = Counter("ingestion_events_out_total", "Events published", ["type"])
