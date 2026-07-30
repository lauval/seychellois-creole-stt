# Research Decisions Log
## Project: Seselwa ASR Evaluation Pipeline
## Language: Seychellois Creole (ISO 639-3: crs)

This log captures methodological decisions as they are made.
Append new entries as the project evolves. This becomes the backbone
of the methodology section in any write-up or application narrative.

---

## Entry 001 — Project framing
**Date:** July 2026

**Decision:** Frame this as an *evaluation* project, not a training project.

**Rationale:** We are not building a model from scratch. We are stress-testing
existing multilingual ASR models on a language variety and domain (parliamentary
code-switching speech) they have not been designed for. The contribution is the
evaluation set itself, the benchmark results, and the failure mode analysis.
This is a valid and publishable research contribution for a proof-of-concept
at this stage.

---

## Entry 002 — Dataset scope
**Date:** July 2026

**Decision:** Begin with one hour of manually verified audio-transcript pairs.

**Rationale:** One hour is sufficient to run a meaningful end-to-end pipeline
and produce real WER numbers. It is also honest — we are not overclaiming a
large dataset. The framing is a carefully curated small corpus, not a
comprehensive benchmark. More data can be added iteratively once the pipeline
is validated end to end.

**Data source — named session:** National Assembly of Seychelles,
Wednesday 25th February 2026.
- Verbatim: https://www.nationalassembly.sc/node/3910
- YouTube: https://www.youtube.com/watch?v=hFQ0L3wZAnY

**Rationale for session selection:** This sitting was selected because it
contains dense, analytically documented code-switching between Kreol Seselwa
and English, particularly in the Vice President's Department of Public
Administration budget presentation. A specific extract from this session
was already cited and analysed in the OCEAN AI Technical Feasibility Report
(Valentin, May 2026), giving the data selection a motivated, non-arbitrary
basis that can be cited in methodology write-ups.

The extract in question (Verbatim, p.5) illustrates intra-sentential
code-switching triggered by domain-specific terminology with no established
Kreol equivalent — exactly the linguistic phenomenon under investigation.

---

## Entry 003 — Ground truth transcripts
**Date:** July 2026

**Decision:** Use official parliamentary verbatims as ground truth, without
adding disfluency annotation (ums, false starts, self-corrections).

**Rationale:** The research question is code-switching performance, not
disfluency handling. Disfluencies absent from the verbatim but present in
audio would inflate insertion error rates in a misleading way. The verbatim
represents edited but linguistically faithful text for our purposes.

**Caveat to monitor:** Official verbatims may silently substitute French for
Creole utterances or vice versa. During the manual correction pass, each
segment must be checked to confirm the *language* of each unit is faithfully
represented, even if exact wording is tidied up. Instances where language
substitution occurs should be noted — this finding is itself analytically
interesting and speaks to how the institution treats Creole in its official record.

**Orthographic note:** The February 25th verbatim exhibits documented
orthographic variability — e.g. "avek" vs "ek" appearing in the same document.
This is a known property of Kreol Seselwa's maturing written standard
(Lortograf Kreol Seselwa). For this evaluation set, both forms are accepted
as valid ground truth. Normalisation decisions are deferred to a later
dataset construction phase and should involve the Lenstiti Kreol.

---

## Entry 004 — Timestamp alignment method
**Date:** July 2026

**Decision:** Use WhisperX to generate candidate word-level timestamps,
then manually correct against the verbatim.

**Rationale:** The official verbatims contain no timestamps. WhisperX
produces word-level alignment via phoneme-level forced alignment, giving
a much better starting point for manual correction than raw Whisper
segment-level output. Manual correction is scoped to the first hour of
audio for the initial pipeline run.

**Alignment language proxy:** WhisperX does not support crs natively.
We use `fr` (French) as the alignment language given Seychellois Creole's
French lexical base. Alignment confidence is expected to degrade at
English code-switch points — these are priority targets for manual correction
and are analytically significant in their own right.

---

## Entry 005 — Language tagging
**Date:** July 2026

**Decision:** Tag each token in the ground truth with its language:
Seychellois Creole (crs), French (fr), or English (en).

**Rationale:** WER alone is not sufficient for our research question.
The analytical contribution is showing *where* models fail — specifically
whether errors cluster at code-switch points. Language tags at the token
level make this analysis possible. Tagging will be done during the
manual correction pass.

---

## Entry 006 — Model comparison design
**Date:** July 2026

