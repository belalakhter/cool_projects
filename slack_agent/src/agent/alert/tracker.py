import os
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class AlertRunner:
    def __init__(self):
        self.slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        self.active_alerts = {}
        self.message_tracker = defaultdict(lambda: defaultdict(int))
        self.lock = threading.Lock()

    def add_alert(self, user_id, channel_id, user_name):
        """Add a user to the alert tracking list"""
        with self.lock:
            start_time = datetime.now()
            self.active_alerts[user_id] = {
                'channel_id': channel_id,
                'start_time': start_time,
                'user_name': user_name
            }


            if channel_id in self.message_tracker:
                self.message_tracker[channel_id].clear()

            print(f"Added alert for {user_name} ({user_id}) in channel {channel_id}")

            timer = threading.Timer(1000, self.send_report, args=[user_id])
            timer.daemon = True
            timer.start()

    def track_message(self, channel_id, user_id):
        """Track a message from a user in a channel"""
        with self.lock:
            if any(alert['channel_id'] == channel_id for alert in self.active_alerts.values()):
                self.message_tracker[channel_id][user_id] += 1
                print(f"Tracked message from {user_id} in {channel_id}. Total: {self.message_tracker[channel_id][user_id]}")

    def send_report(self, requesting_user_id):
        """Send DM report to the user who requested the alert"""
        try:
            with self.lock:
                if requesting_user_id not in self.active_alerts:
                    return

                alert_info = self.active_alerts[requesting_user_id]
                channel_id = alert_info['channel_id']
                user_name = alert_info['user_name']




                channel_info = self.slack_client.conversations_info(channel=channel_id)
                channel_name = channel_id



                message_counts = self.message_tracker.get(channel_id, {})

                if not message_counts:
                    report_text = f"12-Hour Activity Report for #{channel_name}\n\nNo messages were tracked in the last 12 hours."
                else:
                    sorted_users = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)

                    report_lines = [f"12-Hour Activity Report for #{channel_name}\n"]

                    for user_id, count in sorted_users:

                        user_info = self.slack_client.users_info(user=user_id)
                        display_name = user_id


                        report_lines.append(f"• {display_name}: {count} messages")

                    total_messages = sum(message_counts.values())
                    total_users = len(message_counts)
                    report_lines.append(f"\nTotal: {total_messages} messages from {total_users} users*")

                    report_text = "\n".join(report_lines)

                self.slack_client.chat_postMessage(
                    channel=requesting_user_id,
                    text=report_text
                )

                print(f"Sent report to {user_name} ({requesting_user_id})")


                del self.active_alerts[requesting_user_id]
                if channel_id in self.message_tracker:
                    del self.message_tracker[channel_id]

        except SlackApiError as e:
            print(f"Error sending report: {e}")
        except Exception as e:
            print(f"Unexpected error in send_report: {e}")

    def get_active_alerts(self):
        """Get list of active alerts"""
        with self.lock:
            return dict(self.active_alerts)

    def cancel_alert(self, user_id):
        """Cancel an active alert"""
        with self.lock:
            alert_info = self.active_alerts.get(user_id)
            if alert_info:
                channel_id = alert_info.get('channel_id')
                del self.active_alerts[user_id]
                if channel_id and channel_id in self.message_tracker:
                    del self.message_tracker[channel_id]
                return True
            return False


alert_runner = AlertRunner()

def get_runner():
    """Get the global alert runner instance"""
    return alert_runner
