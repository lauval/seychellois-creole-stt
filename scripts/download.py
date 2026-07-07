"""Download a YouTube video using yt-dlp."""

import argparse
import subprocess
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "video"


def main():
    parser = argparse.ArgumentParser(description="Download a YouTube video")
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Download best video+audio, let yt-dlp pick the container
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", str(OUTPUT_DIR / "%(title)s.%(ext)s"),
        "--print", "after_move:filepath",
        args.url,
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(1)

    # Resolve the actual output file, ignoring partial downloads
    files = sorted(
        [f for f in OUTPUT_DIR.glob("*") if not f.name.endswith(".part")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not files:
        print("Error: download failed — no completed file found in output directory", file=sys.stderr)
        sys.exit(1)

    print(files[0])


if __name__ == "__main__":
    main()
