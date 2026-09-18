# Drawn Under Pressure

Cloud pipeline: private source photograph → grounded viva script → deterministic revision board → offline British English speech → captioned vertical MP4 → private Drive ZIP.

## v0.3

- Measured 1080×1920 cream-and-teal board, progressive sections and burned sentence captions. Overflow blocks rendering instead of truncating medical facts.
- Free offline eSpeak NG with examiner/candidate pitch differences and an injectable SpeechProvider interface. The default voice is synthetic, not a studio performance.
- FFmpeg H.264/AAC assembly, four-second thinking pause, final board hold and checked 45–60 second duration. Long scripts fail rather than being sped up or cut.
- ZIP contains MP4, PNG, script, SRT, timeline, source transcription, grounded facts, QC and SHA-256 manifest. Source photos are never committed or packaged.
- Bounded Drive batches, pagination, resumable upload, checksum verification, recovery and private failure reports.
- CI runs unit, media integration and real speech tests without API credentials.

## Local usage

Python 3.11+. On Ubuntu install ffmpeg, espeak-ng and fonts-dejavu-core.

```sh
pip install -r requirements.txt
python -m pytest -q
python -m app.main /private/source.jpg --out outputs/new-episode
```

Set GEMINI_API_KEY in the environment or ignored .env. Use --extract-only to skip media. Always use a fresh output directory. BOARD_FONT optionally selects a TrueType font. Windows uses an imageio FFmpeg fallback; install eSpeak NG separately for narration.

## Cloud setup

[Project Drive folder](https://drive.google.com/drive/folders/1ANoG0ewnnVqo2rzhc02WRqY7yf19vfl1) is created. Non-secret folder IDs are in config/drive-folders.json.

1. Set GitHub Actions secret GEMINI_API_KEY.
2. Set GOOGLE_DRIVE_OAUTH_JSON to consented authorized-user OAuth JSON with client_id, client_secret, refresh_token and token_uri. Enable the Drive API for the OAuth client and authorize a scope able to read/write the project folders. Never put credentials in chat, issues or source files.
3. Set repository variable DRIVE_PIPELINE_ENABLED=true. The workflow checks every six hours, at most three items per run; manual dispatch is also available.
4. Upload readable JPEG, PNG or WebP images up to 20 MiB to Inbox.

The connected ChatGPT Drive account does not export credentials to GitHub Actions. Separate Google OAuth consent is required for unattended execution. Authorized-user OAuth is the default for personal My Drive. Configure the OAuth app for ongoing use; testing-mode refresh tokens can expire.

Successful source files move to Finished beside source-id.zip. QC and format failures move to Failed with a private report. Infrastructure failures leave sources in Processing for retry. Exactly one worker is supported: preserve the Actions concurrency group and do not run a local worker concurrently. Drive moves are not a distributed lock.

## Source grounding

The supplied source is the sole authority. Missing facts stay missing. Exact evidence excerpts are checked against transcription. Numeric checks cover extracted facts, narration and board labels, including percentages, ranges and compound units. Independent model QC sees the source image and checks transcription and semantic claims. Uncertain image quality blocks automation. Significant omissions also block.

Automated QC establishes source fidelity, not medical correctness. Numeric matching alone cannot verify which dose belongs to which indication. The independent image/model check is the semantic layer. No live Amiodarone or other medical acceptance result is claimed until a credentialed trusted-source run succeeds.

Layout or timing failures require a shorter source-grounded script and repeated QC. No outside supplementation, silent rewriting or automatic public video publishing is enabled.

Recovery: inspect Failed privately, fix the source and move it back to Inbox. For a changed source with the same ID, archive its old ZIP elsewhere before retrying; different packages are never silently overwritten. Processing recovery checks the source version and uploaded package checksum, including interruption before the final verification marker. Medical source material and generated medical output are never uploaded as public Actions artifacts.

## Watch the synthetic presentation demo

The `Render synthetic style demo` workflow creates a spoken 45–60 second preview with no credentials and no medical claims. Download its `synthetic-style-demo` artifact from the Actions run. These explicitly labelled synthetic files are safe to share and are retained for 14 days.

```sh
python -m app.demo --out outputs/style-demo
```

The preview includes a full-screen examiner question, a pause screen, a memory hook, progressive sketch-style panels and a final recall board. It uses the free eSpeak NG voice, which remains noticeably synthetic. It is a style demonstration, not medical acceptance testing. Generic frames and marks are decorative; medical illustrations have not been introduced without sources.

Caption chunks preserve the script's words, while speech clips are padded to video-frame boundaries. Lossless intermediate audio avoids encoder padding accumulating between clips. A final decode and duration check guards the assembled MP4.

## Validation

```sh
RUN_MEDIA_TESTS=1 python -m pytest -q
```

Tests cover altered numbers, board-only claims, missing evidence, uncertain sources, overflow, deterministic boards, blocked rendering, actual FFmpeg encoding/decoding, manifests and Drive success/failure/outage transitions. Synthetic fixtures contain no medical advice. Linux CI tests real eSpeak NG.

References: [Drive moves](https://developers.google.com/workspace/drive/api/guides/folder), [uploads](https://developers.google.com/workspace/drive/api/guides/manage-uploads), [eSpeak NG](https://github.com/espeak-ng/espeak-ng), [FFmpeg](https://ffmpeg.org/ffmpeg.html).
