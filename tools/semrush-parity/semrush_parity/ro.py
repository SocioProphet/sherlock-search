from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RecommendationObject:
    ro_id: str
    created_time: str
    scope: dict[str, Any]
    evidence: dict[str, Any]
    proposal: dict[str, Any]
    risk: dict[str, Any]
    rollback: dict[str, Any]
    validation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_ro(
    ro_id: str,
    domain: str,
    surface_ids: list[str],
    evidence: dict[str, Any],
    action: str,
    parameters: dict[str, Any] | None = None,
    risk_score: float = 0.2,
    risk_factors: list[str] | None = None,
    guardrails: list[str] | None = None,
    rollback_strategy: str = "manual",
    rollback_steps: list[str] | None = None,
    validation_method: str = "time_holdout",
    primary_metric: str = "issue_count_delta",
    success_criteria: str = "improves",
    followup_metrics: list[str] | None = None,
) -> RecommendationObject:
    return RecommendationObject(
        ro_id=ro_id,
        created_time=now_iso(),
        scope={"domain": domain, "surface_ids": surface_ids},
        evidence=evidence,
        proposal={"action": action, "parameters": parameters or {}},
        risk={
            "risk_score": float(max(0.0, min(1.0, risk_score))),
            "risk_factors": risk_factors or [],
            "guardrails": guardrails or [],
        },
        rollback={
            "strategy": rollback_strategy,
            "steps": rollback_steps or [],
        },
        validation={
            "method": validation_method,
            "primary_metric": primary_metric,
            "success_criteria": success_criteria,
            "followup_metrics": followup_metrics or [],
        },
    )
