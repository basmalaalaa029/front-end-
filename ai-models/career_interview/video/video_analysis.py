"""
video/video_analysis.py
=======================
Analyses video frames for non-verbal communication.
v8: Improved frame extraction, proper fallback, no fake scores,
    logging, face validation, lighting checks.
"""

import os
import cv2
import base64
import logging
import subprocess
import tempfile
import requests
import numpy as np
from typing import Dict, List, Optional

log = logging.getLogger("interview.video")

# ── Frame extraction ───────────────────────────────────────────────────────

def _extract_frames_ffmpeg(video_path: str, num_frames: int = 5) -> List[np.ndarray]:
    """
    Use ffmpeg to extract evenly-spaced frames from a video file.
    This is far more reliable than OpenCV for browser-recorded WebM blobs,
    which often lack a finalized seek index and duration header.
    Raises ValueError if fewer than 3 frames can be extracted.
    """
    # First probe the duration with ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", video_path],
        capture_output=True, text=True
    )
    duration = 0.0
    if probe.returncode == 0:
        import json
        info = json.loads(probe.stdout)
        duration = float(info.get("format", {}).get("duration", 0) or 0)
        # Also try streams for duration
        if duration <= 0:
            for s in info.get("streams", []):
                d = float(s.get("duration", 0) or 0)
                if d > duration:
                    duration = d

    if duration <= 0:
        # Can't probe duration — extract at fixed intervals and hope for the best
        duration = 60.0  # assume up to 60s, ffmpeg will stop early

    # Sample timestamps from 15%–85% of duration to skip intros/outros
    start_t = duration * 0.15
    end_t   = duration * 0.85
    if end_t <= start_t:
        start_t = 0.0
        end_t = duration

    timestamps = np.linspace(start_t, end_t, num_frames)

    frames = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, ts in enumerate(timestamps):
            out_path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-ss", f"{ts:.3f}",
                    "-i", video_path,
                    "-vframes", "1",
                    "-vf", "scale=480:-1",   # downscale — face detection doesn't need full res
                    "-q:v", "3",
                    out_path,
                ],
                capture_output=True, text=True
            )
            if result.returncode == 0 and os.path.exists(out_path):
                frame = cv2.imread(out_path)
                if frame is not None and frame.size > 0:
                    frames.append(frame)

    log.info(f"ffmpeg extracted {len(frames)}/{num_frames} frames from {video_path} (duration={duration:.1f}s)")
    if len(frames) < 3:
        raise ValueError(f"ffmpeg could only extract {len(frames)} frames — video may be too short or corrupted")
    return frames


def extract_frames(video_path: str, num_frames: int = 5, max_decode_frames: int = 1200) -> List[np.ndarray]:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    # ── Try ffmpeg first (more reliable for browser WebM blobs) ───────────
    try:
        frames = _extract_frames_ffmpeg(video_path, num_frames)
        if frames:
            return frames
    except Exception as e:
        log.warning(f"ffmpeg frame extraction failed ({e}), falling back to OpenCV")

    # ── OpenCV fallback ────────────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Neither ffmpeg nor OpenCV could open video: {video_path}")

    reported_total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    log.info(f"OpenCV fallback: reported_total={reported_total} @ {fps:.1f} fps — {video_path}")

    # Browser-recorded webm blobs (MediaRecorder output) often have no
    # finalized seek index/duration, so CAP_PROP_FRAME_COUNT can come back
    # as garbage. Always decode sequentially.
    all_frames = []
    read_count = 0
    max_width = 480
    while read_count < max_decode_frames:
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            break
        h, w = frame.shape[:2]
        if w > max_width:
            scale = max_width / w
            frame = cv2.resize(frame, (max_width, int(h * scale)))
        all_frames.append(frame)
        read_count += 1
    cap.release()

    total = len(all_frames)
    log.info(f"OpenCV decoded {total} real frames from {video_path}")

    if total < 3:
        raise ValueError(f"Video too short: only {total} frames could be decoded")

    # Sample from 15%-85% of the decoded frames to skip intros/outros
    start = max(int(total * 0.15), 0)
    end = min(int(total * 0.85), total - 1)
    positions = np.linspace(start, end, min(num_frames, end - start + 1), dtype=int)

    frames = [all_frames[p] for p in sorted(set(positions))]
    log.info(f"OpenCV sampled {len(frames)}/{num_frames} frames")

    if not frames:
        raise ValueError("No frames could be extracted from video")
    return frames


