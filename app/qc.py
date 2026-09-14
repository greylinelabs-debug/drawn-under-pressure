from __future__ import annotations

import json
import re

from app.gemini import GeminiStructuredClient
from app.models import DrugTopic, ModelQCReview, QCReport, ScriptPackage, SourcePage
from app.prompts import load_prompt


_NUMERIC_UNIT = re.compile(
    r"(?i)(?<![\w.])\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\s*(?:micrograms?|mcg|mg|kg|g|ml|l|%|mmol|mol|hours?|hrs?|days?|weeks?|months?|years?|minutes?|mins?|seconds?|secs?|bpm)(?:\s*/\s*(?:kg|mg|ml|h|min|day|hr))*(?!\w)"
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

    def review(self, source: SourcePage, topic: DrugTopic, script: ScriptPackage, *, image_path=None) -> QCReport:
        if source.source_quality != "good":
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
        model_review = self.client.generate(prompt, ModelQCReview, image_path=image_path) if image_path else self.client.generate(prompt, ModelQCReview)

        combined_script = ' '.join([script.examiner_question, script.memory_line, script.formal_answer] +
            [s.heading + ' ' + ' '.join(s.bullets) for s in script.board_sections] +
            [f.value for k,v in topic.model_dump().items() if isinstance(v,list) for f in getattr(topic,k)])
        evidence_issues = []
        normalise = lambda text: ' '.join(text.casefold().split())
        facts = [f for k,v in topic.model_dump().items() if isinstance(v,list) for f in getattr(topic,k)]
        for fact in facts:
            if not fact.value.strip() or not fact.evidence.strip() or normalise(fact.evidence) not in normalise(source.source_text):
                evidence_issues.append('Missing or unverified evidence: ' + fact.value)
        if not facts or not script.formal_answer.strip() or not script.board_sections:
            evidence_issues.append('Empty topic, answer or board')
        if not script.examiner_question.startswith('Right then, doctor. Tell me about'):
            evidence_issues.append('Missing required examiner opening')
        # Also reject novel bare numbers (e.g. ratios, frequencies and receptor numbers).
        number = r'(?<![\w.])\d+(?:\.\d+)?'
        novel_numbers = set(re.findall(number, combined_script)) - set(re.findall(number, source.source_text))
        deterministic_numeric = find_novel_numeric_unit_claims(source.source_text, combined_script)

        numeric_issues = sorted(set(model_review.numeric_or_unit_issues + deterministic_numeric + list(novel_numbers)))
        blocked = (
            not model_review.supported
            or bool(model_review.unsupported_or_distorted_claims)
            or bool(numeric_issues)
            or bool(evidence_issues)
            or bool(model_review.missing_high_value_source_facts)
        )

        return QCReport(
            status="blocked_qc" if blocked else "ready_for_render",
            source_quality=source.source_quality,
            model_supported=model_review.supported,
            unsupported_or_distorted_claims=model_review.unsupported_or_distorted_claims + evidence_issues,
            numeric_or_unit_issues=numeric_issues,
            missing_high_value_source_facts=model_review.missing_high_value_source_facts,
            notes=model_review.notes + source.quality_notes,
        )
