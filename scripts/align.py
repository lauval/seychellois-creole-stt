"""Forced alignment of verbatim transcript to audio using WhisperX."""

import argparse
import json
import re
import sys
from pathlib import Path

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


def parse_verbatim(text):
    """Parse verbatim into speaker turns, collapsing PDF line breaks."""
    lines = text.splitlines()
    turns = []
    current_speaker = None
    current_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line and re.match(r"^[A-Z][A-Z .,'*-]+$", line):
            if current_speaker and current_lines:
                joined = re.sub(r"\s+", " ", " ".join(current_lines)).strip()
                if joined:
                    turns.append({"speaker": current_speaker, "text": joined})

            speaker_parts = [line]
            while (
                i + 1 < len(lines)
                and lines[i + 1].strip()
                and re.match(r"^[A-Z][A-Z .,'*-]+$", lines[i + 1].strip())
            ):
                i += 1
                speaker_parts.append(lines[i].strip())

            current_speaker = " ".join(speaker_parts)
            current_lines = []
        elif line:
            current_lines.append(line)

        i += 1

    if current_speaker and current_lines:
        joined = re.sub(r"\s+", " ", " ".join(current_lines)).strip()
        if joined:
            turns.append({"speaker": current_speaker, "text": joined})

    return turns


def map_verbatim_to_segments(turns, trans_segments):
    """Map verbatim text onto transcription segment timing proportionally."""
    full_verbatim = " ".join(t["text"] for t in turns)
    total_trans_chars = sum(len(seg["text"].strip()) for seg in trans_segments)
    if total_trans_chars == 0:
        return []

    segments = []
    verb_pos = 0
    for seg in trans_segments:
        ratio = len(seg["text"].strip()) / total_trans_chars
        end_pos = verb_pos + round(ratio * len(full_verbatim))
        # Snap to word boundary
        if end_pos < len(full_verbatim):
            space = full_verbatim.find(" ", end_pos)
            if space != -1 and space - end_pos < 30:
                end_pos = space

        chunk = full_verbatim[verb_pos:end_pos].strip()
        if chunk:
            segments.append({"text": chunk, "start": seg["start"], "end": seg["end"]})
        verb_pos = end_pos

    if verb_pos < len(full_verbatim) and segments:
        segments[-1]["text"] += " " + full_verbatim[verb_pos:].strip()

    return segments


def assign_speakers(aligned_segments, turns):
    """Tag each aligned segment with the speaker, based on character position."""
    turn_ranges = []
    pos = 0
    for t in turns:
        end = pos + len(t["text"]) + 1
        turn_ranges.append((pos, end, t["speaker"]))
        pos = end

    full_verbatim = " ".join(t["text"] for t in turns)
    seg_pos = 0
    for seg in aligned_segments:
        text = seg.get("text", "").strip()
        idx = full_verbatim.find(text, max(0, seg_pos - 50))
        if idx == -1:
            idx = seg_pos
        seg_pos = idx + len(text)

        for start, end, speaker in turn_ranges:
            if start <= idx < end:
                seg["speaker"] = speaker
                break


def main():
    parser = argparse.ArgumentParser(description="Align verbatim transcript to audio with WhisperX")
    parser.add_argument("audio", help="Path to the input audio file (16kHz mono WAV)")
    parser.add_argument("--verbatim", required=True, help="Path to the verbatim transcript text file")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    verbatim_path = Path(args.verbatim)

    if not audio_path.exists():
        print(f"Error: audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)
    if not verbatim_path.exists():
        print(f"Error: verbatim file not found: {verbatim_path}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = audio_path.stem

    # Parse verbatim into speaker turns
    verbatim_text = verbatim_path.read_text(encoding="utf-8")
    turns = parse_verbatim(verbatim_text)
    print(f"Parsed {len(turns)} speaker turns from verbatim")

    # Load audio
    audio = whisperx.load_audio(str(audio_path))

    # Transcribe to get segment timing (text quality doesn't matter, VAD boundaries do)
    print("Transcribing to get segment timing...")
    model = whisperx.load_model("large-v2", DEVICE, compute_type=COMPUTE_TYPE, language=TRANSCRIBE_LANG)
    trans_result = model.transcribe(audio, language=TRANSCRIBE_LANG, batch_size=8)
    print(f"Got {len(trans_result['segments'])} transcription segments")

    # Map verbatim text onto transcription segment timing
    segments = map_verbatim_to_segments(turns, trans_result["segments"])
    print(f"Mapped verbatim to {len(segments)} segments for alignment")

    # Run forced alignment with French model
    print("Running forced alignment...")
    align_model, metadata = whisperx.load_align_model(language_code=ALIGN_LANG, device=DEVICE)
    result = whisperx.align(
        segments, align_model, metadata, audio, DEVICE, return_char_alignments=False
    )

    # Tag aligned segments with speaker names
    assign_speakers(result["segments"], turns)

    # Save JSON
    json_path = OUTPUT_DIR / f"{stem}.json"
    with open(json_path, "w") as f:
        json.dump(result["segments"], f, ensure_ascii=False, indent=2)

    # Save timestamped text with speakers
    txt_path = OUTPUT_DIR / f"{stem}.txt"
    with open(txt_path, "w") as f:
        for seg in result["segments"]:
            start = format_timestamp(seg.get("start", 0))
            end = format_timestamp(seg.get("end", 0))
            speaker = seg.get("speaker", "UNKNOWN")
            text = seg.get("text", "").strip()
            f.write(f"[{start} -> {end}] [{speaker}] {text}\n")

    print(json_path)
    print(txt_path)


if __name__ == "__main__":
    main()