**Decision:** Evaluate three models as baselines:
1. Whisper large-v3 (OpenAI) — Western multilingual benchmark
2. MMS mms-1b-all (Meta) — broad multilingual coverage, language forced to crs
3. Whisper large-v3 with language hint set to French — tests whether
   the French lexical proximity of Seychellois Creole helps a model
   not explicitly supporting crs without any retraining

**Rationale:** This comparison structure lets us ask two distinct questions:
(a) does broader language coverage (MMS) outperform a stronger but more
linguistically biased model (Whisper) on an unseen low-resource language?
This question is motivated by Michel (2024), which found XLSR-Wav2Vec2
outperforming fine-tuned Whisper on Haitian Creole — a cautionary result
against assuming the best general model is the best low-resource model.
(b) does exploiting linguistic relatedness (French hint) improve Whisper's
performance on crs without any retraining?

**Metric:** Primary — Word Error Rate (WER) overall.
Secondary — WER segmented by monolingual vs code-switch regions.
The delta between these two is the core finding.

---

## Entry 007 — Architectural literature for discussion
**Date:** July 2026

**Key papers to engage:**

**Paper 1:** "Adapting Whisper for code-switching through encoding refining
and language-aware decoding" (ICASSP 2025).
This paper addresses the core architectural failure mode we hypothesise:
Whisper treats each utterance as belonging to one language, so mid-sentence
switches confuse the language identification component upstream of transcription.
Language-aware decoding at the token level is the proposed fix. Our results
will either support or complicate this framing.

**Paper 2:** "Adapting Whisper for parameter-efficient code-switching speech
recognition via soft prompt tuning" (arXiv 2506.21576, 2025).
Cited in the OCEAN AI Technical Feasibility Report (Valentin, May 2026, ref. [8]).
This paper demonstrates that soft prompt tuning — prepending learned prompt
vectors to Whisper's encoder input — can adapt the model for code-switching
without full fine-tuning. Crucially, it does so on Mandarin-English, a
high-resource code-switching pair. The significance for our work: this is
the architectural direction that a future Kreol Seselwa-specific adaptation
would likely follow, but it depends on having labelled code-switching training
data that does not yet exist for crs. Our benchmark results make the case
for why that data needs to be built.

**Narrative function of these papers:** We are not running these methods.
We are citing them as the state-of-the-art response to the failure modes
our results will demonstrate. The structure is: here is what models do,
here is where they fail on our data, here is what the literature proposes
as a fix, here is why that fix cannot yet be applied to Kreol Seselwa,
here is what would need to exist for it to be applied. That is the roadmap
contribution.

---

## Entry 008 — Alignment pipeline implementation and findings
**Date:** July 2026

**Transcription language decision:** Initial pipeline used French (`fr`) as
the transcription language, treating it as the closest supported proxy for
Kreol Seselwa. Switched to Haitian Creole (`ht`) on the basis that it is a
closer typological match — both are French-lexifier creoles. WhisperX
produced word-level timestamps using `ht` transcription with `fr` alignment,
demonstrating that Haitian Creole generalises to Kreol Seselwa in a forced
alignment context. This is itself an interesting finding: the Whisper model's
representation of Haitian Creole captures enough phonological structure to
segment Kreol Seselwa speech at the word level.

**Alignment model:** French (`fr`) forced alignment via wav2vec2
(`VOXPOPULI_ASR_BASE_10K_FR`). No wav2vec2 alignment model exists for
Haitian Creole — the only HuggingFace model (`LLL-CREAM/wav2vec2-HAT-0.2K-ALH-base`)
is a self-supervised base model, not CTC-finetuned, so it cannot be used for
forced alignment. French alignment works given the shared phoneme inventory
between Kreol Seselwa and French.

**Approach 1 — Proportional segment mapping (failed):** Transcribed with
WhisperX to get VAD-derived segment boundaries, then mapped verbatim text
onto those segments proportionally by character count. Result: wildly uneven
timestamp distribution. The Haitian Creole transcription produced highly
variable text density across the audio (some segments dense, others sparse),
and the proportional mapping amplified this variance. 133 segments exceeded
10 seconds, with some containing ~2000 characters. A 60-second gap appeared
at minute 1 where the transcription produced no text. Not usable.

