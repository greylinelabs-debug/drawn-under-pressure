"""Credentialed end-to-end smoke test using an explicitly fictional source."""
from pathlib import Path
from PIL import Image, ImageDraw

from app.main import run
from app.render import font


SOURCE = """FICTIONALINE — PIPELINE TEST ONLY
This is a fictional medication created solely to test software. It is not a real medicine and contains no clinical advice.
Classification: fictional demonstration compound.
Presentation: labelled training card only.
Route: no route of administration; never administer.
Dose: no dose; never administer.
Mechanism: changes a blue test indicator to coral in this fictional example.
Use: validates extraction, evidence, narration, captions and layout.
Kinetics: not applicable.
Adverse effects: not applicable because this is not a real medicine.
Monitoring: verify that every generated claim is present on this card.
Exam point: state clearly that Fictionaline is fictional and must never be used clinically.
"""


def create_source(path: Path) -> None:
    image = Image.new("RGB", (1600, 2200), "#fffdf7")
    draw = ImageDraw.Draw(image)
    y = 90
    for paragraph in SOURCE.splitlines():
        face = font(48 if y == 90 else 34)
        words, line = paragraph.split(), ""
        for word in words:
            trial = (line + " " + word).strip()
            if face.getlength(trial) > 1400:
                draw.text((100, y), line, font=face, fill="#202c38")
                y += 55
                line = word
            else:
                line = trial
        draw.text((100, y), line, font=face, fill="#202c38")
        y += 78
    image.save(path)


def main() -> int:
    root = Path("outputs/live-smoke")
    root.mkdir(parents=True, exist_ok=True)
    source = root / "fictional-source.png"
    create_source(source)
    status = run(source, root / "episode")
    if status:
        raise RuntimeError("Credentialed synthetic pipeline smoke test was blocked")
    print("Credentialed fictional end-to-end smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
