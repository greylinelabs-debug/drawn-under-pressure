# Drawn Under Pressure

Cloud-first pipeline for automatically turning a reliable anaesthetics/ICU source page into a short, viva-style revision video.

## Intended workflow

1. Source image arrives from Google Drive.
2. Gemini extracts only source-supported facts.
3. A structured script is generated:
   - Examiner: “Right then, doctor. Tell me about …”
   - PAUSE THE VIDEO / THINK LIKE THE CANDIDATE
   - One short sassy memory line
   - Proper Primary FRCA-style model answer
4. QC blocks unsupported or altered claims.
5. Later stages render the Drawn Under Pressure board, generate two voices, assemble a 45–60 second vertical MP4, and upload the result back to Drive.

## Current milestone

**v0.2: extraction + script generation + source-grounding QC**

This repository deliberately does not contain copyrighted textbook/source images. Test images should be supplied at runtime or via private cloud storage.

## Local test

```bash
python -m pip install -r requirements.txt
export GEMINI_API_KEY="..."
python -m app.main path/to/source-page.jpg --out outputs/test
```

On Windows PowerShell:

```powershell
python -m pip install -r requirements.txt
$env:GEMINI_API_KEY="..."
python -m app.main .\source-page.jpg --out .\outputs\test
```

## Safety rules

- Source is the authority.
- Missing facts stay missing.
- Numeric values and units must not be invented or silently changed.
- Every extracted fact should carry source evidence.
- A separate QC pass decides whether the episode is ready to render.

## Next milestone

v0.3 will add the branded board renderer, TTS voices and MP4 assembly.
