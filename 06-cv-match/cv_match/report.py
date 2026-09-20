"""Step 6: Render the Markdown report (port of the Langdock Output node `output`)."""

from .schemas import CVAssessment, JobRequirements
from .scoring import ScoreResult


def _cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")


def render_report(reqs: JobRequirements, cva: CVAssessment, score: ScoreResult) -> str:
    lines = [
        "| ID | Requirement | Category | Priority | Weight | Score | Evidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in score.matrix:
        lines.append(
            f"| {r.id} | {_cell(r.requirement)} | {r.category} | {r.priority} "
            f"| {r.weight} | {r.fulfilment}/3 | {_cell(r.evidence)} |"
        )
    matrix_md = "\n".join(lines)

    category_md = "\n".join(f"- {k}: {v} %" for k, v in score.category_scores.items())
    missing_md = "\n".join(f"- {m}" for m in score.must_have_missing) or "- none"
    strengths_md = "\n".join(f"- {s}" for s in cva.additional_strengths) or "- none"

    report = f"""## CV Match: {cva.candidate_name} → {reqs.role_title}

**Overall match: {score.overall_score} %**  ·  Must-haves covered: {score.must_have_coverage} %  ·  Verdict: {score.verdict}

### Missing must-haves
{missing_md}

### Scores by category
{category_md}

### Requirement matrix
{matrix_md}

### Additional strengths not asked for
{strengths_md}
"""
    if score.unassessed_ids:
        report += f"\n> Note: the assessor returned no rating for {', '.join(score.unassessed_ids)}; scored as 0.\n"
    return report