**Approach 2 — Uniform 30-second chunks (limited):** Bypassed transcription
entirely. Divided the verbatim text into equal-length chunks mapped to
uniform 30-second audio windows, then ran French CTC alignment within each
chunk. Result: perfectly even timestamp distribution across the full audio,
but the CTC alignment model failed on many segments ("backtrack failed,
resorting to original"), particularly toward the end. Root cause: 30 seconds
of Kreol text is too much for the French alignment model to match reliably.
More fundamentally, this dataset is not conversational — parliamentary speech
contains long monologues (ministers reading budget presentations) that do not
segment naturally into 30-second units. A uniform chunking approach does not
suit this speech register.

**Audio extraction bug found and fixed:** FFmpeg's `-ss` flag placed before
`-i` (input seeking) resets the output timeline to zero. Combined with `-to`
(interpreted as output time, not source time), this produced 77.8 minutes of
audio instead of the intended 69 minutes (10:37 to 1:19:40 in the source
video). Fixed by moving `-ss` after `-i` so both `-ss` and `-to` are
interpreted as source timestamps. Re-extracted audio confirmed at 1:09:03.

**Dependency issues encountered:** WhisperX 3.1.1 was yanked from PyPI
(unofficial release) and incompatible with current torchaudio. Upgraded to
3.7.2. Additionally, pyannote-audio 3.4.0 references removed torchaudio APIs
(`AudioMetaData`, `list_audio_backends`) — patched in-venv. PyTorch 2.12
defaults to `weights_only=True` in `torch.load`, which breaks pyannote model
loading — overridden in the align script.

**Next steps:**
1. Re-run Haitian Creole transcription + French alignment on the corrected
   69-minute audio to recover word-level timestamp data.
2. Manual correction pass (see Entry 009).
3. Re-run forced alignment on corrected segments (see Entry 009).

---

## Entry 009 — Manual correction and forced alignment workflow
**Date:** July 2026

**Decision:** Use the Haitian Creole transcription output as the structural
scaffold, manually correct the text against the verbatim, then re-run forced
alignment to get accurate word-level timestamps for the corrected text.

**Workflow — three passes:**

1. **Transcription pass (automated):** Run WhisperX with `ht` (Haitian Creole)
   on the audio. This produces a JSON with segments, each containing `start`,
   `end`, and `text` fields. The timing is accurate (derived from VAD — voice
   activity detection — which operates on the audio signal, not the language
   model). The text is approximate — the model's best guess at what's being
   said, filtered through Haitian Creole phonology.

2. **Manual correction pass (human):** Listen to the audio while reading the
   transcription output. Replace the imperfect Haitian Creole text with the
   correct verbatim text, segment by segment. Keep the `start` and `end`
   timestamps intact — these are the timing scaffolding. Adjust segment
   boundaries only where they clearly misalign with speaker turns or pauses.
   Output: a corrected JSON with accurate text and approximate timing.

3. **Forced alignment pass (automated):** Feed the corrected JSON back into
   `whisperx.align()`. The alignment model (French wav2vec2) takes each
   segment's text and its time window, then searches within that window to
   pin each word to its exact position. Output: word-level timestamps for
   the ground truth text.

**Why this works:** Forced alignment needs two inputs: known text and
approximate timing. The original verbatim had no timing at all, which is
why earlier forced alignment attempts failed — we had to invent approximate
timestamps, and our heuristics (proportional mapping, uniform chunks) were
too inaccurate. The transcription pass solves this by providing reliable
segment boundaries derived from the audio signal itself.

**Why not skip straight to forced alignment with the verbatim?** Because
`whisperx.align()` works within time windows — it extracts the audio between
`start` and `end` for each segment, then aligns the text to that audio
slice. If the time window is wrong (text says minute 5, audio is actually
minute 8), the model searches wrong audio and fails. The verbatim has no
timestamps, so without a prior on when each chunk of text occurs, forced
alignment cannot operate. The transcription pass provides that prior.

**Key insight:** The three components of WhisperX serve different purposes:
- **VAD** (voice activity detection): finds where speech exists. Operates
  on audio signal. Language-agnostic. Always accurate.
- **Transcription** (Whisper): generates text. Language-dependent. Imperfect
  for Kreol Seselwa but provides structural scaffolding.
- **Alignment** (wav2vec2 CTC): pins known text to exact timing. Needs
  approximate boundaries to search within. Phoneme-level, so French works
  for Kreol given shared phonology.

The manual correction step sits between transcription and alignment,
substituting ground truth text while preserving the timing structure.

---

## Entry 010 — Automated verbatim-to-audio alignment (replacing manual correction)
**Date:** July 2026

**Decision:** Replace the manual correction pass (Entry 009, step 2) with
automated word-level matching between the Haitian Creole transcription and
the verbatim transcript. This eliminates the human bottleneck while
preserving the timing scaffold approach.

**Problem:** Entry 009 assumed a human would manually replace ht text with
verbatim text segment-by-segment. This is prohibitively slow for 69 minutes
of audio. Automating the text-to-timing mapping is essential.

**Approaches tested and failed:**

1. **Character-ratio mapping (Approach 3).** Transcribe with ht to get
   segment boundaries, then distribute verbatim text across those segments
   proportionally to the ht text's character count in each segment.
   Hallucinated segments (Whisper repetition loops, ~15 of 580 segments)
   got duration-based estimates instead.
   *Result:* 167 ht segments with median 25s duration. CTC alignment
   failed on 39% of segments (141/359). The character-ratio assumption —
   that ht text density proxies for verbatim text position — is
   fundamentally wrong. The two texts have different word counts,
   morphology, and density patterns. Verbatim text was systematically
   mapped to wrong time windows.

2. **Character-ratio + segment splitting (Approach 3b).** Same as above,
   but split long mapped segments at sentence boundaries before alignment,
   targeting ~400 chars per segment.
   *Result:* 730 segments, median 5s, but 74% CTC failure rate (662/889).
   Splitting compounded the timing error — each sub-segment inherited
   proportionally-divided timestamps from an already-wrong parent, making
   the text-to-audio mismatch worse, not better.

**Approach that works — two-pass word-level matching (Approach 4):**

1. **Pass 1 — ht transcription + alignment:** Transcribe with ht and
   run French CTC alignment on the ht text. This produces word-level
   timestamps for ~8,000+ ht words (filtering out low-confidence words
   with alignment score < 0.3, which removes hallucination artifacts).
   We know this works well from earlier testing — the original ht-only
   pipeline produced 580 segments with word-level alignment on all of them.

2. **Word matching:** Greedy forward matching between normalized ht words
   and normalized verbatim words. Skip words shorter than 3 characters
   to avoid false matches on common particles (e, i, a). Use a
   proportional search window (±80 ht words around the expected position)
   to handle varying text density. Each match creates an anchor point:
   a verbatim word position with a known audio timestamp.

3. **Timeline interpolation:** For unmatched verbatim words (the majority,
   since the verbatim has ~5x more words than the ht transcription),
   interpolate timestamps linearly between surrounding anchor points.

4. **Segmentation:** Split the timed verbatim into segments at sentence
   boundaries (. ? !), targeting 80–400 characters per segment.

5. **Pass 2 — verbatim alignment:** Run French CTC alignment on the
   verbatim segments. Because the timing now comes from matched anchor
   points rather than character-ratio guesses, the text-to-audio
   correspondence is much tighter and the CTC model can find the words.

**Why this works better:** The ht transcription and the verbatim describe
the same speech. Despite different orthography and word forms, many words
are identical or near-identical (proper nouns, numbers, English terms,
shared Creole vocabulary). These shared words serve as anchor points that
pin the verbatim to the audio timeline with actual phonetic evidence,
rather than the statistical guess of character-ratio mapping.

**Key finding — why character-ratio mapping fails:** The ht transcription's
text density is NOT a reliable proxy for where verbatim text falls in the
audio. The two texts differ in word count (~10K vs ~52K), morphology, and
coverage (hallucination segments produce hundreds of fake words). Treating
ht character count as proportional to verbatim position introduces
systematic timing errors that cascade through the pipeline.

**Approach 4 also failed — word matching is harder than expected.**

Three variants were tested:

4a. **Greedy forward matching** with exact word comparison, window of ±80
    ht words. Only 322 anchors (0.7% of verbatim). The search window was
    too narrow and the monotonicity constraint caused the algorithm to
    desync early. Different orthographic conventions between ht output
    and crs verbatim meant many cognates didn't match exactly
    ("bonjou" vs "bonzour", "moun" vs "dimoun").

4b. **Global SequenceMatcher** (difflib) on full word lists. 1875 anchors
    (3.8%) — better coverage, but the LCS matched repeated words
    (e.g. "Mersi") across distant parts of the text, producing a timeline
    that spanned 45,442 seconds for 4,143 seconds of audio. Global LCS
    is wrong for this problem; local matching is needed.

4c. **Chunked SequenceMatcher** — match within 30-second time windows to
    keep anchors temporally local. 540 anchors (1.1%). Locally correct
    but too sparse — the proportional verbatim window estimate drifted
    between chunks, and most chunks produced very few matches despite
    73% vocabulary overlap between ht and verbatim at the type level.
    Median segment duration 0.3s. 86% CTC alignment failure rate.

**Key diagnostic finding:** 73% of unique ht word types appear in the
verbatim vocabulary. The overlap exists but is not being captured by the
matching algorithms. Suspected causes:

1. The "ht-only" words in the vocabulary analysis were mostly just
   punctuation variants ("bidze," vs "bidze"). The normalization strips
   this, so the overlap should translate to matches. But the matching
   is still sparse, suggesting the issue is distributional — the same
   words appear at different densities and positions in the two texts.

2. The ht transcription has ~10K words for 69 minutes; the verbatim has
   ~50K words. The 5:1 ratio means large stretches of verbatim have no
   ht counterpart. When the proportional window estimate drifts even
   slightly, the correct verbatim window moves out of range.

3. Hallucinated segments (~5 minutes of audio) produce zero reliable
   ht words, creating anchor deserts that compound the drift problem.

**Broader lesson:** The problem of mapping untimed verbatim text to audio
without a matching-language ASR model is harder than expected. The ht
transcription is a useful phonological proxy for transcription and segment
timing, but it is not a reliable bridge for automated text mapping because
the orthographic distance between the two texts is too large for word-level
matching and the word count ratio is too skewed for proportional estimation.

**Status: resolved — see Entry 011.** Character-level matching was
attempted next but failed due to cursor drift at scale. Decision: manual
alignment using a browser-based editor tool, with the ht timestamps as
the timing scaffold. MFA remains an unexplored alternative.

---

## Entry 011 — Manual alignment with editor tool
**Date:** 28 July 2026

**Decision:** Abandon automated verbatim-to-audio mapping. Use the ht
alignment cache (580 segments with timestamps) as the timing scaffold
and manually replace the ht text with verbatim text using a browser-based
editor.

**What was tried since Entry 010:**

Character-level SequenceMatcher matching — instead of matching whole words
between ht and verbatim (which failed at 1.1% coverage in Entry 010),
match the CHARACTER SEQUENCES of each ht segment against the verbatim
text. This correctly identifies corresponding regions ("ban nan di moun"
(ht) ≈ "bann dimoun" (crs)) with ratios of 0.6–0.88 in testing. The
character-level signal is strong.

However, the algorithm failed at scale. 466 of 580 segments matched, but
cursor tracking — determining WHERE in the verbatim we are as we process
segments sequentially — caused anchor points to bunch up at the start of
the text. The timestamps for the first few minutes were compressed into
seconds, and 89% of segments failed CTC alignment. Adjusting the cursor
advancement (using time-proportional estimates instead of match extent)
made it worse because speech rate varies across the recording.

**Why automated mapping is fundamentally hard for this data:**

The ht transcription has ~10K words; the verbatim has ~50K words. This
5:1 ratio means any algorithm tracking position through both texts
simultaneously faces a drift problem — small errors in estimating how
much verbatim corresponds to each ht segment compound over 580 segments.
Character-level matching proved that the phonological overlap is real and
detectable, but tracking cumulative position through a 5:1 word ratio
over 69 minutes defeats sequential cursor-based algorithms.

**Current pipeline state:**

- `scripts/align.py` — cleaned to do one thing: generate the ht alignment
  cache (`_ht_aligned.json`). The cache for the February 2026 session
  already exists. All failed matching code has been removed.
- `data/aligned/*_ht_aligned.json` — 580 segments with start/end times
  and word-level timestamps. This is the timing scaffold.
- Alignment editor (browser tool) — loads the audio + JSON, provides
  clickable segment navigation, editable text areas, edit tracking,
  and JSON export. The manual workflow is: click a timestamp to hear the
  segment, paste the corresponding verbatim text, move to the next segment.

**Revised workflow (supersedes Entry 009 step 2):**

1. **Transcription pass (automated, done):** `scripts/align.py` produces
   the ht alignment cache.
2. **Manual correction pass (human, via editor):** Load the cache JSON
   and audio in the alignment editor. Replace ht text with verbatim text
   segment by segment. Export corrected JSON.
3. **Forced alignment pass (automated, future):** Feed the corrected JSON
   back into `whisperx.align()` to get word-level timestamps on the
   verbatim text. This step should work because the segment boundaries
   (from ht VAD) are accurate and the text will now be correct.

**Assessment:** The manual pass is slower than automation but reliable.
580 segments at ~15 seconds each is roughly 2.5 hours of editing work.
The editor tool makes this practical. The forced alignment pass (step 3)
has not been re-run yet — it depends on completing the manual correction.

---

## Open questions
- Will the National Assembly share audio directly, bypassing YouTube quality
  limitations? (Follow up — would improve audio cleanliness significantly)
- Does MMS include crs in its supported language list meaningfully, or is
  it present only nominally? (Test empirically during pipeline run)
- Does the verbatim faithfully represent code-switching language, or does
  it normalise toward French? (Assess during manual correction pass)
