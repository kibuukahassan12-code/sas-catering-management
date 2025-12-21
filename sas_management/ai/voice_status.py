def voice_ready():
    """
    Returns (ready: bool, reason: str)
    """
    try:
        import shutil

        ffmpeg_ok = shutil.which("ffmpeg") is not None
        if not ffmpeg_ok:
            return False, "ffmpeg not installed"

        try:
            from faster_whisper import WhisperModel  # type: ignore

            # Lightweight model load check; errors are treated as "unavailable"
            WhisperModel("base")
        except Exception:
            return False, "speech model unavailable"

        return True, "ready"
    except Exception as e:
        return False, str(e)


