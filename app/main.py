from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import settings
from app.pipeline import ExtractionPipeline
from app.qc import SourceGroundingQC


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run(image_path: str | Path, out_dir: str | Path | None = None) -> int:
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    out = Path(out_dir) if out_dir else settings.output_dir / image_path.stem
    out.mkdir(parents=True, exist_ok=True)

    pipeline = ExtractionPipeline()
    qc_engine = SourceGroundingQC(pipeline.client)

    source = pipeline.transcribe_source(image_path)
    _write_json(out / "source.json", source.model_dump())

    if source.source_quality == "poor":
        report = {
            "status": "blocked_source_quality",
            "source_quality": source.source_quality,
            "notes": source.quality_notes,
        }
        _write_json(out / "qc.json", report)
        print(f"Blocked: source quality is poor. See {out / 'qc.json'}")
        return 2

    topic = pipeline.extract_drug(source)
    _write_json(out / "topic.json", topic.model_dump())

    script = pipeline.write_script(source, topic)
    _write_json(out / "script.json", script.model_dump())

    qc = qc_engine.review(source, topic, script)
    _write_json(out / "qc.json", qc.model_dump())

    print(f"Topic: {topic.topic}")
    print(f"QC status: {qc.status}")
    print(f"Output: {out.resolve()}")
    return 0 if qc.status == "ready_for_render" else 3


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a source-grounded Drawn Under Pressure episode package from a photographed drug page.")
    parser.add_argument("image", help="Path to source page image")
    parser.add_argument("--out", help="Output directory")
    args = parser.parse_args()
    raise SystemExit(run(args.image, args.out))


if __name__ == "__main__":
    main()
