"""Generate timestamped ht (Haitian Creole) alignment from audio using WhisperX.

Transcribes with Haitian Creole (closest phonological proxy for Kreol Seselwa),
then aligns with French CTC model (shared phoneme inventory) to get word-level
timestamps. Output is cached as JSON for use in the alignment editor.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import torch
_orig_torch_load = torch.load
torch.load = lambda *a, **kw: _orig_torch_load(*a, **{**kw, "weights_only": False})

import whisperx

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "aligned"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"
TRANSCRIBE_LANG = "ht"
ALIGN_LANG = "fr"


def format_timestamp(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h:02d}:{int(m):02d}:{s:05.2f}"


def load_verbatim(path):
    """Parse bracketed-speaker verbatim into (full_text, turns)."""
    text = Path(path).read_text()
    turns = []
    current_speaker = None
    current_lines = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current_speaker and current_lines:
                joined = re.sub(r"\s+", " ", " ".join(current_lines)).strip()
                if joined:
                    turns.append({"speaker": current_speaker, "text": joined})
            current_speaker = stripped[1:-1]
            current_lines = []
        elif stripped:
            current_lines.append(stripped)

    if current_speaker and current_lines:
        joined = re.sub(r"\s+", " ", " ".join(current_lines)).strip()
        if joined:
            turns.append({"speaker": current_speaker, "text": joined})

    full_text = " ".join(t["text"] for t in turns)
    return full_text, turns


def main():
    parser = argparse.ArgumentParser(
        description="Generate ht alignment cache from audio with WhisperX"
    )
    parser.add_argument("audio", help="Path to the input audio file (16kHz mono WAV)")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = audio_path.stem

    # ── Load audio ──
    audio = whisperx.load_audio(str(audio_path))
    audio_duration = len(audio) / 16000
    print(f"Audio duration: {audio_duration:.1f}s ({audio_duration / 60:.1f} min)")

    # ── Transcribe with ht, align to get word timestamps ──
    ht_cache = OUTPUT_DIR / f"{stem}_ht_aligned.json"
    if ht_cache.exists():
        print(f"Cache already exists: {ht_cache}")
        with open(ht_cache) as f:
            segments = json.load(f)
        total_words = sum(len(s.get("words", [])) for s in segments)
        print(f"  {len(segments)} segments, {total_words} words")
        return

    print(f"Transcribing with '{TRANSCRIBE_LANG}' for timing scaffold...")
    model = whisperx.load_model(
        "large-v2", DEVICE, compute_type=COMPUTE_TYPE, language=TRANSCRIBE_LANG
    )
    trans_result = model.transcribe(
        audio, language=TRANSCRIBE_LANG, batch_size=8, print_progress=True
    )
    del model

    print(f"Got {len(trans_result['segments'])} segments, aligning for word timestamps...")
    align_model, metadata = whisperx.load_align_model(
        language_code=ALIGN_LANG, device=DEVICE
    )
    ht_aligned = whisperx.align(
        trans_result["segments"], align_model, metadata, audio, DEVICE,
        return_char_alignments=False, print_progress=True,
    )
    del align_model, metadata

    segments = ht_aligned["segments"]
    total_words = sum(len(s.get("words", [])) for s in segments)

    with open(ht_cache, "w") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    print(f"Cached {len(segments)} segments, {total_words} words to {ht_cache}")

    # ── Summary ──
    txt_path = OUTPUT_DIR / f"{stem}_ht_aligned.txt"
    with open(txt_path, "w") as f:
        for seg in segments:
            start = format_timestamp(seg.get("start", 0))
            end = format_timestamp(seg.get("end", 0))
            text = seg.get("text", "").strip()
            f.write(f"[{start} -> {end}] {text}\n")
    print(txt_path)


if __name__ == "__main__":
    main()
