"""Transcribe and align audio using WhisperX, outputting word-level timestamps."""

import argparse
import json
import sys
from pathlib import Path

import whisperx

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "aligned"

# MPS has documented broadcast-compatibility crashes with WhisperX on Apple Silicon.
# CPU is the safe choice for both transcription and alignment.
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


def format_timestamp(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h:02d}:{int(m):02d}:{s:05.2f}"


def main():
    parser = argparse.ArgumentParser(description="Transcribe and align audio with WhisperX")
    parser.add_argument("audio", help="Path to the input audio file (16kHz mono WAV)")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = audio_path.stem

    # Load audio
    audio = whisperx.load_audio(str(audio_path))

    # Transcribe with large-v2, forcing French as closest proxy for Kreol Seselwa
    model = whisperx.load_model("large-v2", DEVICE, compute_type=COMPUTE_TYPE, language="fr")
    result = model.transcribe(audio, language="fr", batch_size=8)

    # Align to get word-level timestamps
    align_model, metadata = whisperx.load_align_model(language_code="fr", device=DEVICE)
    result = whisperx.align(
        result["segments"], align_model, metadata, audio, DEVICE, return_char_alignments=False
    )

    # Save word-level JSON
    json_path = OUTPUT_DIR / f"{stem}.json"
    with open(json_path, "w") as f:
        json.dump(result["segments"], f, ensure_ascii=False, indent=2)

    # Save plain text with inline timestamps for manual correction
    txt_path = OUTPUT_DIR / f"{stem}.txt"
    with open(txt_path, "w") as f:
        for seg in result["segments"]:
            start = format_timestamp(seg.get("start", 0))
            end = format_timestamp(seg.get("end", 0))
            text = seg.get("text", "").strip()
            f.write(f"[{start} -> {end}] {text}\n")

    print(json_path)
    print(txt_path)


if __name__ == "__main__":
    main()
