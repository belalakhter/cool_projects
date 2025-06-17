import os
from flask import Flask, request, jsonify
from .slack.client import run_client
from .alert.tracker import get_runner



slack_token = os.environ["SLACK_BOT_TOKEN"]
app_token = os.environ["SLACK_APP_TOKEN"]

def create_flask_app():
    app = Flask(__name__)
    runner = get_runner()

    @app.route("/slack/accept-alert", methods=["POST"])
    def slash_command():
        """Handle the /accept-alerts slash command via HTTP"""
        data = request.form
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        channel_id = data.get("channel_id")
        text = data.get("text", "").strip()

        try:
            runner.add_alert(user_id, channel_id, user_name)

            tracking_text = "tracking activity"
            if text:
                tracking_text = f"tracking `{text}`"

            return jsonify({
                "response_type": "in_channel",
                "text": f"Accepted alert from {user_name}. Now {tracking_text} for the next 12 hours. You'll receive a DM with the activity report."
            })

        except Exception as e:
            return jsonify({
                "response_type": "ephemeral",
                "text": f"❌ Error setting up alert: {str(e)}"
            })

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        active_alerts = runner.get_active_alerts()
        return jsonify({
            "status": "healthy",
            "active_alerts": len(active_alerts),
            "runner_active": True
        })

    @app.route("/alerts", methods=["GET"])
    def list_alerts():
        """List all active alerts"""
        active_alerts = runner.get_active_alerts()
        return jsonify({
            "active_alerts": len(active_alerts),
            "alerts": [
                {
                    "user_name": alert["user_name"],
                    "channel_id": alert["channel_id"],
                    "start_time": alert["start_time"].isoformat()
                }
                for alert in active_alerts.values()
            ]
        })

    return app

if __name__ == "__main__":
    print("Starting Slack Socket Mode client...")
    client_thread = run_client()

    app = create_flask_app()
    port = int(os.getenv("PORT", 3000))

    print(f"Starting Flask server on port {port}...")

    app.run(host="0.0.0.0", port=port)