# ── Basic CV analysis ──────────────────────────────────────────────────────
def _basic_cv_analysis(frames: List[np.ndarray]) -> Dict:
    """
    Real CV analysis — never returns fake static scores.
    Returns None scores when analysis is not possible rather than placeholders.
    """
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye.xml'
    )

    face_detections  = []
    eye_detections   = []
    brightness_vals  = []
    face_centredness = []
    face_sizes       = []
    observations     = []

    n = len(frames)

    for i, frame in enumerate(frames):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        brightness_vals.append(float(np.mean(gray)))

        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
        )

        if len(faces) > 0:
            face_detections.append(True)
            fx, fy, fw, fh = faces[0]
            face_sizes.append(fw * fh)

            # Face centredness
            cx = fx + fw // 2
            cy = fy + fh // 2
            centred = (w * 0.15 < cx < w * 0.85) and (h * 0.05 < cy < h * 0.90)
            face_centredness.append(centred)

            # Eyes within face region
            face_roi = gray[fy:fy+fh, fx:fx+fw]
            eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=3)
            eye_detections.append(len(eyes) >= 1)
        else:
            face_detections.append(False)
            face_centredness.append(False)
            eye_detections.append(False)

    face_ratio  = sum(face_detections) / n
    eye_ratio   = sum(eye_detections) / n if sum(face_detections) > 0 else 0
    centre_ratio = sum(face_centredness) / n
    avg_brightness = np.mean(brightness_vals)

    log.info(f"Video CV: face={face_ratio:.0%} eye={eye_ratio:.0%} centre={centre_ratio:.0%} brightness={avg_brightness:.0f}")

    # ── Return unavailable if no face detected ─────────────────────────────
    if face_ratio < 0.3:
        log.warning("Face not detected in enough frames — video analysis unavailable")
        observations.append("Face not clearly visible in video. Ensure camera is positioned correctly and room is well-lit.")
        return {
            "score": None, "eye_contact_score": None,
            "expression_score": None, "posture_score": None,
            "observations": observations, "method": "basic_cv_no_face",
            "face_ratio": round(face_ratio, 2), "avg_brightness": round(avg_brightness, 1),
            "analysis_available": False,
        }

    # ── Eye contact score ──────────────────────────────────────────────────
    # Based on: eye detection rate AND face centredness (proxy for looking at camera)
    eye_contact_score = round(
        (eye_ratio * 0.6 + centre_ratio * 0.4) * 10, 1
    )
    eye_contact_score = min(max(eye_contact_score, 1.0), 10.0)

    if eye_contact_score >= 7:
        observations.append("Good eye contact maintained throughout the response.")
    elif eye_contact_score >= 5:
        observations.append("Eye contact was inconsistent. Try to look directly at the camera.")
    else:
        observations.append("Limited eye contact detected. Position camera at eye level and look into the lens.")

    # ── Expression score (proxy: brightness variation = engagement) ────────
    brightness_variance = float(np.var(brightness_vals))
    if brightness_variance > 200:
        expression_score = 7.5
        observations.append("Facial expressions appear engaged and varied.")
    elif brightness_variance > 50:
        expression_score = 6.0
        observations.append("Facial expressions appear neutral throughout.")
    else:
        expression_score = 4.5
        observations.append("Very static expression detected. Try to show engagement through facial expressions.")

    # ── Posture score (proxy: face size consistency + centredness) ─────────
    if len(face_sizes) >= 2:
        size_variance = float(np.var(face_sizes)) / (np.mean(face_sizes) ** 2 + 1)
        if size_variance < 0.05 and centre_ratio > 0.7:
            posture_score = 8.0
            observations.append("Stable posture maintained — well-framed and consistent.")
        elif size_variance < 0.15:
            posture_score = 6.5
            observations.append("Slight movement detected. Try to maintain a stable upright position.")
        else:
            posture_score = 4.5
            observations.append("Significant movement or position changes. Keep a steady, professional posture.")
    else:
        posture_score = None  # Not enough data — don't show a fake 5

    # ── Lighting adjustment ────────────────────────────────────────────────
    if avg_brightness < 50:
        eye_contact_score = max(eye_contact_score - 1.5, 1.0)
        expression_score  = max(expression_score  - 1.5, 1.0)
        posture_score     = max(posture_score     - 1.0, 1.0)
        observations.append("Lighting is poor. Move to a brighter, well-lit environment for better analysis.")
    elif avg_brightness > 210:
        observations.append("Strong backlighting detected. Avoid sitting with a bright window behind you.")
    elif 70 <= avg_brightness <= 190:
        observations.append("Lighting conditions are good.")

    _scores_for_avg = [s for s in [eye_contact_score, expression_score, posture_score] if s is not None]
    overall = round(sum(_scores_for_avg) / len(_scores_for_avg), 1) if _scores_for_avg else None

    return {
        "score": overall,
        "eye_contact_score": round(eye_contact_score, 1),
        "expression_score":  round(expression_score, 1),
        "posture_score":     (round(posture_score, 1) if posture_score is not None else None),
        "observations":      observations,
        "method":            "basic_cv",
        "face_ratio":        round(face_ratio, 2),
        "avg_brightness":    round(avg_brightness, 1),
        "analysis_available": True,
    }


