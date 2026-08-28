#!/usr/bin/env python3
"""Resonance-aware ranking postprocess.

This layer keeps large emitters credible without letting them dominate only
because they are large. It also keeps small, concrete, early dynamics visible.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import network_hub_postprocess as hub
import yaml


ROOT = Path(__file__).resolve().parents[1]
BRIEFINGS = ROOT / "briefings"
STATE = ROOT / "state"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def text_of(item: dict[str, Any]) -> str:
    return " ".join(str(x or "") for x in [
        item.get("title"),
        item.get("summary"),
        item.get("url"),
        item.get("source"),
        " ".join(item.get("matched_keywords") or []),
        " ".join(item.get("watchgraph_modules") or []),
    ]).lower()


def infer_class_from_item(item: dict[str, Any]) -> str:
    explicit = str(item.get("source_class") or "").strip()
    if explicit:
        return explicit

    text = f"{item.get('source','')} {item.get('source_type','')} {item.get('url','')}".lower()
    if any(x in text for x in ["federal reserve", "federalreserve.gov", "ecb", "europa.eu/rss", "bis.org", "bank for international settlements"]):
        return "central_bank"
    if any(x in text for x in ["oecd", "world bank", "imf.org", "wto.org"]):
        return "policy_institution"
    if any(x in text for x in ["gdeltproject.org", "gdelt "]):
        return "global_media_monitor"
    if any(x in text for x in ["usgs", "gdacs", "noaa", "nhc", "gfz", "geofon"]):
        return "emergency_official"
    return hub.source_class(item)


def reach_profile(classes: set[str], sources: list[str]) -> dict[str, Any]:
    source_text = " ".join(sources).lower()

    if "central_bank" in classes or any(x in source_text for x in ["federal reserve", "ecb", "bis "]):
        return {"tier": "institutional", "reach": 5.0, "dominant_emitter": True, "kind": "central_bank"}
    if "policy_institution" in classes or any(x in source_text for x in ["oecd", "world bank", "imf"]):
        return {"tier": "institutional", "reach": 4.5, "dominant_emitter": True, "kind": "policy_institution"}
    if "global_media_monitor" in classes:
        return {"tier": "broad_sensor", "reach": 3.0, "dominant_emitter": False, "kind": "media_monitor"}
    if "emergency_official" in classes or "tier1_official" in classes:
        return {"tier": "official", "reach": 4.0, "dominant_emitter": True, "kind": "official"}
    if "tier2_major_news" in classes:
        return {"tier": "major_media", "reach": 4.0, "dominant_emitter": True, "kind": "major_media"}
    if "tier3_specialist" in classes:
        return {"tier": "specialist", "reach": 2.5, "dominant_emitter": False, "kind": "specialist"}
    if "tier4_platform_social" in classes:
        return {"tier": "social", "reach": 2.0, "dominant_emitter": False, "kind": "social"}
    if "tier5_generic_repo" in classes:
        return {"tier": "small_initial", "reach": 1.5, "dominant_emitter": False, "kind": "repo"}
    return {"tier": "unknown", "reach": 2.0, "dominant_emitter": False, "kind": "unknown"}


EARLY_TERMS = [
    "wildfire", "forest fire", "flood", "drought", "blackout", "port closure",
    "strike", "protest", "pipeline outage", "supply chain", "outage",
    "local", "regional", "evacuation", "unrest", "shortage",
]

HIGH_SIGNAL_TERMS = [
    "rate decision", "emergency", "market halted", "trading suspended",
    "state of emergency", "evacuation order", "red alert", "orange alert",
    "central bank emergency", "export ban", "pipeline outage", "port closure",
]


def configured_signal_terms() -> tuple[list[str], list[str]]:
    """Extend legacy defaults with the governed fork configuration."""
    early = list(EARLY_TERMS)
    high = list(HIGH_SIGNAL_TERMS)

    resonance_path = ROOT / "config" / "resonance_ranking.yaml"
    governance_path = ROOT / "config" / "source_governance.yaml"
    try:
        resonance = yaml.safe_load(resonance_path.read_text(encoding="utf-8")) or {}
    except Exception:
        resonance = {}
    try:
        governance = yaml.safe_load(governance_path.read_text(encoding="utf-8")) or {}
    except Exception:
        governance = {}

    if isinstance(resonance, dict):
        early_config = ((resonance.get("early_signal") or {}).get("trigger_terms") or [])
        early.extend(early_config)
    if isinstance(governance, dict):
        signals = governance.get("signals") or {}
        if isinstance(signals, dict):
            early.extend(signals.get("early_signal_terms") or [])
            high.extend(signals.get("high_signal_terms") or [])

    def dedupe(values: list[Any]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            term = str(value).strip()
            key = term.casefold()
            if term and key not in seen:
                result.append(term)
                seen.add(key)
        return result

    return dedupe(early), dedupe(high)


EARLY_TERMS, HIGH_SIGNAL_TERMS = configured_signal_terms()


def any_term(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def calc_scores(cluster: dict[str, Any], items: list[dict[str, Any]], velocity: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    key = str(cluster.get("key") or "")
    sources = list(cluster.get("sources") or [])
    classes = {infer_class_from_item(item) for item in items}
    classes.update(str(c) for c in (cluster.get("source_classes") or []) if c)
    classes = {str(c) for c in classes if c}

    profile = reach_profile(classes, sources)
    max_score = float(cluster.get("max_score") or 0)
    source_count = max(1, len(sources))
    cross = bool(cluster.get("cross_source_confirmed"))
    delta = int(cluster.get("momentum_delta") or 0)

    joined_text = " ".join(text_of(item) for item in items)
    high_signal = any_term(joined_text, HIGH_SIGNAL_TERMS)

    entity = ((velocity.get("entities") or {}) if isinstance(velocity, dict) else {}).get(key, {})
    first_seen_at = entity.get("first_seen_at") if isinstance(entity, dict) else None
    history = entity.get("history") if isinstance(entity, dict) else []
    age_runs = len(history) if isinstance(history, list) else 1

    base = ((baseline.get("entities") or {}) if isinstance(baseline, dict) else {}).get(key, {})
    z_hint = float(base.get("z_hint") or 0) if isinstance(base, dict) else 0.0

    authority_bonus = min(3.0, float(profile["reach"]) * 0.6)

    breadth_bonus = min(8.0, 2.5 * max(0, source_count - 1))
    if cross:
        breadth_bonus += 3.0

    momentum_bonus = min(8.0, 2.5 * max(0, delta))
    baseline_bonus = min(5.0, max(0.0, z_hint) * 0.4)

    is_newish = age_runs <= 3 and delta >= 0
    small_or_broad = not bool(profile["dominant_emitter"])
    concrete_initial = any_term(joined_text, EARLY_TERMS)
    early_signal = bool(is_newish and small_or_broad and (concrete_initial or max_score >= 12))
    early_bonus = 0.0
    if early_signal:
        early_bonus = 4.0
        if concrete_initial:
            early_bonus += 2.0
        if source_count == 1 and max_score >= 12:
            early_bonus += 1.5
        early_bonus = min(8.0, early_bonus)

    dominance_penalty = 0.0
    dominance_reason = ""
    if profile["dominant_emitter"] and not cross and delta <= 1 and not high_signal:
        dominance_penalty = 3.0
        dominance_reason = "large emitter without cross-source resonance or high-signal term"

    ranking_score = (
        max_score
        + authority_bonus
        + breadth_bonus
        + momentum_bonus
        + baseline_bonus
        + early_bonus
        - dominance_penalty
    )
    if high_signal:
        ranking_score += 4.0

    hot = bool(
        (cross and ranking_score >= 22)
        or (early_signal and ranking_score >= 24)
        or (high_signal and ranking_score >= 24)
        or (source_count >= 3 and delta >= 1)
    )

    return {
        "source_classes": sorted(classes),
        "initial_reach_tier": profile["tier"],
        "source_reach_score": round(float(profile["reach"]), 2),
        "authority_bonus_capped": round(authority_bonus, 2),
        "breadth_bonus": round(breadth_bonus, 2),
        "momentum_bonus": round(momentum_bonus, 2),
        "baseline_bonus": round(baseline_bonus, 2),
        "early_signal": early_signal,
        "early_signal_bonus": round(early_bonus, 2),
        "high_signal": high_signal,
        "dominant_emitter": bool(profile["dominant_emitter"]),
        "dominance_penalty": round(dominance_penalty, 2),
        "dominance_reason": dominance_reason,
        "first_seen_at": first_seen_at,
        "raw_network_score": cluster.get("network_score"),
        "ranking_score": round(max(0.0, ranking_score), 2),
        "hot": hot,
    }


def render_breaking(network: dict[str, Any]) -> str:
    lines = ["# Senna Breaking", "", f"_Generiert: {network.get('generated_at')}_", ""]
    hot = [c for c in network.get("clusters", []) if c.get("hot")][:5]
    if not hot:
        lines += ["Keine Breaking-Signale. Kleine Signale bleiben im Network Hub sichtbar.", ""]
    for c in hot:
        urls = c.get("urls") or ["keine"]
        dominant = "ja" if c.get("dominant_emitter") else "nein"
        early = "ja" if c.get("early_signal") else "nein"
        cross = "ja" if c.get("cross_source_confirmed") else "nein"
        lines += [
            f"## {c.get('title')}",
            "",
            f"- Ranking Score: `{c.get('network_score')}`",
            f"- Raw Network Score: `{c.get('raw_network_score', 'n/a')}`",
            f"- Max Monitor Score: `{c.get('max_score')}`",
            f"- Reichweite: `{c.get('initial_reach_tier')}` / `{c.get('source_reach_score')}`",
            f"- Early Signal: `{early}`",
            f"- Dominanter Emitter: `{dominant}`",
            f"- Quellen: {', '.join(c.get('sources') or []) or 'unbekannt'}",
            f"- Klassen: {', '.join(c.get('source_classes') or []) or 'unbekannt'}",
            f"- Cross-source bestaetigt: {cross}",
            f"- Momentum: {c.get('momentum_status')} ({int(c.get('momentum_delta') or 0):+d})",
            f"- Erste Quelle: {urls[0]}",
            f"- Handlung: {c.get('recommended_action')}",
            "",
        ]
    return "\n".join(lines)


def main() -> int:
    latest = read_json(BRIEFINGS / "latest.json", {})
    network = read_json(BRIEFINGS / "network.json", {})
    velocity = read_json(STATE / "velocity.json", {})
    baseline = read_json(STATE / "baseline.json", {})

    findings = latest.get("findings") if isinstance(latest, dict) else []
    findings = findings if isinstance(findings, list) else []

    groups: dict[str, list[dict[str, Any]]] = {}
    for item in findings:
        if isinstance(item, dict):
            groups.setdefault(hub.key_for(item), []).append(item)

    clusters = network.get("clusters") if isinstance(network, dict) else []
    clusters = clusters if isinstance(clusters, list) else []

    updated = []
    for cluster in clusters:
        if not isinstance(cluster, dict):
            continue
        key = str(cluster.get("key") or "")
        items = groups.get(key, [])
        calc = calc_scores(cluster, items, velocity, baseline)
        c = dict(cluster)
        c["raw_network_score"] = calc["raw_network_score"]
        c["network_score"] = calc["ranking_score"]
        c["ranking_score"] = calc["ranking_score"]
        c["source_classes"] = calc["source_classes"] or c.get("source_classes", [])
        c["initial_reach_tier"] = calc["initial_reach_tier"]
        c["source_reach_score"] = calc["source_reach_score"]
        c["authority_bonus_capped"] = calc["authority_bonus_capped"]
        c["breadth_bonus"] = calc["breadth_bonus"]
        c["momentum_bonus"] = calc["momentum_bonus"]
        c["baseline_bonus"] = calc["baseline_bonus"]
        c["early_signal"] = calc["early_signal"]
        c["early_signal_bonus"] = calc["early_signal_bonus"]
        c["high_signal"] = calc["high_signal"]
        c["dominant_emitter"] = calc["dominant_emitter"]
        c["dominance_penalty"] = calc["dominance_penalty"]
        c["dominance_reason"] = calc["dominance_reason"]
        c["first_seen_at"] = calc["first_seen_at"]
        c["hot"] = calc["hot"]

        if c["hot"]:
            if c["early_signal"]:
                c["recommended_action"] = "HOT EARLY: kleines oder breites Anfangssignal sichern, Gegenquellen pruefen, Verlauf beobachten."
            elif c.get("cross_source_confirmed"):
                c["recommended_action"] = "HOT CONFIRMED: cross-source bestaetigt. Quelle sichern, Kontext pruefen, bei Relevanz aktiv alarmieren."
        updated.append(c)

    updated.sort(
        key=lambda c: (
            float(c.get("network_score") or 0),
            bool(c.get("early_signal")),
            int(c.get("max_score") or 0),
            int(c.get("finding_count") or 0),
        ),
        reverse=True,
    )

    network = dict(network  if isinstance(network, dict) else {})
    network["resonance_ranking"] = {
        "schema_version": 1,
        "generated_at": now(),
        "principle": "Authority is capped; early novelty, cross-source breadth, momentum and baseline deviation carry ranking.",
        "dominance_guard": "Large emitters keep credibility but receive no automatic dominance without resonance or high-signal terms.",
    }
    network["clusters"] = updated
    network["counts"] = dict(network.get("counts") or {})
    network["counts"]["hot"] = sum(1 for c in updated if c.get("hot"))
    network["counts"]["early_signals"] = sum(1 for c in updated if c.get("early_signal"))
    network["counts"]["dominance_penalized"] = sum(1 for c in updated if float(c.get("dominance_penalty") or 0) > 0)

    write_json(BRIEFINGS / "network.json", network)
    write_text(BRIEFINGS / "breaking.md", render_breaking(network) + "\n")

    print(
        "Resonance ranking complete: "
        f"{len(updated)} clusters, {network['counts']['early_signals']} early, "
        f"{network['counts']['dominance_penalized']} dominance-penalized."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
