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
uv run python scripts/01_download.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. Extract 16kHz mono WAV audio
uv run python scripts/02_extract_audio.py data/raw/video/filename.mp4

# 3. Transcribe and align (outputs JSON + timestamped text)
uv run python scripts/03_align.py data/raw/audio/filename.wav
```

## Target session

National Assembly sitting of Wednesday 25th February 2026.
Verbatim: https://www.nationalassembly.sc/node/3910

Selected for dense code-switching between Kreol Seselwa and English
(Vice President's budget presentation).

## Notes

- WhisperX uses `fr` (French) as the closest supported language proxy for Kreol Seselwa
- Runs on CPU — WhisperX has documented MPS compatibility issues on Apple Silicon
- Aligned output goes to `data/aligned/`; manually corrected ground truth goes to `data/ground_truth/`
