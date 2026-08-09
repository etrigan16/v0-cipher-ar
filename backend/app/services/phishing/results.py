"""Pure phishing results aggregation (Phase 5, PR 5).

The routes perform the tenant-scoped queries (target rows + a GROUP BY over
tracking events) and feed plain values into these functions, keeping the
per-target flag/timestamp shape, the tenant aggregate math and the CSV
rendering pure and unit-testable without the ORM — mirroring the report
generators in ``app.services.reports``.

Result-surfaced event types (design D3): ``open|click|credential|report``.
The ``landing`` event is audited for tracking but never flips a results flag.
"""

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

OPEN = "open"
CLICK = "click"
CREDENTIAL = "credential"
REPORT = "report"

# Spec R1 CSV headers — the PR-5 export resolution of the per-target table.
RESULTS_CSV_HEADERS = ("email", "name", "status", "opened", "clicked", "credential", "reported")


@dataclass(frozen=True)
class TargetResult:
    """One target's aggregated activity: flags + first-event timestamps.

    ``opened_at``/``clicked_at``/``credential_at``/``reported_at`` carry the
    target's earliest ``occurred_at`` for each result-surfaced event type
    (``None`` when the target never performed that action).
    """

    email: str
    name: str
    status: str
    opened: bool
    clicked: bool
    credential: bool
    reported: bool
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    credential_at: datetime | None = None
    reported_at: datetime | None = None


@dataclass(frozen=True)
class ResultsSummary:
    """Tenant-wide aggregate: counts + engagement rates (spec R2)."""

    total_targets: int
    sent: int
    opened_count: int
    opened_rate: float
    clicked_count: int
    clicked_rate: float
    credentials_count: int
    reported_count: int


def build_target_result(
    *,
    email: str,
    name: str,
    status: str,
    event_times: Mapping[str, datetime | None],
) -> TargetResult:
    """Aggregate one target's per-type first-event times (spec R1).

    ``event_times`` maps a result-surfaced event type to the target's
    earliest ``occurred_at`` for that type. An absent key (or a ``None``
    value) means the target never performed the action: flag ``False``,
    timestamp ``None``.
    """
    return TargetResult(
        email=email,
        name=name,
        status=status,
        opened=event_times.get(OPEN) is not None,
        clicked=event_times.get(CLICK) is not None,
        credential=event_times.get(CREDENTIAL) is not None,
        reported=event_times.get(REPORT) is not None,
        opened_at=event_times.get(OPEN),
        clicked_at=event_times.get(CLICK),
        credential_at=event_times.get(CREDENTIAL),
        reported_at=event_times.get(REPORT),
    )


def summarize(results: Sequence[TargetResult]) -> ResultsSummary:
    """Aggregate counts/rates from per-target results (spec R2).

    ``sent`` counts targets whose status is ``active`` — launch activates
    every target, so pending targets were never delivered. Rates are
    percentages of ``sent``; an empty tenant (or any zero ``sent``) yields
    0.0 rates and zero counts, never an error (spec R2 empty-tenant
    scenario).
    """
    total = len(results)
    sent = sum(1 for r in results if r.status == "active")
    opened = sum(1 for r in results if r.opened)
    clicked = sum(1 for r in results if r.clicked)
    credentials = sum(1 for r in results if r.credential)
    reported = sum(1 for r in results if r.reported)
    return ResultsSummary(
        total_targets=total,
        sent=sent,
        opened_count=opened,
        opened_rate=round(opened / sent * 100, 2) if sent else 0.0,
        clicked_count=clicked,
        clicked_rate=round(clicked / sent * 100, 2) if sent else 0.0,
        credentials_count=credentials,
        reported_count=reported,
    )


def generate_results_csv(results: Sequence[TargetResult]) -> str:
    """Render per-target results as CSV (spec R1 / PR-5 export).

    Uses the stdlib ``csv`` writer with ``\\n`` line terminators (quoting and
    escaping of commas/quotes/newlines handled by the module). Boolean flags
    render as lowercase ``true``/``false``. An empty campaign still produces
    the headers-only row — 200, never an error (mirrors ``generate_csv``).
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(RESULTS_CSV_HEADERS)
    for row in results:
        writer.writerow(
            [
                row.email,
                row.name,
                row.status,
                "true" if row.opened else "false",
                "true" if row.clicked else "false",
                "true" if row.credential else "false",
                "true" if row.reported else "false",
            ]
        )
    return buffer.getvalue()
