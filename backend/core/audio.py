import logging
import os
from typing import List, Tuple

import numpy as np
import torch
from pydub import AudioSegment

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
# gigaam transcribe() rejects files > 25 s; keep hard cap at 15 s for safety
HARD_CAP_SEC = 15


def convert_to_wav(input_path: str, output_path: str) -> str:
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(2)
    audio.export(output_path, format="wav")
    return output_path


def get_duration(wav_path: str) -> float:
    audio = AudioSegment.from_wav(wav_path)
    return len(audio) / 1000.0


def _pydub_to_tensor(audio: AudioSegment) -> torch.Tensor:
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
    return torch.from_numpy(samples)


def _export_segment(audio: AudioSegment, start_ms: int, end_ms: int, path: str) -> str:
    audio[start_ms:end_ms].export(path, format="wav")
    return path


def _sub_split(
    audio: AudioSegment,
    start_ms: int,
    end_ms: int,
    tmp_dir: str,
    idx_ref: list,  # mutable counter [n]
) -> List[Tuple[str, float, float]]:
    """Split a segment into HARD_CAP_SEC sub-chunks if it's too long."""
    cap_ms = HARD_CAP_SEC * 1000
    result = []
    offset = start_ms
    while offset < end_ms:
        chunk_end = min(offset + cap_ms, end_ms)
        out = os.path.join(tmp_dir, f"chunk_{idx_ref[0]:04d}.wav")
        _export_segment(audio, offset, chunk_end, out)
        result.append((out, offset / 1000.0, chunk_end / 1000.0))
        idx_ref[0] += 1
        offset = chunk_end
    return result


def split_fixed(wav_path: str, chunk_sec: int, tmp_dir: str) -> List[Tuple[str, float, float]]:
    cap_sec = min(chunk_sec, HARD_CAP_SEC)
    audio = AudioSegment.from_wav(wav_path)
    cap_ms = cap_sec * 1000
    total_ms = len(audio)
    chunks = []
    idx = [0]
    offset = 0
    while offset < total_ms:
        end_ms = min(offset + cap_ms, total_ms)
        out = os.path.join(tmp_dir, f"chunk_{idx[0]:04d}.wav")
        _export_segment(audio, offset, end_ms, out)
        chunks.append((out, offset / 1000.0, end_ms / 1000.0))
        idx[0] += 1
        offset = end_ms
    return chunks


def split_vad(wav_path: str, chunk_sec: int, tmp_dir: str) -> List[Tuple[str, float, float]]:
    cap_sec = min(chunk_sec, HARD_CAP_SEC)
    try:
        from silero_vad import load_silero_vad, get_speech_timestamps

        audio = AudioSegment.from_wav(wav_path)
        wav_tensor = _pydub_to_tensor(audio)

        vad_model = load_silero_vad()
        timestamps = get_speech_timestamps(wav_tensor, vad_model, sampling_rate=SAMPLE_RATE)

        if not timestamps:
            return split_fixed(wav_path, cap_sec, tmp_dir)

        cap_ms = cap_sec * 1000
        idx = [0]
        chunks: List[Tuple[str, float, float]] = []

        # Group consecutive speech segments into chunks ≤ cap_ms,
        # then sub-split any chunk that still exceeds HARD_CAP_SEC.
        pending_start_ms: int | None = None
        pending_end_ms: int = 0
        pending_dur_ms: int = 0

        def flush_pending():
            if pending_start_ms is None:
                return
            for item in _sub_split(audio, pending_start_ms, pending_end_ms, tmp_dir, idx):
                chunks.append(item)

        for ts in timestamps:
            seg_start_ms = int(ts["start"] * 1000 / SAMPLE_RATE)
            seg_end_ms = int(ts["end"] * 1000 / SAMPLE_RATE)
            seg_dur_ms = seg_end_ms - seg_start_ms

            if pending_start_ms is None:
                pending_start_ms = seg_start_ms
                pending_end_ms = seg_end_ms
                pending_dur_ms = seg_dur_ms
            elif pending_dur_ms + seg_dur_ms > cap_ms:
                # flush what we have, start new group
                for item in _sub_split(audio, pending_start_ms, pending_end_ms, tmp_dir, idx):
                    chunks.append(item)
                pending_start_ms = seg_start_ms
                pending_end_ms = seg_end_ms
                pending_dur_ms = seg_dur_ms
            else:
                pending_end_ms = seg_end_ms
                pending_dur_ms += seg_dur_ms

        # flush last group
        if pending_start_ms is not None:
            for item in _sub_split(audio, pending_start_ms, pending_end_ms, tmp_dir, idx):
                chunks.append(item)

        return chunks if chunks else split_fixed(wav_path, cap_sec, tmp_dir)

    except Exception as e:
        logger.warning("VAD failed (%s), falling back to fixed split", e)
        return split_fixed(wav_path, cap_sec, tmp_dir)
