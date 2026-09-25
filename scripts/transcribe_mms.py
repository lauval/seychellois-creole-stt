"""Transcribe audio with Meta MMS using a selected language adapter.

This is an experimental path for comparing MMS output against the current
WhisperX timing scaffold. If an alignment JSON is provided, its start/end
boundaries are reused so the output can be loaded directly in the editor.
"""

import argparse
import json
import sys
from pathlib import Path

import torch
import torchaudio
from transformers import AutoProcessor, Wav2Vec2ForCTC

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "mms"
DEFAULT_MODEL = "facebook/mms-1b-all"
DEFAULT_LANGUAGE = "crs"
TARGET_SAMPLE_RATE = 16_000


def format_timestamp(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h:02d}:{int(m):02d}:{s:05.2f}"


def load_audio(path: Path) -> torch.Tensor:
    waveform, sample_rate = torchaudio.load(path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sample_rate != TARGET_SAMPLE_RATE:
        waveform = torchaudio.functional.resample(
            waveform, sample_rate, TARGET_SAMPLE_RATE
        )
    return waveform.squeeze(0)


def load_segments(path: Path | None, duration: float, chunk_seconds: float) -> list[dict]:
    if path is not None:
        with open(path) as f:
            raw_segments = json.load(f)
        return [
            {
                "start": float(seg.get("start", 0)),
                "end": float(seg.get("end", 0)),
                "whisperx_text": seg.get("text", ""),
                "speaker": seg.get("speaker"),
            }
            for seg in raw_segments
            if float(seg.get("end", 0)) > float(seg.get("start", 0))
        ]

    segments = []
    start = 0.0
    while start < duration:
        end = min(start + chunk_seconds, duration)
        segments.append({"start": start, "end": end})
        start = end
    return segments


def transcribe_slice(
    audio: torch.Tensor,
    start: float,
    end: float,
    processor: AutoProcessor,
    model: Wav2Vec2ForCTC,
    device: torch.device,
) -> str:
    start_sample = max(0, int(start * TARGET_SAMPLE_RATE))
    end_sample = min(audio.numel(), int(end * TARGET_SAMPLE_RATE))
    chunk = audio[start_sample:end_sample]
    if chunk.numel() == 0:
        return ""

    inputs = processor(
        chunk.numpy(),
        sampling_rate=TARGET_SAMPLE_RATE,
        return_tensors="pt",
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.inference_mode():
        logits = model(**inputs).logits

    ids = torch.argmax(logits, dim=-1)[0]
    return processor.decode(ids).strip()


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(requested)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio with Meta MMS for comparison with WhisperX"
    )
    parser.add_argument("audio", nargs="?", help="Path to input audio, ideally 16kHz mono WAV")
    parser.add_argument(
        "--segments",
        help="Optional WhisperX alignment JSON whose start/end boundaries are reused",
    )
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="MMS language code")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Hugging Face model id")
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Inference device",
    )
    parser.add_argument(
        "--chunk-seconds",
        type=float,
        default=20.0,
        help="Chunk length used when --segments is not supplied",
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Download/cache the model and language adapter, then exit",
    )
    args = parser.parse_args()

    device = choose_device(args.device)

    print(f"Loading MMS model: {args.model}")
    processor = AutoProcessor.from_pretrained(args.model)
    model = Wav2Vec2ForCTC.from_pretrained(args.model).to(device)
    processor.tokenizer.set_target_lang(args.language)
    model.load_adapter(args.language)
    model.eval()

    if args.cache_only:
        print(f"Cached model '{args.model}' with language adapter '{args.language}'")
        return

    if not args.audio:
        print("Error: audio path is required unless --cache-only is set", file=sys.stderr)
        sys.exit(1)

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    segments_path = Path(args.segments) if args.segments else None
    if segments_path is not None and not segments_path.exists():
        print(f"Error: segments file not found: {segments_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading audio: {audio_path}")
    audio = load_audio(audio_path)
    duration = audio.numel() / TARGET_SAMPLE_RATE
    print(f"Audio duration: {duration:.1f}s ({duration / 60:.1f} min)")

    segments = load_segments(segments_path, duration, args.chunk_seconds)
    print(f"Transcribing {len(segments)} segments with language '{args.language}'...")

    out_segments = []
    for idx, seg in enumerate(segments, start=1):
        start = max(0.0, min(float(seg["start"]), duration))
        end = max(start, min(float(seg["end"]), duration))
        text = transcribe_slice(audio, start, end, processor, model, device)
        out = {"start": start, "end": end, "text": text}
        if seg.get("whisperx_text"):
            out["whisperx_text"] = seg["whisperx_text"]
        if seg.get("speaker"):
            out["speaker"] = seg["speaker"]
        out_segments.append(out)
        print(f"{idx:>4}/{len(segments)} [{format_timestamp(start)} -> {format_timestamp(end)}] {text}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = args.language
    if segments_path is not None:
        suffix += "_on_whisperx_segments"
    json_path = OUTPUT_DIR / f"{audio_path.stem}_mms_{suffix}.json"
    txt_path = OUTPUT_DIR / f"{audio_path.stem}_mms_{suffix}.txt"

    with open(json_path, "w") as f:
        json.dump(out_segments, f, ensure_ascii=False, indent=2)

    with open(txt_path, "w") as f:
        for seg in out_segments:
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            f.write(f"[{start} -> {end}] {seg['text']}\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved text: {txt_path}")


if __name__ == "__main__":
    main()
