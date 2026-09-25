# Seychellois Creole ASR Project Framing

## Short Project Description

I am developing an evaluation and data-creation pipeline for Seychellois Creole
automatic speech recognition using public parliamentary recordings and official
transcripts. The project compares Haitian Creole proxy transcription with Meta's
MMS model in Seychellois Creole, constructs a manually corrected segment-level
reference, and uses WER/CER analysis to identify where multilingual ASR succeeds
and fails for an under-resourced Creole language.

## Research Framing

The project began with a cross-lingual transfer question:

> Is there a strong enough signal across Creole languages that an ASR model run
> in Haitian Creole mode can meaningfully transcribe Seychellois Creole audio
> with high fidelity?

Early experiments suggested that Haitian Creole proxy transcription was not a
strong enough baseline for high-fidelity Seychellois Creole transcription.
However, Meta's multilingual MMS model, using the `crs` language adapter,
produced a noticeably stronger baseline. This shifted the project from simply
testing cross-Creole transfer to building the infrastructure needed for a proper
Seychellois Creole ASR benchmark and fine-tuning dataset.

## Core Contribution

The main contribution is a reproducible pipeline for collecting, segmenting,
aligning, correcting, and evaluating public Seychellois Creole speech data.
Rather than treating transcription as a one-off task, the pipeline is designed
to support:

- baseline ASR comparison across models;
- creation of corrected segment-level reference transcripts;
- WER and CER evaluation against a consistent reference;
- future fine-tuning of models for Seychellois Creole;
- development of an open dataset for an under-resourced language.

## Methodological Position

The official National Assembly transcripts are not fully raw verbatim
transcripts. They appear to remove many false starts, repetitions, and
disfluencies, meaning they are closer to lightly normalized parliamentary
transcripts than exact speech records.

For evaluation, the corrected reference should therefore be described as a
manually corrected near-verbatim or lightly normalized Kreol Seselwa reference,
rather than a fully verbatim transcript. This distinction matters because WER is
only meaningful when the reference style is clearly defined.

CER should also be reported alongside WER, since character-level error may be
more informative for a lower-resource language with spelling variation,
code-switching, and inconsistent orthographic conventions.

## Baseline Comparison

The first evaluation compares:

- WhisperX using Haitian Creole (`ht`) as a proxy language;
- Meta MMS using Seychellois Creole (`crs`).

The expectation from the current experiment is that MMS with explicit `crs`
support will outperform the Haitian Creole proxy approach, though it still has
weaknesses in names, numbers, code-switching, noisy sections, and segmentation.

## Segmentation Strategy

MMS currently produces stronger text, but the output is segmented mechanically
into fixed 20-second chunks. This is acceptable as a first-pass canonical grid
because it is regular, auditable, and easy to correct.

Manual splitting should be used only where a speaker change inside a 20-second
segment materially affects readability, attribution, or evaluation. The goal is
not perfect natural utterance segmentation, but a practical and defensible
segment-level dataset.

## Longer-Term Direction

Once the corrected reference transcript is complete, the next stages are:

1. Run WER and CER analysis comparing WhisperX in Haitian Creole mode with MMS
   in Seychellois Creole mode.
2. Expand the corrected corpus with more public parliamentary speech.
3. Use the corrected segment-level audio/text pairs to fine-tune MMS for
   Seychellois Creole.
4. Optionally fine-tune a Whisper/WhisperX-based model and compare post-tuning
   results.
5. Publish the pipeline, evaluation results, and dataset-building methodology as
   an open resource for Seychellois Creole ASR.

## Application-Friendly Summary

I investigated whether cross-Creole transfer from Haitian Creole ASR could
support transcription of Seychellois Creole parliamentary speech, and found that
a language-specific multilingual MMS model produced a stronger baseline. This
led me to build a reproducible pipeline for collecting, segmenting, aligning,
correcting, and evaluating public Seychellois Creole speech data, with the
longer-term goal of creating an open ASR benchmark and fine-tuning dataset for
an under-resourced language.

