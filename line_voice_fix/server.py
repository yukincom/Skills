from flask import Flask, Response, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

import os
import requests
import traceback

from ai_handler import get_ai_response
from memory_manager import RobotMemory

load_dotenv(".env")

app = Flask(__name__)
memory = RobotMemory()
pending_notifications = []

VOICE_SERVER_URL = os.getenv("VOICE_SERVER_URL", "http://192.168.1.48:5001")
VOICE_REQUEST_TIMEOUT = int(os.getenv("VOICE_REQUEST_TIMEOUT", "30"))
VOICE_DEFAULT_NAME = os.getenv("VOICE_DEFAULT_NAME", "O-Ren")

voice_state = {
    "latest_voice_id": None,
    "latest_voice_url": None,
    "latest_ready": False,
    "latest_sha256": None,
    "latest_settings": None,
}

RENDER_URL = "https://line-family-bot-n1gp.onrender.com"
POLL_INTERVAL = 10


def generate_voice(text, rate=160, pitch=45, voice=None):
    """M4側 voice_server.py の /generate を直接呼ぶ。"""
    try:
        selected_voice = voice or VOICE_DEFAULT_NAME
        response = requests.post(
            f"{VOICE_SERVER_URL}/generate",
            json={"text": text, "voice": selected_voice, "rate": rate, "pitch": pitch},
            timeout=VOICE_REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        result = response.json()
        if not result.get("success"):
            print(f"❌ voice_server generation failed: {result.get('error')}")
            return None

        voice_id = result["voice_id"]
        download_path = result.get("download_path", f"/voice/{voice_id}")
        source_url = f"{VOICE_SERVER_URL}{download_path}"

        print(f"[VOICE] generated voice_id={voice_id} requested={selected_voice} used={result.get('settings', {}).get('voice')}")

        return {
            "voice_id": voice_id,
            "source_url": source_url,
            "size": result["size"],
            "sha256": result["sha256"],
            "settings": result["settings"],
        }
    except requests.exceptions.Timeout:
        print(f"❌ timeout: voice_server({VOICE_SERVER_URL})")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ connection error: voice_server({VOICE_SERVER_URL})")
        return None
    except Exception as e:
        print(f"❌ generate_voice error: {e}")
        return None


def cleanup_old_voice_files(max_age_seconds=3600, keep_latest=True):
    """M4側 voice_server.py の /cleanup を直接呼ぶ。"""
    try:
        response = requests.post(
            f"{VOICE_SERVER_URL}/cleanup",
            json={"max_age_seconds": max_age_seconds, "keep_latest": keep_latest},
            timeout=VOICE_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return int(response.json().get("deleted", 0))
    except Exception as e:
        print(f"⚠️ cleanup error: {e}")
        return 0


def process_notification(user_id, message):
    global voice_state

    mama_id = os.getenv("MAMA_LINE_USER_ID", "")
    papa_id = os.getenv("PAPA_LINE_USER_ID", "")

    if user_id == mama_id and mama_id != "未設定":
        sender_name = "お母さん"
    elif user_id == papa_id and papa_id != "未設定":
        sender_name = "お父さん"
    else:
        sender_name = "家族"

    if "帰る" in message or "帰ります" in message:
        notification_message = f"{sender_name}がそろそろ帰ってくるってー！"
    elif "遅い" in message or "遅く" in message:
        notification_message = f"{sender_name}、今夜はちょっと遅いって言ってるよ〜"
    elif "よろしく" in message:
        notification_message = f"{sender_name}からよろしくって言ってるよ〜"
    elif "買" in message:
        notification_message = f"{sender_name}が買ってきてほしいものある？って聞いてるよ〜"
    else:
        notification_message = f"{sender_name}からメッセージだぜ。「{message}」だってさ！"

    # 新規生成開始時点で ready を false にし、古い音声を配らない
    voice_state["latest_ready"] = False

    voice_result = generate_voice(notification_message, rate=160, pitch=45, voice=VOICE_DEFAULT_NAME)

    if voice_result:
        voice_state["latest_voice_id"] = voice_result["voice_id"]
        voice_state["latest_voice_url"] = voice_result["source_url"]
        voice_state["latest_sha256"] = voice_result["sha256"]
        voice_state["latest_settings"] = voice_result["settings"]
        voice_state["latest_ready"] = True

    notification_data = {
        "sender": sender_name,
        "message": notification_message,
        "original_text": message,
        "voice_id": voice_result["voice_id"] if voice_result else None,
        "voice_url": voice_result["source_url"] if voice_result else None,
    }
    pending_notifications.append(notification_data)
    memory.add_conversation("system", f"[LINE通知] {sender_name}", message)


def poll_render():
    try:
        response = requests.get(f"{RENDER_URL}/poll", timeout=60)
        response.raise_for_status()
        data = response.json()

        if data.get("notification"):
            n = data["notification"]
            process_notification(n.get("user_id", ""), n.get("message", ""))
    except requests.exceptions.Timeout:
        pass
    except Exception as e:
        print(f"[ERROR] poll_render: {e}")


def scheduled_cleanup():
    try:
        cleanup_old_voice_files(max_age_seconds=3600, keep_latest=True)
    except Exception as e:
        print(f"[ERROR] scheduled_cleanup: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(poll_render, "interval", seconds=POLL_INTERVAL)
scheduler.add_job(scheduled_cleanup, "interval", hours=1)
scheduler.start()


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "version": "2.3", "memory": "local", "voice_server": VOICE_SERVER_URL, "voice_default": VOICE_DEFAULT_NAME})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_text = data["text"]
        speaker = data.get("speaker", "yuki")

        context = memory.get_context(speaker, query=user_text)
        ai_response = get_ai_response(user_text, context, speaker)
        memory.add_conversation(speaker, user_text, ai_response)

        return jsonify({"success": True, "response": ai_response})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/notify/pending", methods=["GET"])
def get_pending_notifications():
    global pending_notifications
    if pending_notifications:
        return jsonify({"success": True, "notification": pending_notifications.pop(0)})
    return jsonify({"success": True, "notification": None})


@app.route("/voice/latest", methods=["GET"])
def get_latest_voice():
    global voice_state

    if not voice_state.get("latest_ready"):
        return jsonify({"success": False, "status": "not_ready"}), 202

    voice_url = voice_state.get("latest_voice_url")
    if not voice_url:
        return jsonify({"success": False, "status": "missing"}), 404

    try:
        remote_response = requests.get(voice_url, timeout=30)
        if remote_response.status_code != 200:
            return jsonify({"success": False, "status": "upstream_error"}), 502

        return Response(
            remote_response.content,
            mimetype="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=voice.wav",
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Voice-Id": str(voice_state.get("latest_voice_id", "")),
                "X-Voice-Name": str((voice_state.get("latest_settings") or {}).get("voice", "")),
            },
        )
    except requests.RequestException:
        return jsonify({"success": False, "status": "upstream_unreachable"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
