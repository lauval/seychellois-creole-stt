# Seselwa ASR Pipeline

ASR evaluation pipeline for Seychellois Creole (Kreol Seselwa, ISO 639-3: crs).

Downloads National Assembly parliamentary sessions from YouTube, extracts audio,
and produces word-level aligned transcriptions using WhisperX for manual correction
against official verbatim transcripts.

## Setup

```bash
uv sync
```

## Usage

```bash
# 1. Download video from YouTube
uv run python scripts/download.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. Extract 16kHz mono WAV audio
uv run python scripts/extract_audio.py data/raw/video/filename.mp4

# 3. Transcribe and align (outputs JSON + timestamped text)
uv run python scripts/align.py data/raw/audio/filename.wav
```

## Target session

National Assembly sitting of Wednesday 25th February 2026.
Verbatim: https://www.nationalassembly.sc/node/3910

Selected for dense code-switching between Kreol Seselwa and English
(Vice President's budget presentation).

## Notes

- WhisperX transcribes with `ht` (Haitian Creole) as the closest proxy for Kreol Seselwa, with `fr` (French) for alignment (no alignment model exists for Haitian Creole)
- Runs on CPU — WhisperX has documented MPS compatibility issues on Apple Silicon
- Aligned output goes to `data/aligned/`; manually corrected ground truth goes to `data/ground_truth/`
