"""Extract 16kHz mono WAV audio from a video file using FFmpeg."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "audio"


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print(
            "Error: FFmpeg not found on PATH. "
            "Install it with: brew install ffmpeg (macOS) "
            "or apt install ffmpeg (Linux)",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    check_ffmpeg()

    parser = argparse.ArgumentParser(description="Extract audio from a video file")
    parser.add_argument("video", help="Path to the input video file")
    parser.add_argument("--start", help="Start timestamp, e.g. 10:37 or 1:02:30")
    parser.add_argument("--end", help="End timestamp, e.g. 1:30:00")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{video_path.stem}.wav"

    cmd = ["ffmpeg", "-y"]
    if args.start:
        cmd += ["-ss", args.start]
    cmd += ["-i", str(video_path)]
    if args.end:
        cmd += ["-to", args.end]
    cmd += ["-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(output_path)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(output_path)


if __name__ == "__main__":
    main()
