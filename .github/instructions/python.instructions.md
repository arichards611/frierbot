---
applyTo: "**/*.py"
---

# QE-Tests Development Conventions

## Environment

Always use the project venv to run tests — the system python is missing dependencies and the root `conftest.py` requires libraries only installed in the venv:
```bash
venv/bin/python -m pytest tests/monitoring_tests/ -v
```

## Fixture Patterns

### Dynamic Fixture Resolution
Use `request.getfixturevalue()` when a fixture needs to pull in other fixtures without requiring tests to declare them:
```python
@pytest.fixture(scope="function")
def my_fixture(request):
    client = request.getfixturevalue("elastic_tunnel_client")
    # Test doesn't need to list elastic_tunnel_client as a parameter
```

### Zero-Touch Fixture Integration
For fixtures that need no interaction from the test body, use `usefixtures` in the marker:
```python
@pytest.mark.usefixtures("ntp_enabled", "restart_sensor_broker_pod")
def test_something(elastic_tunnel_client):
    ...
```

## Common Fixture Types

| Fixture | Type | Import |
|---------|------|--------|
| `prometheus_client` | `Prometheus` | `from framework.api.Prometheus import Prometheus` |
| `elastic_tunnel_client` | `Elasticsearch` | `from elasticsearch import Elasticsearch` |
| `amqp_tunnel_client` | `pika.BlockingConnection` | `import pika` |
| `sensor_host` | `Host` | `from frametools.host import Host` |
| `replay_host_and_interface` | `Tuple[Host, str]` | |
| `files_client` | `Files.Files` | `from framework.api import Files` |
| `dropped_queue_monitor` | `DroppedQueueMonitor` | auto-requested via `@pytest.mark.dropped_queue_monitor` |

## Allure Patterns

### Conditional Allure (works with and without allure runner)
```python
try:
    allure.attach(data, name="Report", attachment_type=allure.attachment_type.TEXT)
except Exception:
    LOGGER.warning(f"Allure not available, report:\n{data}")  # Fallback for local runs without allure
```

### Metadata Constants
Always use enums from `allure_testops/metadata.py`:
```python
from allure_testops.metadata import Feature, Label, Severity, Tag, Team, jira_link
```

### Allure Steps (required when refactoring)
When refactoring or creating tests, every logical phase must be wrapped in `allure.step()`:
```python
with allure.step("Replay PCAP"):
    replay_pcap_list_full(...)

with allure.step("Verify ES records"):
    # poll and assert
```
Replace old `separator("Step N: ...")` calls with `with allure.step("..."):`.

## Marker Registration

Register custom markers in `pytest.ini` (preferred) or in the `pytest_configure()` hook in `conftest.py`:
```ini
# pytest.ini (preferred for this repo — most markers live here)
markers =
    my_marker(arg): Description of marker.
```
```python
# conftest.py (use only when marker needs runtime logic)
def pytest_configure(config):
    config.addinivalue_line("markers", "my_marker(arg): Description of marker.")
```

## Dropped Queue Monitor

Opt-in monitoring of `dataflow.sensorData.dropped_sis` for message drops during tests.

### Usage
```python
@pytest.mark.dropped_queue_monitor(strict=True)
def test_sensor_flow(...):
    ...
```

- Just add the marker — the fixture is auto-requested via `pytest_collection_modifyitems`

- `strict=True` — test fails if drops detected
- `strict=False` — emits a warning
- Requires `elastic_tunnel_client` fixture (auto-resolved)
- Reports failure reasons from `dataflow_failures` ES index
- Attaches report to allure (or logs it for local runs)

### Ignore List
Known/expected ES failures can be silently ignored via `IGNORE_RULES` in `shared/monitoring/ignore_rules.py`.
Rules use multi-field AND conditions — a rule matches when **all** its conditions match:
```python
from shared.monitoring.ignore_rules import IgnoreCondition, IgnoreRule

# Single-field rule:
IgnoreRule(
    conditions=[IgnoreCondition(field="firstBody", contains="sensor-heartbeat")],
    description="Known heartbeat noise",
)

# Multi-field rule (AND logic):
IgnoreRule(
    conditions=[
        IgnoreCondition(field="firstBody", contains="sensor-heartbeat"),
        IgnoreCondition(field="processor", contains="ArpSensorDataProcessor"),
    ],
    description="Heartbeat noise from ARP processor only",
)
```

