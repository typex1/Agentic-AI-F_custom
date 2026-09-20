"""CV Match workflow with Strands Agents.

Port of the Langdock workflow `jm_3.json`. The six Langdock nodes map to six
plain Python steps; the two agent nodes become Strands ``Agent`` calls with
``structured_output_model``.

    Langdock node                          here
    -------------------------------------  ------------------------------------
    1  form1   Form trigger (cv, jd, notes) argparse / run(cv_path, jd_path, notes)
    2  code2   Code "Read files"            cv_match.files.read_text
    3  agent   JD Requirement Extractor     cv_match.agents.extract_requirements  -> JobRequirements
    4  agent2  Assess CV per requirement    cv_match.agents.assess_cv             -> CVAssessment
    5  code    Code "Compute score"         cv_match.scoring.compute_score        -> ScoreResult
    6  output  Output "Report"              cv_match.report.render_report         -> Markdown

Usage:
    python workflow.py samples/CV_AI_engineer.txt samples/Job_Description_AI_engineer.txt
    python workflow.py cv.txt jd.txt --notes "must-have: German C1" --out report.md --json run.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

from cv_match.agents import DEFAULT_MODEL_ID, assess_cv, extract_requirements
from cv_match.files import read_text
from cv_match.report import render_report
from cv_match.scoring import compute_score


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def run(cv_path: str, jd_path: str, notes: str = "", model_id: str | None = None) -> dict:
    """Run all six steps and return the report plus every intermediate result."""
    t0 = time.time()

    # Step 2: Read files (step 1, the "form", is the function signature / CLI)
    log("[2/6] Reading files")
    cv_text = read_text(cv_path)
    jd_text = read_text(jd_path)

    # Step 3: Agent 1 with structured output -> JobRequirements
    log("[3/6] Extracting requirements from the job description (agent, structured output)")
    reqs = extract_requirements(jd_text, notes, model_id)
    log(f"      {len(reqs.requirements)} requirements for '{reqs.role_title}'")

    # Step 4: Agent 2 with structured output -> CVAssessment
    log("[4/6] Assessing the CV against every requirement (agent, structured output)")
    cva = assess_cv(reqs, cv_text, model_id)
    log(f"      {len(cva.assessments)} assessments for '{cva.candidate_name}'")

    # Step 5: deterministic scoring
    log("[5/6] Computing score")
    score = compute_score(reqs, cva)
    log(f"      overall {score.overall_score} %, must-haves {score.must_have_coverage} %, verdict {score.verdict}")

    # Step 6: report
    log("[6/6] Rendering report")
    report = render_report(reqs, cva, score)
    log(f"      done in {time.time() - t0:.1f} s")

    return {
        "inputs": {
            "cv": str(cv_path),
            "job_description": str(jd_path),
            "notes": notes,
            "model_id": model_id or DEFAULT_MODEL_ID,
        },
        "requirements": reqs.model_dump(),
        "assessment": cva.model_dump(),
        "score": score.model_dump(),
        "report_md": report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Match a CV against a job description with Strands Agents.")
    parser.add_argument("cv", help="Path to the CV (.txt)")
    parser.add_argument("job_description", help="Path to the job description (.txt)")
    parser.add_argument("--notes", default="", help='Extra recruiter constraints, e.g. "must-have: German C1"')
    parser.add_argument("--model-id", default=None, help="Bedrock model id (default: CV_MATCH_MODEL_ID env or amazon.nova-lite-v1:0)")
    parser.add_argument("--out", default=None, help="Write the Markdown report to this file")
    parser.add_argument("--json", default=None, help="Write all intermediate structured results to this JSON file")
    args = parser.parse_args()

    result = run(args.cv, args.job_description, args.notes, args.model_id)

    if args.out:
        Path(args.out).write_text(result["report_md"], encoding="utf-8")
        log(f"Report written to {args.out}")
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"Structured results written to {args.json}")

    print(result["report_md"])


if __name__ == "__main__":
    main()
