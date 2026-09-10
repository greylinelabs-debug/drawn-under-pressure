from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SourcePage(BaseModel):
    topic: str = Field(description="Best concise topic name visible on the supplied source page.")
    topic_type: Literal["drug", "other"] = Field(description="Use drug only when the page is primarily about a medication.")
    source_text: str = Field(description="Faithful transcription of the medically relevant text on the source page. Preserve numbers and units exactly.")
    source_quality: Literal["good", "usable_with_caution", "poor"]
    quality_notes: list[str] = Field(default_factory=list)


class GroundedFact(BaseModel):
    value: str = Field(description="Concise fact, preserving numeric values and units exactly as supported by the source.")
    evidence: str = Field(description="Short exact or near-exact source excerpt supporting this fact.")


class DrugTopic(BaseModel):
    topic: str
    classification: list[GroundedFact] = Field(default_factory=list)
    presentation_formulations: list[GroundedFact] = Field(default_factory=list)
    routes: list[GroundedFact] = Field(default_factory=list)
    common_doses: list[GroundedFact] = Field(default_factory=list)
    mechanism: list[GroundedFact] = Field(default_factory=list)
    pharmacodynamics: list[GroundedFact] = Field(default_factory=list)
    pharmacokinetics: list[GroundedFact] = Field(default_factory=list)
    indications_uses: list[GroundedFact] = Field(default_factory=list)
    contraindications_cautions: list[GroundedFact] = Field(default_factory=list)
    side_effects: list[GroundedFact] = Field(default_factory=list)
    interactions: list[GroundedFact] = Field(default_factory=list)
    monitoring: list[GroundedFact] = Field(default_factory=list)
    key_exam_points: list[GroundedFact] = Field(default_factory=list)


class BoardSection(BaseModel):
    heading: str
    bullets: list[str] = Field(default_factory=list)
    visual_hint: str = Field(default="", description="Simple medically accurate visual suggestion for the later renderer.")


class ScriptPackage(BaseModel):
    examiner_question: str
    pause_screen_top: Literal["PAUSE THE VIDEO"]
    pause_screen_bottom: Literal["THINK LIKE THE CANDIDATE"]
    memory_line: str = Field(description="One short, dry, slightly sassy sentence that captures the central memory hook.")
    formal_answer: str = Field(description="Concise, professional Primary FRCA-style oral answer. No jokes in this section.")
    board_sections: list[BoardSection] = Field(default_factory=list)
    omitted_due_to_source: list[str] = Field(default_factory=list)


class ModelQCReview(BaseModel):
    supported: bool
    unsupported_or_distorted_claims: list[str] = Field(default_factory=list)
    numeric_or_unit_issues: list[str] = Field(default_factory=list)
    missing_high_value_source_facts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class QCReport(BaseModel):
    status: Literal["ready_for_render", "blocked_source_quality", "blocked_qc"]
    source_quality: str
    model_supported: bool
    unsupported_or_distorted_claims: list[str] = Field(default_factory=list)
    numeric_or_unit_issues: list[str] = Field(default_factory=list)
    missing_high_value_source_facts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
