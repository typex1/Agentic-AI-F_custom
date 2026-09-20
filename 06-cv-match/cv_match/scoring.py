"""Step 5: Compute score (port of the Langdock Code node `code`).

Design principle carried over from the Langdock workflow: the model judges,
the code counts. LLMs are decent at "does this CV cover this requirement?"
and bad at arithmetic, so the score is deterministic Python.

Compare this file with the original Code node: about half of that node was
``as_list_of_dicts`` / ``to_int`` defensive parsing, because the agent nodes
could return lists, JSON strings, or strings inside lists. Here the inputs are
already validated Pydantic objects, so that code disappears.
"""

from pydantic import BaseModel

from .schemas import CVAssessment, JobRequirements

# Tuning knobs (same values as the Langdock Code node)
MUST_COVERED_MIN_FULFILMENT = 2  # a must-have counts as covered at fulfilment 2 or 3
STRONG_THRESHOLD = 75
REVIEW_THRESHOLD = 50
REVIEW_WITH_GAP_THRESHOLD = 60


class MatrixRow(BaseModel):
    id: str
    requirement: str
    category: str
    priority: str
    weight: int
    fulfilment: int
    evidence: str
    comment: str


class ScoreResult(BaseModel):
    overall_score: int
    must_have_coverage: int
    must_have_missing: list[str]
    verdict: str
    category_scores: dict[str, int]
    matrix: list[MatrixRow]
    unassessed_ids: list[str]


def compute_score(reqs: JobRequirements, cva: CVAssessment) -> ScoreResult:
    # One cross-step check the Pydantic validators cannot do on their own: the
    # assessor's output must line up with the extractor's output. Missing ids
    # are scored 0 and reported, exactly like the Langdock Code node did.
    by_id = {a.requirement_id: a for a in cva.assessments}
    unassessed = [r.id for r in reqs.requirements if r.id not in by_id]

    rows: list[MatrixRow] = []
    total_w = got_w = 0
    must_total = must_met = 0
    must_missing: list[str] = []

    for r in reqs.requirements:
        a = by_id.get(r.id)
        f = a.fulfilment if a else 0
        total_w += r.weight * 3
        got_w += r.weight * f
        if r.priority == "must":
            must_total += 1
            if f >= MUST_COVERED_MIN_FULFILMENT:
                must_met += 1
            else:
                must_missing.append(r.text)
        rows.append(
            MatrixRow(
                id=r.id,
                requirement=r.text,
                category=r.category,
                priority=r.priority,
                weight=r.weight,
                fulfilment=f,
                evidence=a.evidence if a else "",
                comment=a.comment if a else "not assessed",
            )
        )

    overall = round(100 * got_w / total_w) if total_w else 0
    must_rate = round(100 * must_met / must_total) if must_total else 100

    # Verdict: hard gate on must-haves, then bands on the weighted score
    if must_total and must_rate < 100:
        verdict = "review" if overall >= REVIEW_WITH_GAP_THRESHOLD else "weak"
    else:
        verdict = "strong" if overall >= STRONG_THRESHOLD else "review" if overall >= REVIEW_THRESHOLD else "weak"

    # Per-category breakdown
    cats: dict[str, dict[str, int]] = {}
    for row in rows:
        c = cats.setdefault(row.category, {"got": 0, "max": 0})
        c["got"] += row.weight * row.fulfilment
        c["max"] += row.weight * 3
    category_scores = {k: round(100 * v["got"] / v["max"]) for k, v in sorted(cats.items()) if v["max"]}

    return ScoreResult(
        overall_score=overall,
        must_have_coverage=must_rate,
        must_have_missing=must_missing,
        verdict=verdict,
        category_scores=category_scores,
        matrix=rows,
        unassessed_ids=unassessed,
    )
