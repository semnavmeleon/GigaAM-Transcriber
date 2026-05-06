import logging
import os
import shutil
import subprocess
from typing import List, Tuple

import numpy as np
import torch
from pydub import AudioSegment

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
HARD_CAP_SEC = 15

VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.ts', '.m2ts'}


def _is_video(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in VIDEO_EXTS


def _has_audio_stream(input_abs: str, ffmpeg_bin: str) -> bool:
    ffprobe_bin = shutil.which('ffprobe') or ffmpeg_bin.replace('ffmpeg', 'ffprobe')
    probe = subprocess.run(
        [ffprobe_bin, '-v', 'error',
         '-select_streams', 'a:0',
         '-show_entries', 'stream=codec_type',
         '-of', 'default=noprint_wrappers=1:nokey=1',
         input_abs],
        capture_output=True,
    )
    if probe.returncode == 0 and b'audio' in probe.stdout:
        return True
    info = subprocess.run(
        [ffmpeg_bin, '-v', 'quiet', '-i', input_abs],
        capture_output=True,
    )
    return b'Audio:' in info.stderr


def _load_pcm(path: str) -> AudioSegment:
    """Decode any audio/video file to 16 kHz mono PCM in memory — no temp file."""
    abs_path = os.path.abspath(path)
    ffmpeg_bin = shutil.which('ffmpeg') or 'ffmpeg'

    if _is_video(abs_path):
        if not _has_audio_stream(abs_path, ffmpeg_bin):
            raise RuntimeError(
                'В файле не найдена аудиодорожка. '
                'Возможно, файл содержит только видео без звука.'
            )

    cmd = [
        ffmpeg_bin, '-y',
        '-i', abs_path,
        '-map', '0:a:0',
        '-vn',
        '-f', 's16le',
        '-acodec', 'pcm_s16le',
        '-ar', str(SAMPLE_RATE),
        '-ac', '1',
        '-',
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace')
        raise RuntimeError(f'ffmpeg decode failed: {err[-400:]}')

    return AudioSegment(
        data=result.stdout,
        sample_width=2,
        frame_rate=SAMPLE_RATE,
        channels=1,
    )


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
    idx_ref: list,
) -> List[Tuple[str, float, float]]:
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


def _split_fixed_seg(audio: AudioSegment, chunk_sec: int, tmp_dir: str) -> List[Tuple[str, float, float]]:
    cap_ms = min(chunk_sec, HARD_CAP_SEC) * 1000
    total_ms = len(audio)
    chunks: List[Tuple[str, float, float]] = []
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


def _split_vad_seg(audio: AudioSegment, chunk_sec: int, tmp_dir: str) -> List[Tuple[str, float, float]]:
    cap_ms = min(chunk_sec, HARD_CAP_SEC) * 1000
    try:
        from silero_vad import load_silero_vad, get_speech_timestamps

        wav_tensor = _pydub_to_tensor(audio)
        vad_model = load_silero_vad()
        timestamps = get_speech_timestamps(wav_tensor, vad_model, sampling_rate=SAMPLE_RATE)

        if not timestamps:
            return _split_fixed_seg(audio, chunk_sec, tmp_dir)

        idx = [0]
        chunks: List[Tuple[str, float, float]] = []
        pending_start_ms: int | None = None
        pending_end_ms: int = 0
        pending_dur_ms: int = 0

        for ts in timestamps:
            seg_start_ms = int(ts["start"] * 1000 / SAMPLE_RATE)
            seg_end_ms = int(ts["end"] * 1000 / SAMPLE_RATE)
            seg_dur_ms = seg_end_ms - seg_start_ms

            if pending_start_ms is None:
                pending_start_ms = seg_start_ms
                pending_end_ms = seg_end_ms
                pending_dur_ms = seg_dur_ms
            elif pending_dur_ms + seg_dur_ms > cap_ms:
                for item in _sub_split(audio, pending_start_ms, pending_end_ms, tmp_dir, idx):
                    chunks.append(item)
                pending_start_ms = seg_start_ms
                pending_end_ms = seg_end_ms
                pending_dur_ms = seg_dur_ms
            else:
                pending_end_ms = seg_end_ms
                pending_dur_ms += seg_dur_ms

        if pending_start_ms is not None:
            for item in _sub_split(audio, pending_start_ms, pending_end_ms, tmp_dir, idx):
                chunks.append(item)

        return chunks if chunks else _split_fixed_seg(audio, chunk_sec, tmp_dir)

    except Exception as e:
        logger.warning("VAD failed (%s), falling back to fixed split", e)
        return _split_fixed_seg(audio, chunk_sec, tmp_dir)


def load_split(
    path: str,
    chunk_sec: int,
    tmp_dir: str,
    use_vad: bool,
) -> Tuple[float, List[Tuple[str, float, float]]]:
    """
    Decode audio/video in one ffmpeg pass, return (duration_sec, chunks).
    No intermediate file written — PCM lives in RAM only during this call.
    """
    audio = _load_pcm(path)
    duration = len(audio) / 1000.0
    if use_vad:
        chunks = _split_vad_seg(audio, chunk_sec, tmp_dir)
    else:
        chunks = _split_fixed_seg(audio, chunk_sec, tmp_dir)
    return duration, chunks
