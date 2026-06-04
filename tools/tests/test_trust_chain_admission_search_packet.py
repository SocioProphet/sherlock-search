from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_trust_chain_admission_search_packet import main as validate_trust_chain_admission_search_packet


ROOT = Path(__file__).resolve().parents[2]
ALLOW_FIXTURE = ROOT / "examples" / "trust-chain" / "admission-search-packet.allow.json"
DENIED_FIXTURE = ROOT / "examples" / "trust-chain" / "admission-search-packet.denied.json"


def test_trust_chain_admission_search_packet_validator() -> None:
    assert validate_trust_chain_admission_search_packet() == 0


def test_allow_packet_is_searchable_without_missing_evidence() -> None:
    fixture = json.loads(ALLOW_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["decision"] == "allow"
    assert fixture["query_facets"]["missing_evidence"] == []
    assert fixture["query_facets"]["remediation_required"] is False
    assert fixture["receipt_refs"]


def test_denied_packet_exposes_missing_evidence_and_remediation() -> None:
    fixture = json.loads(DENIED_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["decision"] == "deny"
    assert fixture["query_facets"]["remediation_required"] is True
    assert fixture["query_facets"]["missing_evidence"]
    assert fixture["remediation"]
    assert fixture["receipt_refs"] == []
