#!/usr/bin/env python3
"""
# Agentic Workflow: CV Match (compact, single-file version)

Same workflow as ``workflow.py`` but laid out exactly like the official Strands
blueprint ``agents_workflow.py`` (Research Assistant: Researcher -> Analyst -> Writer):

  https://github.com/strands-agents/harness-sdk/blob/main/site/docs/examples/python/agents_workflow.py

Read the two files side by side. Comments starting with ``BLUEPRINT:`` say what the
official example does at that point; ``OURS:`` says what we do differently and why.

## Workflow Process
1. Read files                  (plain Python)               BLUEPRINT has no such step
2. JD Requirement Extractor    (Agent, structured output)   ~ Researcher Agent
3. CV Assessor                 (Agent, structured output)   ~ Analyst Agent
4. Compute score               (plain Python)               BLUEPRINT has no such step
5. Render report               (plain Python template)      ~ Writer Agent

## How to Run
    python workflow_compact.py samples/CV_AI_engineer.txt samples/Job_Description_AI_engineer.txt
"""

import json
import sys
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel

# OURS: the only imports from our package. The blueprint needs none because it
# passes plain strings between agents; we pass validated objects, so the two
# Pydantic schemas are the one thing that must live outside this file.
from cv_match.prompts import (
    ASSESSOR_SYSTEM_PROMPT,
    EXTRACTOR_SYSTEM_PROMPT,
)
from cv_match.schemas import CVAssessment, JobRequirements

# MODEL_ID = "global.anthropic.claude-sonnet-4-6"
MODEL_ID = "amazon.nova-lite-v1:0"