- A document is ignored if **any** rule matches (OR across rules)
- If all ES failures match ignore rules, the monitor treats it as no drops detected
- Available fields: `reason`, `firstMessage`, `firstBody`, `processor`, `count`, `timeStart`

## ES Query Patterns

### dataflow_failures Index
```python
es_client.search(index="dataflow_failures-*", body={
    "query": {"bool": {"filter": [
        {"range": {"timeStart": {"gte": since.isoformat()}}}
    ]}},
    "_source": ["reason", "firstMessage", "firstBody", "processor", "count", "timeStart"],
})
```

### Pipeline Data Queries
Use `get_search_param` for flexible field matching:
```python
from sitestore.backend.sensor_management.common import get_search_param
query = get_search_param(from_time=start, query_type="match", source="suricata")
```

### No Manual Refresh Before Search
`elastic_tunnel_client.indices.refresh()` is **not needed** before `.search()` — Elasticsearch automatically refreshes on search. Do not add `indices.refresh()` calls in polling loops.

## Logging
Use the framework logger, not stdlib:
```python
from framework.logger import Logger
LOGGER = Logger(__name__)
```

## Framework API Return Types

Key framework methods have non-obvious return types. Document them here to avoid bugs.

| Method | Returns | Notes |
|--------|---------|-------|
| `Prometheus.get_rabbitmq_queue_len(queue)` | `tuple[dict, float]` | `(response_dict, request_time_seconds)` — must unpack |
| `Prometheus.get_config()` | `tuple[dict, float]` | Same pattern as above |
| `replay_pcap_list_full(...)` | `PcapReplay` | NamedTuple with `.replay_start`, `.replay_stop`, `.pcap_mapping` |

```python
# Correct usage — unpack the tuple:
response, _rtt = prometheus_client.get_rabbitmq_queue_len(queue_name)
count = parse_queue_count(response)

# WRONG — passing the tuple directly:
response = prometheus_client.get_rabbitmq_queue_len(queue_name)
response.get("data")  # AttributeError: 'tuple' object has no attribute 'get'
```

```python
# Correct usage — use PcapReplay return value for start time:
replay = replay_pcap_list_full(pcaps=[...], replay_host_and_interface=..., ...)
query = get_search_param(from_time=replay.replay_start, query_type="match", source="suricata")

# WRONG — calling get_utc_datetime_from_host separately (redundant, replay already captures this):
start = get_utc_datetime_from_host(sensor_host)
replay_pcap_list_full(...)
```

## Monitoring Module (`shared/monitoring/`)

| File | Purpose |
|------|---------|
| `dropped_queue_monitor.py` | `DroppedQueueMonitor`, `MonitorResult`, `DropRecord`, `DroppedQueueSummary` |
| `elasticsearch_utils.py` | `get_recent_dataflow_failures`, `aggregate_failures_by_reason`, `format_failure_message` |
| `ignore_rules.py` | `IgnoreCondition`, `IgnoreRule`, `IGNORE_RULES`, `matches_ignore_rule`, `filter_ignored_failures` |

### Detection Model
The monitor checks the `dataflow_failures-*` ES index for new documents during each test.

`MonitorResult` fields:
- `new_docs` — number of new ES failure docs since test start
- `failure_message` — formatted details of failures (reasons, processors, timestamps)

Session-level summary:
- `DroppedQueueSummary` — accumulates `DropRecord` entries across the session

## Monitoring Module Tests (`tests/monitoring_tests/`)

Unit tests for `shared/monitoring/` modules use `unittest.mock.MagicMock` for external dependencies.

### Mocking ES responses
```python
es = MagicMock()
es.search.return_value = {
    "hits": {"hits": [
        {"_source": {"reason": "MALFORMED_DATA", "firstBody": "...",
                     "processor": "ArpSensorDataProcessor", "count": 5,
                     "timeStart": "2026-02-17T08:58:26.640Z"}},
    ]}
}
```

### Mocking ES for monitor tests
The monitor queries ES once during `check()`. Use `return_value` for a single response:
```python
def _make_es_hits(docs: list[dict]) -> dict:
    return {"hits": {"hits": [{"_source": doc} for doc in docs]}}

es = MagicMock()
es.search.return_value = _make_es_hits([{"reason": "MALFORMED_DATA", "count": 2, ...}])
```
