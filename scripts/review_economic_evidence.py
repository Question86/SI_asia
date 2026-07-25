#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
D_CAND = ROOT / "data/economic_evidence_candidates.jsonl"
D_REVIEWS = ROOT / "data/economic_evidence_reviews.jsonl"
D_EVIDENCE = ROOT / "data/economic_evidence.jsonl"
D_FX = ROOT / "config/economic_fx_rates.json"
D_JSON = ROOT / "briefings/economic_evidence_review.json"
D_MD = ROOT / "briefings/economic_evidence_review.md"

COMPONENT_RULES = [
    ("real_resource", ("cost", "loss", "damage", "repair", "rebuild", "downtime", "kosten", "schaden", "verlust")),
    ("valuation", ("valuation", "market cap", "shares", "stock", "wiped", "bewertung", "börse", "aktie")),
    ("capital_allocation", ("funding", "investment", "budget", "capex", "subsidy", "financing", "investition", "haushalt")),
    ("transfers", ("fine", "penalty", "insurance payout", "claim", "settlement", "bußgeld", "strafe", "vergleich")),
]

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

def load_fx(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"base": "USD", "as_of": None, "rates_to_usd": {"USD": 1.0}}
    return json.loads(path.read_text(encoding="utf-8"))

def classify_component(snippet: str) -> tuple[str, float]:
    text = snippet.lower()
    hits = [(name, sum(term in text for term in terms)) for name, terms in COMPONENT_RULES]
    name, count = max(hits, key=lambda x: x[1])
    return ("unknown", 0.0) if count == 0 else (name, min(0.95, 0.55 + 0.12 * (count - 1)))

def suggest_overlap(event_id: str, component: str, snippet: str) -> str:
    normalized = re.sub(r"\W+", " ", snippet.lower()).strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{event_id}:{component}:{digest}"

def enrich(candidate: dict[str, Any], fx: dict[str, Any]) -> dict[str, Any]:
    row = dict(candidate)
    component, confidence = classify_component(str(row.get("snippet", "")))
    if row.get("component_suggestion") in (None, "", "unknown"):
        row["component_suggestion"] = component
    row["component_confidence"] = confidence
    row["overlap_group_suggestion"] = suggest_overlap(
        str(row.get("event_id", "unknown")),
        str(row.get("component_suggestion", "unknown")),
        str(row.get("snippet", "")),
    )
    currency = str(row.get("currency", "USD"))
    amount_native = float(row.get("amount_native", 0.0) or 0.0)
    rate = fx.get("rates_to_usd", {}).get(currency)
    if rate is not None:
        row["amount_usd"] = round(amount_native * float(rate), 2)
        row["conversion_status"] = "converted" if currency != "USD" else "not_required"
        row["fx_rate_to_usd"] = float(rate)
        row["fx_as_of"] = fx.get("as_of")
    else:
        row["amount_usd"] = None
        row["conversion_status"] = "missing_rate"
    row.setdefault("review_status", "pending")
    return row

def promote(candidate: dict[str, Any], review: dict[str, Any]) -> dict[str, Any] | None:
    if review.get("review_status") != "accepted":
        return None
    probability = review.get("attribution_probability")
    if probability is None or not 0 <= float(probability) <= 1:
        return None
    amount_usd = candidate.get("amount_usd")
    component = review.get("component") or candidate.get("component_suggestion")
    if amount_usd is None or component in (None, "", "unknown"):
        return None
    return {
        "event_id": candidate["event_id"],
        "observed_at": candidate.get("observed_at") or now(),
        "component": component,
        "gross_usd": float(amount_usd),
        "net_usd": review.get("net_usd"),
        "attribution_probability": float(probability),
        "overlap_group": review.get("overlap_group") or candidate["overlap_group_suggestion"],
        "source_url": candidate["source_url"],
        "source_type": review.get("source_type") or candidate.get("source_priority", "unknown"),
        "notes": review.get("notes", ""),
        "candidate_id": candidate["candidate_id"],
        "reviewed_at": review.get("reviewed_at") or now(),
    }

def write_reports(rows, promoted, json_path, md_path, fx):
    counts = {}
    for row in rows:
        status = row.get("review_status", "pending")
        counts[status] = counts.get(status, 0) + 1
    warning = None if rows else "No candidates does not imply no monetary evidence; it may indicate missing or inaccessible source URLs."
    payload = {
        "version": 1, "generated_at": now(), "fx_as_of": fx.get("as_of"),
        "candidate_count": len(rows), "promoted_count": len(promoted),
        "review_counts": counts, "coverage_warning": warning,
        "candidates": sorted(rows, key=lambda r: (r.get("candidate_confidence", 0), r.get("amount_usd") or 0), reverse=True),
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Economic Evidence Review", "", f"Generated: `{payload['generated_at']}`", f"FX as of: `{payload['fx_as_of']}`", "",
             f"- Candidates: **{len(rows)}**", f"- Promoted: **{len(promoted)}**"]
    if warning:
        lines += ["", f"> {warning}"]
    lines += ["", "| Candidate | Event | USD | Component | Status |", "|---|---|---:|---|---|"]
    for row in payload["candidates"][:40]:
        amount = "—" if row.get("amount_usd") is None else f"${row.get('amount_usd'):,.0f}"
        lines.append(f"| `{row.get('candidate_id')}` | `{row.get('event_id')}` | {amount} | {row.get('component_suggestion')} | {row.get('review_status')} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=D_CAND)
    parser.add_argument("--reviews", type=Path, default=D_REVIEWS)
    parser.add_argument("--evidence", type=Path, default=D_EVIDENCE)
    parser.add_argument("--fx", type=Path, default=D_FX)
    parser.add_argument("--json-report", type=Path, default=D_JSON)
    parser.add_argument("--md-report", type=Path, default=D_MD)
    args = parser.parse_args()

    fx = load_fx(args.fx)
    candidates = [enrich(row, fx) for row in read_jsonl(args.candidates)]
    reviews = {row["candidate_id"]: row for row in read_jsonl(args.reviews) if row.get("candidate_id")}
    existing = {row.get("candidate_id"): row for row in read_jsonl(args.evidence) if row.get("candidate_id")}
    promoted = []
    for candidate in candidates:
        review = reviews.get(candidate["candidate_id"])
        if review:
            candidate["review_status"] = review.get("review_status", "pending")
            evidence = promote(candidate, review)
            if evidence:
                existing[candidate["candidate_id"]] = evidence
                promoted.append(evidence)
    write_jsonl(args.candidates, candidates)
    write_jsonl(args.evidence, list(existing.values()))
    write_reports(candidates, promoted, args.json_report, args.md_report, fx)
    print(f"Evidence review: {len(candidates)} candidates, {len(promoted)} promoted this run.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
