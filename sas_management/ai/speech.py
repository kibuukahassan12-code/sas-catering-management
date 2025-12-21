"""
SAS AI Speech-to-Text endpoint (backend STT for browser MediaRecorder).

Browser sends a short WebM audio clip; we convert it to WAV via ffmpeg
and run faster-whisper to obtain a transcription.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required, current_user

from sas_management.models import UserRole
from sas_management.utils import role_required
from sas_management.ai.feature_guard import log_if_disabled
from sas_management.ai.voice_status import voice_ready
from sas_management.ai.permission_checks import can_use_ai_voice

speech_bp = Blueprint("ai_speech", __name__, url_prefix="/ai")

_FASTER_WHISPER_MODEL = None


def _get_faster_whisper_model():
    """
    Lazily load and cache the faster-whisper model.
    """
    global _FASTER_WHISPER_MODEL
    if _FASTER_WHISPER_MODEL is not None:
        return _FASTER_WHISPER_MODEL

    from faster_whisper import WhisperModel  # type: ignore

    model_size = current_app.config.get("AI_SPEECH_MODEL", "base")
    _FASTER_WHISPER_MODEL = WhisperModel(model_size, device="cpu")
    return _FASTER_WHISPER_MODEL


def _transcribe_wav_with_faster_whisper(wav_path: str) -> Optional[str]:
    """
    Run faster-whisper on a WAV file and return plain text.
    """
    model = _get_faster_whisper_model()
    segments, _info = model.transcribe(wav_path)
    text_parts = [seg.text for seg in segments]
    text = " ".join(text_parts).strip()
    return text or None


@speech_bp.route("/speech-to-text", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager, UserRole.Staff)
def speech_to_text():
    """
    Accept audio from the browser and return recognized text (crash-proof).

    Request (multipart/form-data):
        - audio: WebM audio blob recorded via MediaRecorder

    Responses:
        200: { "text": "<recognized speech>" }  (empty string if no speech)
        400: { "text": "", "error": "Speech-to-text failed" }  on error
    """
    try:
        # Phase 2: observe-only voice feature flag logging
        try:
            log_if_disabled("voice_enabled", request.path)
        except Exception:
            pass  # Logging failure should not block request
        
        # Permission check - return message, never raise
        try:
            if not can_use_ai_voice(current_user):
                return jsonify({"text": "", "error": "🔒 Your role does not have access to this AI feature."}), 403
        except Exception as e:
            current_app.logger.warning("AI voice permission check error", exc_info=True)
            return jsonify({"text": "", "error": "Permission check failed"}), 403

    if "audio" not in request.files:
        return jsonify({"text": "", "error": "Speech-to-text failed"}), 400

    file = request.files["audio"]
    if not file or not file.filename:
        return jsonify({"text": "", "error": "Speech-to-text failed"}), 400

    tmp_input = None
    tmp_wav = None
    try:
        # Save incoming audio as temporary .webm (or original extension)
        suffix = os.path.splitext(file.filename)[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file.save(tmp)
            tmp_input = tmp.name

        base, _ = os.path.splitext(tmp_input)
        tmp_wav = base + ".wav"

        # Convert WebM -> WAV using ffmpeg
        current_app.logger.info(
            f"SAS AI speech_to_text: converting {tmp_input} -> {tmp_wav} with ffmpeg"
        )
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_input, tmp_wav],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            current_app.logger.error(
                "SAS AI speech_to_text ffmpeg error: %s",
                e.stderr.decode(errors="ignore"),
            )
            return jsonify({"text": "", "error": "Speech-to-text failed"}), 400

        # Transcribe WAV with faster-whisper
        try:
            text = _transcribe_wav_with_faster_whisper(tmp_wav)
        except Exception as e:
            current_app.logger.error(
                f"SAS AI speech_to_text transcription error: {e}", exc_info=True
            )
            return jsonify({"text": "", "error": "Speech-to-text failed"}), 400

        if not text:
            # No speech detected is a valid, non-error outcome
            current_app.logger.info("SAS AI speech_to_text: no speech detected")
            return jsonify({"text": ""}), 200

        current_app.logger.info("SAS AI speech_to_text: transcription succeeded")
        return jsonify({"text": text}), 200

    except Exception as e:
        # Catch-all to avoid leaking stack traces to clients
        current_app.logger.error(
            f"SAS AI speech_to_text unexpected error: {e}", exc_info=True
        )
        return jsonify({"text": "", "error": "Speech-to-text failed"}), 400
    finally:
        for path in (tmp_input, tmp_wav):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


@speech_bp.route("/voice-status", methods=["GET"])
@login_required
def voice_status():
    """
    Lightweight health check for SAS AI voice input (crash-proof).

    Returns JSON: { "ready": bool, "reason": str }
    """
    try:
        ready, reason = voice_ready()
        return jsonify({"ready": bool(ready), "reason": str(reason or "")}), 200
    except Exception as e:
        # Fail closed but do not raise or log stack traces
        current_app.logger.warning("Voice status check error", exc_info=True)
        return jsonify({"ready": False, "reason": "Voice feature unavailable"}), 200

