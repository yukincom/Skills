# -*- coding: utf-8 -*-
"""voice_server.py
新しい Mac (M4) で動かす音声生成専用サーバー
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
import uuid

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)
VOICE_STORAGE_DIR = os.getenv("VOICE_STORAGE_DIR", "/tmp/voice_gen_store")
VOICE_TMP_DIR = os.getenv("VOICE_TMP_DIR", "/tmp/voice_gen")
os.makedirs(VOICE_STORAGE_DIR, exist_ok=True)
os.makedirs(VOICE_TMP_DIR, exist_ok=True)


def resolve_voice_name(requested_voice):
    """利用可能な voice 名に解決する（完全一致→大文字小文字無視）。"""
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True)
    available = []
    for line in result.stdout.split("\n"):
        if not line.strip():
            continue
        parts = line.split()
        if parts:
            available.append(parts[0])

    if requested_voice in available:
        return requested_voice

    lower_map = {v.lower(): v for v in available}
    if requested_voice.lower() in lower_map:
        return lower_map[requested_voice.lower()]

    return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "voice_generator", "storage_dir": VOICE_STORAGE_DIR, "tmp_dir": VOICE_TMP_DIR})


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(silent=True) or {}

        text = data.get("text", "").strip()
        requested_voice = data.get("voice", "O-Ren")
        rate = max(100, min(300, int(data.get("rate", 160))))
        pitch = max(10, min(90, int(data.get("pitch", 45))))

        if not text:
            return jsonify({"success": False, "error": "text is required"}), 400

        resolved_voice = resolve_voice_name(requested_voice)
        if not resolved_voice:
            return jsonify({"success": False, "error": f"voice not available: {requested_voice}"}), 400

        print(f"[VOICE] request text={text[:30]} requested={requested_voice} resolved={resolved_voice} rate={rate} pitch={pitch}")

        voice_id = f"{int(time.time())}_{uuid.uuid4().hex}"
        tmp_aiff = os.path.join(VOICE_TMP_DIR, f"{voice_id}.aiff")
        tmp_wav = os.path.join(VOICE_TMP_DIR, f"{voice_id}.wav")
        final_wav = os.path.join(VOICE_STORAGE_DIR, f"{voice_id}.wav")

        clipped = text[:120]
        embedded_text = f"[[pbas {pitch}]][[rate {rate}]]{clipped}"

        subprocess.run(["say", "-v", resolved_voice, "-o", tmp_aiff, embedded_text], check=True, capture_output=True)
        subprocess.run(
            ["afconvert", "-f", "WAVE", "-d", "LEI16@44100", "--src-complexity", "bats", "-c", "1", tmp_aiff, tmp_wav],
            check=True,
            capture_output=True,
        )

        with open(tmp_wav, "rb") as f:
            wav_data = f.read()

        sha256_hash = hashlib.sha256(wav_data).hexdigest()
        with open(final_wav, "wb") as f:
            f.write(wav_data)

        os.remove(tmp_aiff)
        os.remove(tmp_wav)

        print(f"[VOICE] done voice_id={voice_id} size={len(wav_data)} tmp_aiff={tmp_aiff} tmp_wav={tmp_wav} final_wav={final_wav}")

        return jsonify(
            {
                "success": True,
                "voice_id": voice_id,
                "size": len(wav_data),
                "sha256": sha256_hash,
                "download_path": f"/voice/{voice_id}",
                "settings": {
                    "text": clipped,
                    "voice": resolved_voice,
                    "requested_voice": requested_voice,
                    "rate": rate,
                    "pitch": pitch,
                    "engine": "m4-voice-server",
                },
            }
        )

    except Exception as e:
        print(f"[VOICE] error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/voice/<voice_id>", methods=["GET"])
def get_voice(voice_id):
    wav_path = os.path.join(VOICE_STORAGE_DIR, f"{voice_id}.wav")
    if not os.path.exists(wav_path):
        return jsonify({"success": False, "error": "voice not found"}), 404

    return send_file(wav_path, mimetype="audio/wav", as_attachment=True, download_name="voice.wav")


@app.route("/voices", methods=["GET"])
def list_voices():
    try:
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True)
        voices = []
        for line in result.stdout.split("\n"):
            if line.strip():
                parts = line.split()
                voices.append({"name": parts[0], "language": parts[1] if len(parts) > 1 else "unknown"})
        return jsonify({"success": True, "voices": voices})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/cleanup", methods=["POST"])
def cleanup():
    payload = request.get_json(silent=True) or {}
    max_age_seconds = int(payload.get("max_age_seconds", 3600))
    keep_latest = bool(payload.get("keep_latest", True))

    files = []
    for filename in os.listdir(VOICE_STORAGE_DIR):
        if filename.endswith(".wav"):
            path = os.path.join(VOICE_STORAGE_DIR, filename)
            files.append((path, os.path.getmtime(path)))

    files.sort(key=lambda x: x[1], reverse=True)
    now = time.time()
    deleted = 0

    for idx, (path, mtime) in enumerate(files):
        if keep_latest and idx == 0:
            continue
        if now - mtime > max_age_seconds:
            os.remove(path)
            deleted += 1

    return jsonify({"success": True, "deleted": deleted})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
