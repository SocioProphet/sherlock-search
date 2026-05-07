from __future__ import annotations

import math
from collections import Counter


def total_variation(p: dict[str, float], q: dict[str, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def _kl(p: dict[str, float], q: dict[str, float]) -> float:
    eps = 1e-12
    out = 0.0
    for k, pv in p.items():
        if pv <= 0:
            continue
        qv = q.get(k, 0.0)
        out += pv * math.log((pv + eps) / (qv + eps))
    return out


def js_distance(p: dict[str, float], q: dict[str, float]) -> float:
    """Jensen–Shannon distance (sqrt of JS divergence), base-e."""
    keys = set(p) | set(q)
    m = {k: 0.5 * (p.get(k, 0.0) + q.get(k, 0.0)) for k in keys}
    js = 0.5 * _kl(p, m) + 0.5 * _kl(q, m)
    return math.sqrt(max(js, 0.0))


def normalize_counter(c: Counter[str]) -> dict[str, float]:
    total = float(sum(c.values()))
    if total <= 0:
        return {}
    return {k: v / total for k, v in c.items() if v > 0}
