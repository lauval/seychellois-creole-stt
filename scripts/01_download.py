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

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    # The last non-empty line of stdout is the final file path
    output_path = result.stdout.strip().splitlines()[-1]
    print(output_path)


if __name__ == "__main__":
    main()
