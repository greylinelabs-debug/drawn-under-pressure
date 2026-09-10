from __future__ import annotations

import json
import re

from app.gemini import GeminiStructuredClient
from app.models import DrugTopic, ModelQCReview, QCReport, ScriptPackage, SourcePage
from app.prompts import load_prompt


_NUMERIC_UNIT = re.compile(
    r"(?i)\b\d+(?:\.\d+)?\s*(?:mg|mcg|micrograms?|g|kg|ml|mL|l|L|%|mmol|mol|hours?|hrs?|days?|weeks?|months?|years?|minutes?|mins?|seconds?|secs?|bpm)\b"
)


def _normalise_numeric(token: str) -> str:
    return re.sub(r"\s+", "", token.lower())


def find_novel_numeric_unit_claims(source_text: str, script_text: str) -> list[str]:
    source_tokens = {_normalise_numeric(x) for x in _NUMERIC_UNIT.findall(source_text)}
    # findall returns full match because regex has no capturing group
    issues: list[str] = []
    for match in _NUMERIC_UNIT.finditer(script_text):
        token = match.group(0)
        if _normalise_numeric(token) not in source_tokens:
            issues.append(token)
    return sorted(set(issues))


class SourceGroundingQC:
    def __init__(self, client: GeminiStructuredClient | None = None) -> None:
        self.client = client or GeminiStructuredClient()

    def review(self, source: SourcePage, topic: DrugTopic, script: ScriptPackage) -> QCReport:
        if source.source_quality == "poor":
            return QCReport(
                status="blocked_source_quality",
                source_quality=source.source_quality,
                model_supported=False,
                notes=source.quality_notes or ["Source image quality was judged too poor for safe automated use."],
            )

        prompt = load_prompt("qc.txt").format(
            script_json=json.dumps(script.model_dump(), ensure_ascii=False, indent=2),
            topic_json=json.dumps(topic.model_dump(), ensure_ascii=False, indent=2),
            source_text=source.source_text,
        )
        model_review = self.client.generate(prompt, ModelQCReview)

        combined_script = " ".join([script.memory_line, script.formal_answer])
        deterministic_numeric = find_novel_numeric_unit_claims(source.source_text, combined_script)

        numeric_issues = sorted(set(model_review.numeric_or_unit_issues + deterministic_numeric))
        blocked = (
            not model_review.supported
            or bool(model_review.unsupported_or_distorted_claims)
            or bool(numeric_issues)
        )

        return QCReport(
            status="blocked_qc" if blocked else "ready_for_render",
            source_quality=source.source_quality,
            model_supported=model_review.supported,
            unsupported_or_distorted_claims=model_review.unsupported_or_distorted_claims,
            numeric_or_unit_issues=numeric_issues,
            missing_high_value_source_facts=model_review.missing_high_value_source_facts,
            notes=model_review.notes + source.quality_notes,
        )
