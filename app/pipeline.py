from __future__ import annotations

import json
from pathlib import Path

from app.gemini import GeminiStructuredClient
from app.models import DrugTopic, ScriptPackage, SourcePage
from app.prompts import load_prompt


class ExtractionPipeline:
    def __init__(self, client: GeminiStructuredClient | None = None) -> None:
        self.client = client or GeminiStructuredClient()

    def transcribe_source(self, image_path: str | Path) -> SourcePage:
        prompt = load_prompt("transcribe_source.txt")
        return self.client.generate(prompt, SourcePage, image_path=image_path)

    def extract_drug(self, source: SourcePage) -> DrugTopic:
        if source.topic_type != "drug":
            raise ValueError(f"v0.2 currently supports drug pages only; detected {source.topic_type!r}")
        prompt = load_prompt("extract_drug.txt").format(source_text=source.source_text)
        result = self.client.generate(prompt, DrugTopic)
        if not result.topic.strip():
            result.topic = source.topic
        return result

    def write_script(self, source: SourcePage, topic: DrugTopic) -> ScriptPackage:
        prompt = load_prompt("write_script.txt").format(
            topic_json=json.dumps(topic.model_dump(), ensure_ascii=False, indent=2),
            source_text=source.source_text,
        )
        return self.client.generate(prompt, ScriptPackage)