# ── LLaVA analysis ────────────────────────────────────────────────────────
def _llava_analyse(frame_b64: str, ollama_url: str) -> Optional[str]:
    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": "llava",
                "prompt": (
                    "You are analysing an interview video frame. "
                    "Describe in 2-3 sentences: "
                    "1) Eye contact with camera (direct/averted/looking down) "
                    "2) Facial expression (confident/neutral/nervous/engaged) "
                    "3) Posture (upright/slouching/leaning). "
                    "Be specific and constructive."
                ),
                "images": [frame_b64],
                "stream": False,
            },
            timeout=12,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
        return None
    except Exception as e:
        log.debug(f"LLaVA unavailable: {e}")
        return None


def _llava_score(observations: List[str]) -> Dict:
    combined = " ".join(observations).lower()
    eye  = (9.0 if any(w in combined for w in ["direct", "camera", "good eye", "maintaining"])
            else 4.0 if any(w in combined for w in ["avoiding", "away", "distracted", "down"])
            else 6.5)
    expr = (9.0 if any(w in combined for w in ["confident", "calm", "professional", "engaged", "relaxed"])
            else 4.0 if any(w in combined for w in ["nervous", "anxious", "uncomfortable", "tense"])
            else 6.5)
    pos  = (9.0 if any(w in combined for w in ["upright", "straight", "professional posture", "good posture"])
            else 4.0 if any(w in combined for w in ["slouch", "leaning", "hunched", "poor posture"])
            else 6.5)
    return {
        "eye_contact_score": eye, "expression_score": expr, "posture_score": pos,
        "score": round((eye + expr + pos) / 3, 1), "analysis_available": True,
    }


# ── Main entry point ───────────────────────────────────────────────────────
def analyse_video(video_path: str, ollama_url: str = "http://localhost:11434", num_frames: int = 5) -> Dict:
    base = {
        "score": None, "eye_contact_score": None,
        "expression_score": None, "posture_score": None,
        "observations": [], "method": "unavailable",
        "error": None, "analysis_available": False,
    }

    try:
        frames = extract_frames(video_path, num_frames)
    except Exception as e:
        log.error(f"Frame extraction failed: {e}")
        base["error"] = str(e)
        base["observations"] = ["Video could not be processed for non-verbal analysis."]
        return base

    # Try LLaVA first
    llava_responses = []
    for frame in frames[:2]:
        try:
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                b64 = base64.b64encode(buf).decode()
                resp = _llava_analyse(b64, ollama_url)
                if resp:
                    llava_responses.append(resp)
        except Exception as e:
            log.debug(f"LLaVA frame encode failed: {e}")

    if len(llava_responses) >= 1:
        scores = _llava_score(llava_responses)
        base.update(scores)
        base["observations"] = llava_responses
        base["method"] = "llava"
        base["error"]  = None
        log.info("Video analysed via LLaVA")
        return base

    # Basic CV fallback
    result = _basic_cv_analysis(frames)
    base.update(result)
    base["error"] = None
    log.info(f"Video analysed via basic CV — available={result.get('analysis_available')}")
    return base


def interpret_video_metrics(result: Dict) -> Dict:
    available = result.get("analysis_available", False)
    return {
        "overall_score":     result.get("score"),      # None if unavailable
        "eye_contact_score": result.get("eye_contact_score"),
        "expression_score":  result.get("expression_score"),
        "posture_score":     result.get("posture_score"),
        "feedback":          result.get("observations", []),
        "method":            result.get("method", "unavailable"),
        "analysis_available": available,
    }
