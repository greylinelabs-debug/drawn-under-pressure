from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TypeVar, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings


T = TypeVar("T", bound=BaseModel)


class GeminiStructuredClient:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def generate(self, prompt: str, schema: Type[T], *, image_path: str | Path | None = None) -> T:
        contents: list[object] = []
        if image_path is not None:
            path = Path(image_path)
            mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
            contents.append(types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_type))
        contents.append(prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response")
        return schema.model_validate_json(response.text)
