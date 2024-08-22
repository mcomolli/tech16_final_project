import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from openai_functions import chat

# Get environment variables
load_dotenv()

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

@app.action("button_click")
def action_button_click(body, ack, say):
    # Acknowledge the action
    ack()
    say(f"<@{body['user']['id']}> clicked the button")

@app.event("app_mention")
def action_app_mention(body, say):
    message_content = body['event']['text'][14:]
    message_response = chat(message_content)
    say(message_response)

@app.event("message")
def handle_message(logger):
    logger.info("Message was sent!")

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()