from app import app
from slackclient import SlackClient

#slack_client = SlackClient(app.config['SLACK_TOKEN'])

def send_message(channel_id, message):
    slack_client = SlackClient(app.config['SLACK_BOT_TOKEN'])
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        username='OpsBot',
        icon_emoji=':robot_face:'
    )
