#!/usr/bin/env python3
"""
validate.py — Unified validation for spec, PRD, and plan documents.

Usage:
    python validate.py <path> [--type spec|prd|plan] [--verbose] [--json] [--draft]

Doc type is auto-detected when --type is not provided.

Exit codes:
    0 — PASS (score >= threshold)
    1 — NEEDS WORK (score < threshold)

Thresholds:
    Default: 70
    --draft:  50
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Issue:
    severity: str  # "error" | "warning" | "info"
    category: str
    message: str
    line: int = 0


@dataclass
class ValidationReport:
    path: str
    doc_type: str = "unknown"
    threshold: int = 70
    issues: list[Issue] = field(default_factory=list)
    score: int = 100

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0 and self.score >= self.threshold


# ---------------------------------------------------------------------------
# Section detection helpers
# ---------------------------------------------------------------------------


def find_section(lines: list[str], pattern: str) -> tuple[int, int]:
    """Find a section by heading pattern. Returns (start_line, end_line) 0-indexed, or (0, 0)."""
    regex = re.compile(pattern, re.IGNORECASE)
    start = 0
    level = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not start and regex.match(stripped):
            start = i + 1
            level = len(stripped) - len(stripped.lstrip("#"))
            continue
        if start and stripped.startswith("#"):
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            if heading_level <= level:
                return (start, i)
    if start:
        return (start, len(lines))
    return (0, 0)


def section_content(lines: list[str], start: int, end: int) -> str:
    if start == 0:
        return ""
    return "\n".join(lines[start:end])


def count_subsections(lines: list[str], start: int, end: int) -> int:
    count = 0
    for line in lines[start:end]:
        if line.strip().startswith("#"):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

VAGUE_PHRASES = [
    r"\bTBD\b(?!\s*[-—:]\s*\w)",
    r"\bshould work\b",
    r"\bmight need\b",
    r"\bprobably\b",
    r"\bas needed\b",
    r"\betc\.?\b",
    r"\bsomehow\b",
    r"\bvarious\b",
    r"\bas appropriate\b",
    r"\bif necessary\b",
    r"\band so on\b",
    r"\bmaybe\b",
]

_FILE_EXTENSIONS = (
    "c|cc|cpp|cxx|h|hh|hpp|hxx"
    "|kt|java|gradle|scala|clj"
    "|py|pyi|pyx"
    "|ts|tsx|js|jsx|mjs|cjs"
    "|go|rs"
    "|rb|php|pl|pm"
    "|swift|m|mm"
    "|cs|fs|fsx"
    "|sh|bash|zsh|fish|ps1"
    "|sql|yaml|yml|json|jsonc|xml|toml|ini|cfg|conf|env"
    "|md|mdc|mdx|rst|txt|tex|adoc"
    "|html|htm|css|scss|sass|less|svelte|vue"
    "|tf|tfvars|hcl"
    "|cmake|meson|ninja|bazel"
    "|proto|graphql|gql|wasm|zig|nim|dart|ex|exs|erl|hrl|hs|lua|r|jl"
)

FILE_PATH_PATTERN = re.compile(
    r"(?:"
    rf"[`\"][\w./\-]+(?:\.(?:{_FILE_EXTENSIONS}))[`\"]"
    r"|"
    rf"(?:^|\s)[\w./\-]+(?:\.(?:{_FILE_EXTENSIONS}))(?:\s|$|[,;:\)])"
    r")"
)

VERIFICATION_KEYWORDS = re.compile(
    r"\b(?:test|tests|build|lint|verify|verification|validate|check|assert|gradle|pytest|npm run|jest|make)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Shared checks
# ---------------------------------------------------------------------------


def check_vague_language(lines: list[str], report: ValidationReport) -> None:
    hits = 0
    in_code_block = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or stripped.startswith("|"):
            continue
        for phrase_pattern in VAGUE_PHRASES:
            if re.search(phrase_pattern, line, re.IGNORECASE):
                if hits < 5:
                    found = re.search(phrase_pattern, line, re.IGNORECASE)
                    phrase_text = found.group() if found else phrase_pattern
                    report.issues.append(
                        Issue(
                            severity="warning",
                            category="vagueness",
                            message=f'Vague language: "{phrase_text}"',
                            line=i,
                        )
                    )
                hits += 1
    if hits > 0:
        report.score -= min(hits * 2, 10)


def check_oversized_code_blocks(lines: list[str], report: ValidationReport, doc_label: str = "Documents") -> None:
    in_block = False
    block_start = 0
    block_lines = 0

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```") and not in_block:
            in_block = True
            block_start = i
            block_lines = 0
        elif line.strip() == "```" and in_block:
            in_block = False
            if block_lines > 15:
                report.issues.append(
                    Issue(
                        severity="warning",
                        category="scope",
                        message=f"Code block at line {block_start} is {block_lines} lines. {doc_label} should describe behavior, not implement it.",
                        line=block_start,
                    )
                )
                report.score -= 3
        elif in_block:
            block_lines += 1


# ===========================================================================
# SPEC VALIDATION
# ===========================================================================


def spec_check_problem_statement(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+problem\s+statement")
    if s == 0:
        report.issues.append(
            Issue(severity="error", category="structure", message="No Problem Statement section found.")
        )
        report.score -= 15
    else:
        body = section_content(lines, s, e).strip()
        if len(body) < 20:
            report.issues.append(
                Issue(severity="error", category="structure", message="Problem Statement is too brief (< 20 chars).", line=s)
            )
            report.score -= 10


def spec_check_acceptance_criteria(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+acceptance\s+criteria")
    if s == 0:
        report.issues.append(
            Issue(severity="error", category="structure", message="No Acceptance Criteria section found.")
        )
        report.score -= 15
        return


def spec_check_given_when_then(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+acceptance\s+criteria")
    if s == 0:
        return
    body = section_content(lines, s, e)
    # Check single-line GWT or multi-line (Given on one line, When on next, Then on next)
    gwt = re.findall(r"\bgiven\b.*\bwhen\b.*\bthen\b", body, re.IGNORECASE | re.DOTALL)
    if not gwt:
        # Also check for separate Given/When/Then keywords across lines
        has_given = bool(re.search(r"^\s*given\b", body, re.IGNORECASE | re.MULTILINE))
        has_when = bool(re.search(r"^\s*when\b", body, re.IGNORECASE | re.MULTILINE))
        has_then = bool(re.search(r"^\s*then\b", body, re.IGNORECASE | re.MULTILINE))
        if has_given and has_when and has_then:
            return  # Multi-line GWT format detected
    if not gwt:
        report.issues.append(
            Issue(
                severity="warning",
                category="format",
                message="No Given/When/Then format detected in Acceptance Criteria.",
                line=s,
            )
        )
        report.score -= 5


def spec_check_ac_no_and(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+acceptance\s+criteria")
    if s == 0:
        return
    hits = 0
    # Look for "then ... and [verb] ..." patterns — two distinct actions joined by "and"
    ac_pattern = re.compile(r"\bthen\b(.+)", re.IGNORECASE)
    # "and" followed by a verb phrase (subject + verb or bare verb) suggests two behaviors
    and_two_behaviors = re.compile(
        r"\band\s+(?:(?:they|it|the\s+\w+|a\s+\w+)\s+)?(?:is|are|return|redirect|send|creat|updat|delet|log|sav|set|get|receiv|trigger|emit|notif|dispatch|render|display|show)",
        re.IGNORECASE,
    )
    for i in range(s, e):
        line = lines[i]
        m = ac_pattern.search(line)
        if m:
            then_clause = m.group(1)
            if and_two_behaviors.search(then_clause):
                if hits < 3:
                    report.issues.append(
                        Issue(
                            severity="warning",
                            category="format",
                            message='AC uses "and" to join behaviors — split into separate ACs.',
                            line=i + 1,
                        )
                    )
                hits += 1
    if hits > 0:
        report.score -= min(hits * 3, 9)


def spec_check_vertical_slices(lines: list[str], report: ValidationReport) -> None:
    """Warn if no vertical slices found (FEATURE-size specs should have them)."""
    content = "\n".join(lines)
    has_slices = bool(re.search(r"(?:slice|vertical\s+slice)\s+\d", content, re.IGNORECASE))
    if not has_slices:
        # Also check for "## Slice" headings
        has_slices = bool(re.search(r"^#{1,3}\s+slice\s+\d", content, re.IGNORECASE | re.MULTILINE))
    if not has_slices:
        report.issues.append(
            Issue(
                severity="warning",
                category="structure",
                message="No Vertical Slices detected. FEATURE-size specs should organize ACs into vertical slices.",
            )
        )
        report.score -= 5


def spec_check_architecture_placeholder(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+architecture\s+recommendation")
    if s == 0:
        return  # Section absent is fine for SMALL specs
    body = section_content(lines, s, e).strip()
    if "_To be filled by architecture-advisor_" in body or len(body) < 10:
        report.issues.append(
            Issue(
                severity="warning",
                category="completeness",
                message="Architecture Recommendation is a placeholder. Run architecture-advisor to fill it.",
                line=s,
            )
        )
        report.score -= 3


def spec_check_tdd_placeholder(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+tdd\s+plan")
    if s == 0:
        return
    body = section_content(lines, s, e).strip()
    if "_To be filled by tdd-planner_" in body or len(body) < 10:
        report.issues.append(
            Issue(
                severity="warning",
                category="completeness",
                message="TDD Plan is a placeholder. Run tdd-planner to fill it.",
                line=s,
            )
        )
        report.score -= 3


def spec_check_risk_depth(lines: list[str], report: ValidationReport) -> None:
    content_lower = "\n".join(lines).lower()
    # Only flag if the spec mentions HIGH risk
    if "high" not in content_lower:
        return
    risk_keywords = ["edge case", "failure mode", "rollback", "fail safe", "fail-safe"]
    found = sum(1 for kw in risk_keywords if kw in content_lower)
    if found == 0:
        report.issues.append(
            Issue(
                severity="warning",
                category="completeness",
                message="HIGH risk spec should mention edge cases, failure modes, or rollback paths.",
            )
        )
        report.score -= 5


def validate_spec(path: Path, draft: bool = False) -> ValidationReport:
    threshold = 50 if draft else 70
    report = ValidationReport(path=str(path), doc_type="spec", threshold=threshold)

    if not path.exists():
        report.issues.append(Issue(severity="error", category="io", message=f"File not found: {path}"))
        report.score = 0
        return report

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        report.issues.append(Issue(severity="error", category="io", message=f"Cannot read file: {exc}"))
        report.score = 0
        return report

    lines = content.splitlines()

    spec_check_problem_statement(lines, report)
    spec_check_acceptance_criteria(lines, report)
    spec_check_given_when_then(lines, report)
    spec_check_ac_no_and(lines, report)
    spec_check_vertical_slices(lines, report)
    spec_check_architecture_placeholder(lines, report)
    spec_check_tdd_placeholder(lines, report)
    spec_check_risk_depth(lines, report)
    check_vague_language(lines, report)
    check_oversized_code_blocks(lines, report, "Specs")

    report.score = max(0, report.score)
    return report


# ===========================================================================
# PRD VALIDATION
# ===========================================================================


def prd_check_problem_statement(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:problem\s+statement|problem|the\s+problem)")
    if s == 0:
        report.issues.append(
            Issue(severity="error", category="structure", message="No problem statement section found.")
        )
        report.score -= 15
    else:
        body = section_content(lines, s, e).strip()
        if len(body) < 20:
            report.issues.append(
                Issue(severity="error", category="structure", message="Problem statement is too brief.", line=s)
            )
            report.score -= 10


def prd_check_personas_section(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:user\s+personas?|personas?|target\s+users?)")
    if s == 0:
        report.issues.append(
            Issue(severity="error", category="structure", message="No user personas section found.")
        )
        report.score -= 10
        return
    body = section_content(lines, s, e).strip()
    if len(body) < 20:
        report.issues.append(
            Issue(severity="error", category="structure", message="User personas section is too brief.", line=s)
        )
        report.score -= 10


def prd_check_persona_detail(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:user\s+personas?|personas?|target\s+users?)")
    if s == 0:
        return
    body = section_content(lines, s, e).lower()
    if not re.search(r"\bgoals?\b", body):
        report.issues.append(
            Issue(severity="warning", category="completeness", message="Personas section does not mention user goals.", line=s)
        )
        report.score -= 3
    if not re.search(r"\bpain\s+points?\b|\bfrustrat|\bchalleng|\bstruggl", body):
        report.issues.append(
            Issue(severity="warning", category="completeness", message="Personas section does not mention pain points.", line=s)
        )
        report.score -= 3


def prd_check_functional_requirements(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(
        lines, r"^#{1,3}\s+(?:functional\s+requirements?|requirements?|features?|feature\s+requirements?)"
    )
    if s == 0:
        report.issues.append(
            Issue(severity="error", category="structure", message="No functional requirements section found.")
        )
        report.score -= 15
    else:
        body = section_content(lines, s, e).strip()
        if len(body) < 20:
            report.issues.append(
                Issue(severity="error", category="structure", message="Functional requirements section is too brief.", line=s)
            )
            report.score -= 10


def prd_check_requirement_ids(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    req_ids = re.findall(r"\bFR-\d{3}\b", content)
    if not req_ids:
        alt_ids = re.findall(r"\b(?:REQ|FEAT|US)-\d{3}\b", content)
        if not alt_ids:
            report.issues.append(
                Issue(severity="warning", category="specificity", message="No requirement IDs found (expected FR-001 format).")
            )
            report.score -= 5


def prd_check_acceptance_criteria(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines).lower()
    has_ac = bool(
        re.search(r"acceptance\s+criteria", content)
        or re.search(r"\bdone\s+when\b", content)
        or re.search(r"\bverif(?:y|ication)\b.*\brequirement", content)
    )
    req_ids = re.findall(r"\bFR-\d{3}\b", "\n".join(lines))
    if not has_ac and len(req_ids) > 0:
        report.issues.append(
            Issue(severity="warning", category="completeness", message="No acceptance criteria found for requirements.")
        )
        report.score -= 8
    elif not has_ac and len(req_ids) == 0:
        report.issues.append(
            Issue(severity="warning", category="completeness", message="No acceptance criteria found.")
        )
        report.score -= 5


def prd_check_nonfunctional_requirements(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(
        lines, r"^#{1,3}\s+(?:non-?functional\s+requirements?|nfrs?|quality\s+attributes?|system\s+requirements?)"
    )
    if s == 0:
        content = "\n".join(lines).lower()
        nfr_keywords = ["performance", "scalability", "security", "reliability", "accessibility"]
        found = sum(1 for kw in nfr_keywords if kw in content)
        if found < 2:
            report.issues.append(
                Issue(severity="warning", category="structure", message="No non-functional requirements section found.")
            )
            report.score -= 5


def prd_check_scope_boundary(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:scope|scope\s+boundary)")
    content_lower = "\n".join(lines).lower()
    if s == 0:
        has_scope = "in scope" in content_lower or "in-scope" in content_lower
        has_out = "out of scope" in content_lower or "out-of-scope" in content_lower
        if not has_scope and not has_out:
            report.issues.append(
                Issue(severity="error", category="structure", message="No scope boundary found.")
            )
            report.score -= 10
        elif not has_out:
            report.issues.append(
                Issue(severity="warning", category="completeness", message="In-scope items found but no out-of-scope exclusions.")
            )
            report.score -= 5
    else:
        body = section_content(lines, s, e).lower()
        if not any(p in body for p in ["out of scope", "out-of-scope", "not included", "excluded"]):
            report.issues.append(
                Issue(severity="warning", category="completeness", message="Scope section exists but no out-of-scope exclusions.", line=s)
            )
            report.score -= 5


def prd_check_dependencies(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:dependenc(?:y|ies)|external\s+dependenc|blockers?)")
    if s == 0:
        content_lower = "\n".join(lines).lower()
        if not any(p in content_lower for p in ["depends on", "dependency", "blocked by"]):
            report.issues.append(
                Issue(severity="warning", category="structure", message="No dependencies section found.")
            )
            report.score -= 3


def prd_check_milestones(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:milestones?|phases?|delivery\s+phases?|release\s+plan|rollout)")
    if s == 0:
        content = "\n".join(lines)
        has_phases = bool(re.search(r"\bphase\s+\d\b|\bP\d+-[A-Z]\b|\bmilestone\s+\d\b", content, re.IGNORECASE))
        if not has_phases:
            report.issues.append(
                Issue(severity="warning", category="structure", message="No milestones or phases section found.")
            )
            report.score -= 5


def prd_check_milestone_deliverables(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:milestones?|phases?|delivery\s+phases?|release\s+plan|rollout)")
    if s == 0:
        return
    body = section_content(lines, s, e).lower()
    has_deliverable = bool(
        re.search(r"\bdeliver(?:able|s)\b", body)
        or re.search(r"\boutcome\b", body)
        or re.search(r"\bresult(?:s|ing)?\b", body)
        or re.search(r"\busers?\s+can\b", body)
    )
    if not has_deliverable:
        report.issues.append(
            Issue(severity="warning", category="completeness", message="Milestones section does not describe deliverables.", line=s)
        )
        report.score -= 3


def prd_check_success_metrics(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(
        lines, r"^#{1,3}\s+(?:success\s+metrics?|metrics?|kpis?|success\s+criteria|how\s+we.ll\s+measure)"
    )
    if s == 0:
        content_lower = "\n".join(lines).lower()
        has_metrics = bool(
            re.search(r"\bmeasur(?:e|able|ement)\b", content_lower)
            or re.search(r"\bmetric\b", content_lower)
            or re.search(r"\bkpi\b", content_lower)
        )
        if not has_metrics:
            report.issues.append(
                Issue(severity="warning", category="structure", message="No success metrics found.")
            )
            report.score -= 5
    else:
        body = section_content(lines, s, e).strip()
        if len(body) < 15:
            report.issues.append(
                Issue(severity="warning", category="completeness", message="Success metrics section is too brief.", line=s)
            )
            report.score -= 3


def prd_check_open_questions(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:open\s+questions?|unresolved|unknowns?|questions?)")
    if s == 0:
        report.issues.append(
            Issue(severity="info", category="structure", message="No open questions section found.")
        )


def prd_check_requirement_id_consistency(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    fr_ids = re.findall(r"\bFR-(\d{3})\b", content)
    if fr_ids:
        nums = sorted(set(int(n) for n in fr_ids))
        if len(nums) > 1:
            for i in range(1, len(nums)):
                if nums[i] - nums[i - 1] > 1:
                    report.issues.append(
                        Issue(
                            severity="info",
                            category="consistency",
                            message=f"Gap in requirement IDs: FR-{nums[i-1]:03d} to FR-{nums[i]:03d}.",
                        )
                    )
                    break
    alt_formats = re.findall(r"\b(?:REQ|FEAT|US)-\d{3}\b", content)
    if fr_ids and alt_formats:
        report.issues.append(
            Issue(severity="warning", category="consistency", message="Mixed requirement ID formats found.")
        )
        report.score -= 3


def prd_check_implementation_leakage(lines: list[str], report: ValidationReport) -> None:
    hits = 0
    in_code_block = False
    files_heading_re = re.compile(
        r"^\*{0,2}files?\s+to\s+(?:change|modify|update|edit)\*{0,2}\s*:?\s*$", re.IGNORECASE
    )
    source_path_re = re.compile(
        r"(?:^|\s)(?:`)?(?:src|apps|packages|components|internal|cmd|lib|libs|services)/\S+\.\w{1,4}(?:`)?"
    )
    line_ref_re = re.compile(r"\(lines?\s+\d+|:\s*line\s+\d+|\(lines?\s+\d+[\s,\-]+\d+", re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if files_heading_re.match(stripped):
            if hits < 5:
                report.issues.append(
                    Issue(severity="warning", category="abstraction", message='"Files to change" section belongs in PLAN.md, not the PRD.', line=i)
                )
            hits += 1
        elif source_path_re.search(line):
            if hits < 5:
                report.issues.append(
                    Issue(severity="warning", category="abstraction", message="Source code file path detected. Belongs in PLAN.md.", line=i)
                )
            hits += 1
        elif line_ref_re.search(line):
            if hits < 5:
                report.issues.append(
                    Issue(severity="warning", category="abstraction", message="Line number reference detected. Belongs in PLAN.md.", line=i)
                )
            hits += 1
    if hits > 0:
        report.score -= min(hits * 3, 10)


def validate_prd(path: Path, draft: bool = False) -> ValidationReport:
    threshold = 50 if draft else 70
    report = ValidationReport(path=str(path), doc_type="prd", threshold=threshold)

    if not path.exists():
        report.issues.append(Issue(severity="error", category="io", message=f"File not found: {path}"))
        report.score = 0
        return report

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        report.issues.append(Issue(severity="error", category="io", message=f"Cannot read file: {exc}"))
        report.score = 0
        return report

    lines = content.splitlines()

    prd_check_problem_statement(lines, report)
    prd_check_personas_section(lines, report)
    prd_check_persona_detail(lines, report)
    prd_check_functional_requirements(lines, report)
    prd_check_requirement_ids(lines, report)
    prd_check_acceptance_criteria(lines, report)
    prd_check_nonfunctional_requirements(lines, report)
    prd_check_scope_boundary(lines, report)
    prd_check_dependencies(lines, report)
    prd_check_milestones(lines, report)
    prd_check_milestone_deliverables(lines, report)
    check_vague_language(lines, report)
    check_oversized_code_blocks(lines, report, "PRDs")
    prd_check_success_metrics(lines, report)
    prd_check_open_questions(lines, report)
    prd_check_requirement_id_consistency(lines, report)
    prd_check_implementation_leakage(lines, report)

    report.score = max(0, report.score)
    return report


# ===========================================================================
# PLAN VALIDATION
# ===========================================================================


def plan_check_target_repos(lines: list[str], report: ValidationReport) -> None:
    s, e = find_section(lines, r"^#{1,3}\s+(?:target\s+repo|repos|repository|directories)")
    if s == 0:
        header = "\n".join(lines[:30])
        if not re.search(r"(?:repo|repository|~/|src/)", header, re.IGNORECASE):
            report.issues.append(
                Issue(severity="error", category="structure", message="No target repo or directory identified.")
            )
            report.score -= 15
    else:
        body = section_content(lines, s, e)
        if len(body.strip()) < 5:
            report.issues.append(
                Issue(severity="error", category="structure", message="Target repo section is empty.", line=s)
            )
            report.score -= 15


def plan_check_files_to_modify(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    file_refs = FILE_PATH_PATTERN.findall(content)
    if len(file_refs) < 2:
        report.issues.append(
            Issue(
                severity="error",
                category="specificity",
                message=f"Only {len(file_refs)} file path(s) found. Plans must list specific files.",
            )
        )
        report.score -= 15


def plan_check_ordered_steps(lines: list[str], report: ValidationReport) -> None:
    step_pattern = re.compile(r"^#{1,4}\s+step\s+\d", re.IGNORECASE)
    numbered_pattern = re.compile(r"^\s*\d+\.\s+")
    has_steps = any(step_pattern.match(line.strip()) or numbered_pattern.match(line) for line in lines)
    if not has_steps:
        report.issues.append(
            Issue(severity="error", category="structure", message="No ordered implementation steps found.")
        )
        report.score -= 15


def plan_check_steps_reference_files(lines: list[str], report: ValidationReport) -> None:
    step_pattern = re.compile(r"^#{1,4}\s+step\s+(\d+)", re.IGNORECASE)
    current_step = None
    step_start = 0
    steps_without_files = []

    for i, line in enumerate(lines):
        match = step_pattern.match(line.strip())
        if match:
            if current_step is not None:
                step_body = "\n".join(lines[step_start:i])
                if not FILE_PATH_PATTERN.search(step_body):
                    steps_without_files.append(current_step)
            current_step = match.group(1)
            step_start = i

    if current_step is not None:
        step_body = "\n".join(lines[step_start:])
        if not FILE_PATH_PATTERN.search(step_body):
            steps_without_files.append(current_step)

    for step_num in steps_without_files:
        report.issues.append(
            Issue(severity="warning", category="specificity", message=f"Step {step_num} does not reference any file paths.")
        )
        report.score -= 3


def plan_check_risks_section(lines: list[str], report: ValidationReport) -> None:
    rs, re_ = find_section(lines, r"^#{1,3}\s+(?:risks?|assumptions?|risks?\s+and\s+assumptions?)")
    if rs == 0:
        report.issues.append(Issue(severity="warning", category="structure", message="No risks or assumptions section found."))
        report.score -= 5
    else:
        body = section_content(lines, rs, re_)
        if len(body.strip()) < 10:
            report.issues.append(
                Issue(severity="warning", category="structure", message="Risks section is nearly empty.", line=rs)
            )
            report.score -= 5


def plan_check_verification_section(lines: list[str], report: ValidationReport) -> None:
    vs, ve = find_section(lines, r"^#{1,3}\s+(?:verification|verify|testing|test\s+plan)")
    if vs == 0:
        content = "\n".join(lines)
        if not VERIFICATION_KEYWORDS.search(content):
            report.issues.append(
                Issue(severity="warning", category="structure", message="No verification steps found.")
            )
            report.score -= 5
    else:
        body = section_content(lines, vs, ve)
        if len(body.strip()) < 10:
            report.issues.append(
                Issue(severity="warning", category="structure", message="Verification section is nearly empty.", line=vs)
            )
            report.score -= 5


def plan_check_scope_boundary(lines: list[str], report: ValidationReport) -> None:
    content_lower = "\n".join(lines).lower()
    scope_phrases = ["out of scope", "not included", "excluded", "will not", "does not include"]
    if not any(phrase in content_lower for phrase in scope_phrases):
        report.issues.append(
            Issue(severity="info", category="scope", message="No explicit scope exclusions found.")
        )


def plan_check_traceability_table(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    has_traceability = (
        re.search(r"^#{1,3}\s+traceability", content, re.IGNORECASE | re.MULTILINE)
        or re.search(r"discovery\s+finding\s*\|\s*plan\s+step", content, re.IGNORECASE)
    )
    if not has_traceability:
        report.issues.append(
            Issue(severity="warning", category="traceability", message="No traceability table found.")
        )
        report.score -= 5


def plan_check_testable_outcomes(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    if not VERIFICATION_KEYWORDS.search(content):
        report.issues.append(
            Issue(severity="warning", category="verification", message="No test, build, or verification commands found.")
        )
        report.score -= 5


def plan_check_step_file_specificity(lines: list[str], report: ValidationReport) -> None:
    numbered_step = re.compile(r"^\s*(\d+)\.\s+(.+)$")
    vague_step_phrases = re.compile(
        r"\b(?:update the (?:config|code|file|database|model|service)|"
        r"modify (?:the )?(?:config|settings|code)|"
        r"change (?:the )?(?:config|code|logic))\b",
        re.IGNORECASE,
    )
    vague_steps = []
    for i, line in enumerate(lines, 1):
        m = numbered_step.match(line)
        if m:
            step_text = m.group(2)
            if vague_step_phrases.search(step_text) and not FILE_PATH_PATTERN.search(step_text):
                vague_steps.append((i, m.group(1), step_text[:80]))

    for lineno, step_num, text in vague_steps[:3]:
        report.issues.append(
            Issue(severity="warning", category="specificity", message=f'Step {step_num} uses vague language: "{text}..."', line=lineno)
        )
        report.score -= 3


def plan_check_per_step_verification(lines: list[str], report: ValidationReport) -> None:
    step_sections = []
    step_pattern = re.compile(r"^#{1,4}\s+step\s+(\d+)", re.IGNORECASE)
    current_step = None
    step_start = 0

    for i, line in enumerate(lines):
        m = step_pattern.match(line.strip())
        if m:
            if current_step is not None:
                step_sections.append((current_step, step_start, i))
            current_step = m.group(1)
            step_start = i

    if current_step is not None:
        step_sections.append((current_step, step_start, len(lines)))

    if not step_sections:
        return

    steps_missing = []
    for step_num, start, end in step_sections:
        body = "\n".join(lines[start:end])
        if not VERIFICATION_KEYWORDS.search(body):
            steps_missing.append(step_num)

    if len(steps_missing) > len(step_sections) // 2:
        report.issues.append(
            Issue(
                severity="warning",
                category="verification",
                message=f"Steps {', '.join(steps_missing[:5])} lack per-step verification.",
            )
        )
        report.score -= 5


def plan_check_structure_section(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    has_structure = bool(
        re.search(r"^#{1,3}\s+(?:structure|phases?|phase\s+breakdown|phase\s+ordering|dependency)", content, re.IGNORECASE | re.MULTILINE)
        or re.search(r"\bphase\s+\d+\b|\bP\d+\b", content)
        or re.search(r"depends?\s+on\s+(?:phase|step|P\d)", content, re.IGNORECASE)
    )
    if not has_structure:
        report.issues.append(
            Issue(severity="warning", category="structure", message="No structure section found (phase breakdown or dependency ordering).")
        )
        report.score -= 5


def plan_check_git_branch(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    has_branch = bool(
        re.search(r"\b(?:feature|fix|refactor|chore|docs|hotfix|release)/[\w\-/]+", content)
        or re.search(r"branch[:\s]+`?[\w/\-]+`?", content, re.IGNORECASE)
        or re.search(r"^#{1,3}\s+git\s+(?:strategy|branch|workflow)", content, re.IGNORECASE | re.MULTILINE)
    )
    if not has_branch:
        report.issues.append(
            Issue(severity="warning", category="git", message="No branch name found.")
        )
        report.score -= 5


def plan_check_git_commit_plan(lines: list[str], report: ValidationReport) -> None:
    content = "\n".join(lines)
    has_commits = bool(
        re.search(r"\b(?:feat|fix|refactor|chore|docs|test|perf|ci)\(", content)
        or re.search(r"commit\s+message", content, re.IGNORECASE)
    )
    has_pr = bool(
        re.search(r"\bpr\s+(?:title|description|body)\b", content, re.IGNORECASE)
        or re.search(r"pull\s+request", content, re.IGNORECASE)
        or re.search(r"^#{1,4}\s+pr\b", content, re.IGNORECASE | re.MULTILINE)
    )
    if not has_commits:
        report.issues.append(
            Issue(severity="warning", category="git", message="No commit messages found.")
        )
        report.score -= 5
    if not has_pr:
        report.issues.append(
            Issue(severity="warning", category="git", message="No PR title or description found.")
        )
        report.score -= 3


def validate_plan(path: Path) -> ValidationReport:
    report = ValidationReport(path=str(path), doc_type="plan")

    if not path.exists():
        report.issues.append(Issue(severity="error", category="io", message=f"File not found: {path}"))
        report.score = 0
        return report

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        report.issues.append(Issue(severity="error", category="io", message=f"Cannot read file: {exc}"))
        report.score = 0
        return report

    lines = content.splitlines()

    plan_check_target_repos(lines, report)
    plan_check_files_to_modify(lines, report)
    plan_check_ordered_steps(lines, report)
    plan_check_steps_reference_files(lines, report)
    plan_check_risks_section(lines, report)
    plan_check_verification_section(lines, report)
    check_vague_language(lines, report)
    check_oversized_code_blocks(lines, report, "Plans")
    plan_check_scope_boundary(lines, report)
    plan_check_traceability_table(lines, report)
    plan_check_testable_outcomes(lines, report)
    plan_check_step_file_specificity(lines, report)
    plan_check_per_step_verification(lines, report)
    plan_check_structure_section(lines, report)
    plan_check_git_branch(lines, report)
    plan_check_git_commit_plan(lines, report)

    report.score = max(0, report.score)
    return report


# ===========================================================================
# Doc type auto-detection
# ===========================================================================


def detect_doc_type(path: Path) -> str:
    name = path.name.lower()
    if "prd" in name:
        return "prd"
    if "plan" in name:
        return "plan"
    if "spec" in name:
        return "spec"

    try:
        content = path.read_text(encoding="utf-8").lower()
    except Exception:
        return "spec"  # default

    # Heuristic: count signature phrases
    prd_signals = sum(1 for p in ["user persona", "functional requirement", "success metric", "fr-"] if p in content)
    plan_signals = sum(1 for p in ["target repo", "implementation step", "git strategy", "traceability"] if p in content)
    spec_signals = sum(1 for p in ["acceptance criteria", "given", "when", "then", "vertical slice"] if p in content)

    scores = {"prd": prd_signals, "plan": plan_signals, "spec": spec_signals}
    return max(scores, key=scores.get)  # type: ignore[arg-type]


# ===========================================================================
# Report rendering
# ===========================================================================


def render_text(report: ValidationReport, verbose: bool = False) -> str:
    out = []
    status = "PASS" if report.passed else "NEEDS WORK"
    mode = " (draft mode)" if report.threshold < 70 else ""
    label = report.doc_type.upper()
    out.append(f"{'=' * 60}")
    out.append(f"{label} Validation: {status}{mode}")
    out.append(f"File: {report.path}")
    out.append(f"Score: {max(0, report.score)}/100 (threshold: {report.threshold})")
    out.append(f"{'=' * 60}")

    if report.errors:
        out.append(f"\nERRORS ({len(report.errors)}):")
        for issue in report.errors:
            loc = f" [line {issue.line}]" if issue.line else ""
            out.append(f"  [ERROR] [{issue.category}]{loc} {issue.message}")

    if report.warnings:
        out.append(f"\nWARNINGS ({len(report.warnings)}):")
        for issue in report.warnings:
            loc = f" [line {issue.line}]" if issue.line else ""
            out.append(f"  [WARN]  [{issue.category}]{loc} {issue.message}")

    infos = [i for i in report.issues if i.severity == "info"]
    if verbose and infos:
        out.append(f"\nINFO ({len(infos)}):")
        for issue in infos:
            out.append(f"  [INFO]  [{issue.category}] {issue.message}")

    if not report.issues:
        out.append("\nNo issues found.")

    return "\n".join(out)


def render_json(report: ValidationReport) -> str:
    data = {
        "path": report.path,
        "doc_type": report.doc_type,
        "passed": report.passed,
        "score": max(0, report.score),
        "threshold": report.threshold,
        "issues": [
            {
                "severity": i.severity,
                "category": i.category,
                "message": i.message,
                "line": i.line or None,
            }
            for i in report.issues
        ],
        "error_count": len(report.errors),
        "warning_count": len(report.warnings),
    }
    return json.dumps(data, indent=2)


# ===========================================================================
# Main
# ===========================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a spec, PRD, or plan document for structural completeness.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("path", help="Path to the document to validate")
    parser.add_argument(
        "--type", choices=["spec", "prd", "plan"], default=None,
        help="Document type (auto-detected if omitted)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show info-level findings")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--draft", action="store_true", help="Draft mode: relaxed threshold (PASS >= 50)")
    args = parser.parse_args()

    path = Path(args.path)
    doc_type = args.type or detect_doc_type(path)

    if doc_type == "spec":
        report = validate_spec(path, draft=args.draft)
    elif doc_type == "prd":
        report = validate_prd(path, draft=args.draft)
    elif doc_type == "plan":
        report = validate_plan(path)
    else:
        print(f"Unknown document type: {doc_type}", file=sys.stderr)
        return 1

    if args.json:
        print(render_json(report))
    else:
        print(render_text(report, verbose=args.verbose))

    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
