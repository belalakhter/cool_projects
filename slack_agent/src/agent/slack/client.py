import os
import threading
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from ..alert.tracker import get_runner

app = App(token=os.environ["SLACK_BOT_TOKEN"])
runner = get_runner()

@app.event("message")
def handle_message_events(body, logger):
    """Handle all message events to track user activity"""
    try:
        event = body["event"]

        if event.get("subtype") or event.get("bot_id"):
            return

        channel_id = event.get("channel")
        user_id = event.get("user")

        if channel_id and user_id:

            runner.track_message(channel_id, user_id)

    except Exception as e:
        logger.error(f"Error handling message event: {e}")

@app.command("/accept-alerts")
def handle_accept_alerts(ack, respond, command, client):
    """Handle the /accept-alerts slash command"""
    ack()
    try:
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        user_name = command["user_name"]
        text = command.get("text", "").strip()

        runner.add_alert(user_id, channel_id, user_name)

        try:
            channel_info = client.conversations_info(channel=channel_id)
            channel_name = f"#{channel_info['channel']['name']}"
        except:
            channel_name = "this channel"

        tracking_text = f"tracking activity in {channel_name}"
        if text:
            tracking_text = f"tracking `{text}` in {channel_name}"

        respond({
            "response_type": "in_channel",
            "text": f" Accepted alert from {user_name}. Now {tracking_text} for the next 12 hours. You'll receive a DM with the activity report."
        })
        client.chat_postMessage(
            channel=user_id,
            text=f" Alert activated! I'm now tracking activity in {channel_name} for the next 12 hours. You'll receive a detailed report via DM when the tracking period ends."
        )

    except Exception as e:
        respond({
            "response_type": "ephemeral",
            "text": f"❌ Error setting up alert: {str(e)}"
        })

@app.command("/cancel-alert")
def handle_cancel_alert(ack, respond, command):
    """Handle the /cancel-alert slash command"""
    ack()

    try:
        user_id = command["user_id"]
        user_name = command["user_name"]

        if runner.cancel_alert(user_id):
            respond({
                "response_type": "ephemeral",
                "text": f" Alert cancelled for {user_name}."
            })
        else:
            respond({
                "response_type": "ephemeral",
                "text": f" No active alert found for {user_name}."
            })

    except Exception as e:
        respond({
            "response_type": "ephemeral",
            "text": f" Error cancelling alert: {str(e)}"
        })

@app.command("/list-alerts")
def handle_list_alerts(ack, respond, command):
    """Handle the /list-alerts slash command"""
    ack()

    try:
        user_id = command["user_id"]
        active_alerts = runner.get_active_alerts()

        if not active_alerts:
            respond({
                "response_type": "ephemeral",
                "text": " No active alerts currently running."
            })
            return

        user_alerts = [alert for uid, alert in active_alerts.items() if uid == user_id]

        if not user_alerts:
            respond({
                "response_type": "ephemeral",
                "text": " You don't have any active alerts."
            })
        else:
            alert = user_alerts[0]
            from datetime import datetime
            time_left = 12 * 3600 - (datetime.now() - alert['start_time']).total_seconds()
            hours_left = max(0, time_left / 3600)

            respond({
                "response_type": "ephemeral",
                "text": f" You have 1 active alert with {hours_left:.1f} hours remaining."
            })

    except Exception as e:
        respond({
            "response_type": "ephemeral",
            "text": f" Error listing alerts: {str(e)}"
        })

def start_socket_client():
    """Start the Socket Mode client"""
    try:
        handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
        print("Starting Slack Socket Mode client...")
        handler.start()
    except Exception as e:
        print(f"Error starting Socket Mode client: {e}")

def run_client():
    """Run the Slack client in a separate thread"""
    client_thread = threading.Thread(target=start_socket_client, daemon=True)
    client_thread.start()
    return client_thread
