"""One-time local OAuth helper. Never prints credentials or tokens."""
import argparse
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPE = "https://www.googleapis.com/auth/drive"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Authorize Drawn Under Pressure to process its Google Drive folders."
    )
    parser.add_argument("client_json", type=Path, help="Downloaded Desktop OAuth client JSON")
    parser.add_argument("--out", type=Path, default=Path("drive-authorized-user.json"))
    args = parser.parse_args()
    if not args.client_json.is_file():
        raise FileNotFoundError(args.client_json)
    if args.out.exists():
        raise FileExistsError(f"Refusing to overwrite {args.out}")

    payload = json.loads(args.client_json.read_text(encoding="utf-8"))
    if "installed" not in payload:
        raise ValueError("Expected credentials for an OAuth Desktop app")
    flow = InstalledAppFlow.from_client_config(payload, [SCOPE])
    credentials = flow.run_local_server(
        host="localhost", port=0, authorization_prompt_message="Opening Google consent…",
        success_message="Authorization complete. You may close this tab.",
        open_browser=True, access_type="offline", prompt="consent",
    )
    if not credentials.refresh_token:
        raise RuntimeError("Google did not return an offline refresh token; revoke access and retry")
    args.out.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Saved authorized credentials to {args.out.resolve()}")
    print("Add the entire file contents as GitHub Actions secret GOOGLE_DRIVE_OAUTH_JSON, then delete the local file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