def run_cv_match_workflow(cv_path: str, jd_path: str, notes: str = "") -> str:
    """
    Run a two-agent workflow that matches a CV against a job description.
    Shows progress logs during execution but presents only the final report to the user.

    BLUEPRINT: run_research_workflow(user_input) -> final_report. One function,
    agents created inline, called in a fixed order decided by code (no Graph/Swarm).
    OURS: identical shape. Two more arguments because the inputs are files.
    """
    print(f"\nProcessing: '{Path(cv_path).name}' against '{Path(jd_path).name}'")

    # Step 1: Read files
    # BLUEPRINT: none, the user types the input.
    # OURS: Langdock needed a Code node for this; in Python it is one line each.
    print("\nStep 1: Reading the two text files...")
    cv_text = Path(cv_path).read_text(encoding="utf-8", errors="replace")
    jd_text = Path(jd_path).read_text(encoding="utf-8", errors="replace")

    # Step 2: JD Requirement Extractor Agent
    # BLUEPRINT: Agent(system_prompt=..., callback_handler=None, tools=[http_request])
    #            researcher_response = researcher_agent(f"Research: '{user_input}' ...")
    #            research_findings = str(researcher_response)          <- plain text
    # OURS:      same construction, no tools, low temperature, and the call carries
    #            structured_output_model=JobRequirements. Instead of str(response) we
    #            take response.structured_output, a validated JobRequirements object.
    print("Step 2: JD Requirement Extractor Agent reading the job description...")
    extractor_agent = Agent(
        system_prompt=EXTRACTOR_SYSTEM_PROMPT,
        model=BedrockModel(model_id=MODEL_ID, temperature=0.1, max_tokens=8000),
        callback_handler=None,
    )
    extractor_response = extractor_agent(
        f"Additional constraints from the recruiter (may be empty): {notes or 'none'}\n\n"
        f'JOB DESCRIPTION:\n"""\n{jd_text}\n"""',
        structured_output_model=JobRequirements,
    )
    requirements: JobRequirements = extractor_response.structured_output
    print(f"Extraction complete: {len(requirements.requirements)} requirements for '{requirements.role_title}'")
    print("Passing requirements to CV Assessor Agent...\n")

    # Step 3: CV Assessor Agent
    # BLUEPRINT: analyst_agent(f"Analyze these findings about '{user_input}':\n\n{research_findings}")
    #            analysis = str(analyst_response)
    # OURS:      the previous stage's *object* is serialised into the prompt with
    #            model_dump (the blueprint pastes the previous agent's prose), and the
    #            answer is again a typed object: CVAssessment.
    print("Step 3: CV Assessor Agent rating every requirement...")
    assessor_agent = Agent(
        system_prompt=ASSESSOR_SYSTEM_PROMPT,
        model=BedrockModel(model_id=MODEL_ID, temperature=0.1, max_tokens=8000),
        callback_handler=None,
    )
    requirements_json = json.dumps(
        [r.model_dump(include={"id", "text", "category", "priority"}) for r in requirements.requirements],
        indent=1,
        ensure_ascii=False,
    )
    assessor_response = assessor_agent(
        f'Requirements (JSON):\n{requirements_json}\n\nCV:\n"""\n{cv_text}\n"""',
        structured_output_model=CVAssessment,
    )
    assessment: CVAssessment = assessor_response.structured_output
    print(f"Assessment complete: {len(assessment.assessments)} ratings for '{assessment.candidate_name}'")
    print("Passing structured results to the scoring step...\n")

    # Step 4: Compute score
    # BLUEPRINT: none. Every stage is an LLM.
    # OURS:      the model judged, now the code counts. Possible only because the two
    #            previous results are typed objects with guaranteed fields and ranges.
    print("Step 4: Computing the weighted score...")
    by_id = {a.requirement_id: a for a in assessment.assessments}
    total_w = got_w = must_total = must_met = 0
    must_missing: list[str] = []
    rows: list[str] = []
    for r in requirements.requirements:
        a = by_id.get(r.id)
        f = a.fulfilment if a else 0
        total_w += r.weight * 3
        got_w += r.weight * f
        if r.priority == "must":
            must_total += 1
            if f >= 2:
                must_met += 1
            else:
                must_missing.append(r.text)
        evidence = (a.evidence if a else "").replace("|", "/").replace("\n", " ")
        rows.append(f"| {r.id} | {r.text} | {r.category} | {r.priority} | {r.weight} | {f}/3 | {evidence} |")
    overall = round(100 * got_w / total_w) if total_w else 0
    must_rate = round(100 * must_met / must_total) if must_total else 100
    if must_total and must_rate < 100:
        verdict = "review" if overall >= 60 else "weak"
    else:
        verdict = "strong" if overall >= 75 else "review" if overall >= 50 else "weak"
    print(f"Score complete: {overall} % overall, {must_rate} % must-haves, verdict {verdict}")

    # Step 5: Report
    # BLUEPRINT: writer_agent = Agent(system_prompt=...)  <- default callback handler,
    #            so the third LLM call streams the report to the terminal.
    # OURS:      a deterministic template (like the Langdock Output node). No third
    #            model call, so the numbers in the report are exactly the computed ones.
    print("Step 5: Rendering the report...")
    final_report = "\n".join(
        [
            f"## CV Match: {assessment.candidate_name} → {requirements.role_title}",
            "",
            f"**Overall match: {overall} %**  ·  Must-haves covered: {must_rate} %  ·  Verdict: {verdict}",
            "",
            "### Missing must-haves",
            "\n".join(f"- {m}" for m in must_missing) or "- none",
            "",
            "### Requirement matrix",
            "| ID | Requirement | Category | Priority | Weight | Score | Evidence |",
            "|---|---|---|---|---|---|---|",
            *rows,
            "",
            "### Additional strengths not asked for",
            "\n".join(f"- {s}" for s in assessment.additional_strengths) or "- none",
        ]
    )
    print("Report creation complete\n")

    # BLUEPRINT: return final_report (an AgentResult that prints as text)
    # OURS:      return a str; the caller decides where it goes.
    return final_report


if __name__ == "__main__":
    # BLUEPRINT: interactive `input()` loop with a catch-all try/except.
    # OURS:      the inputs are two files, so they come from the command line, and we
    #            let exceptions (e.g. StructuredOutputException) surface unchanged so
    #            students see what went wrong.
    print("\nAgentic Workflow: CV Match (compact)\n")
    if len(sys.argv) < 3:
        print("Usage: python workflow_compact.py <cv.txt> <job_description.txt> [notes]")
        sys.exit(1)
    report = run_cv_match_workflow(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    print(report)
