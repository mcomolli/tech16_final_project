import os
import asyncio
from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from dotenv import load_dotenv
from openai_functions import chat

# Get environment variables
load_dotenv()

# Initializes your app with your bot token and signing secret
app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)
    
# ASYNC IMPLEMENTATION OF TECHNICAL_TO_BUSINESS
@app.shortcut("technical_to_business")
async def open_modal(ack, shortcut, client, body):
    # Acknowledge the shortcut request
    await ack()

    # Immediately open a basic modal to avoid trigger_id expiration
    try:
        response = await client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "loading_modal",
                "title": {"type": "plain_text", "text": "Processing..."},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "Processing your request..."}
                    }
                ]
            }
        )
    except SlackApiError as e:
        print(f"Error opening modal: {e.response['error']}")

    # Perform the longer tasks after opening the modal
    technical_text = body['message']['text']

    # Get user profile info and fetch user title
    user_profile = await client.users_profile_get(user="U07HY9VPHEE")
    user_title = user_profile['profile'].get('title', 'User')

    # Generate the nontechnical summary
    nontechnical_text = chat(f"""Someone working as a {user_title} needs to better understand the content of the following message. 
                                Rewrite it according to the typical level of understanding of someone in this role. Here's the text: {technical_text}.
                                When in doubt, assume the recipient has less technical knowledge.
                                If you use markdown, follow these guidelines: single asterisk (*) for bold, single underscore (_) for italics. Do not use double asterisks (**) or titles (#, ##, or ###).""")
    
    # Get a list of topics mentioned in the message
    topics = chat("Return a comma-separated list of no more than 5 topics covered in the original text. Include the topics separated by commas with no other text. Make sure the topics are specific enough.")
    topics_list = topics.split(",")

    # Generate checkboxes from topics_list
    checkbox_options = [{"text": {"type": "plain_text", "text": topic}, "value": topic.strip()} for topic in topics_list]

    # Update the modal with the actual content
    await client.views_update(
        view_id=response["view"]["id"],
        view={
            "type": "modal",
            "callback_id": "topics_modal",
            "title": {"type": "plain_text", "text": "Select Topics"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "checkbox_block",
                    "element": {
                        "type": "checkboxes",
                        "options": checkbox_options,
                        "action_id": "selected_topics"
                    },
                    "label": {"type": "plain_text", "text": "We sent you a less technical summary of the message. Are there any topics in particular you'd like to learn more about?"}
                }
            ], 
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            }
        }
    )

    # Open a direct message conversation and post the original and modified messages
    dm_response = await client.conversations_open(users="U07HY9VPHEE")
    channel_id = dm_response["channel"]["id"]

    # Send original message
    await client.chat_postMessage(
        channel=channel_id,
        text=f"_Original message:_ {technical_text} \n \n \n --- \n \n \n"
    )

    # Send message adjusted to business language
    await client.chat_postMessage(
        channel=channel_id,
        text=f"_Summarized message for {user_title}:_ {nontechnical_text} \n \n \n --- \n \n \n",
        parse="full"
    )

# Handle event: user submits topics to learn more
@app.view("topics_modal")
async def handle_view_submission_events(ack, body, logger, client):
    # Acknowledge the submission immediately
    await ack()

    # Show a "Processing..." modal
    processing_view = {
        "type": "modal",
        "callback_id": "processing_modal",
        "title": {"type": "plain_text", "text": "Processing..."},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Please wait while we process your request..."}
            }
        ]
    }

    # Open modal
    response = await client.views_open(
        trigger_id=body["trigger_id"],
        view=processing_view
    )

    # Extract selected topics from the modal submission
    temp_dict = body['view']['state']['values']['checkbox_block']['selected_topics']['selected_options']
    values = [option['value'] for option in temp_dict]
    topics_string = ', '.join(values)

    try:
        # Perform the API call asynchronously
        reading_recs = chat(f"""For each of the topics at the end of this list, provide a brief overview and a reference link where the user can learn more. 
                                When picking a source, remember the technical level associated with the user's role; provide a source with the appropriate level of technical detail. Topics: {topics_string}.
                                If you use markdown, follow these guidelines: single asterisk (*) for bold, single underscore (_) for italics. Do not use double asterisks (**) or titles (#, ##, or ###).""")
        
        # Open a direct message conversation
        dm_response = await client.conversations_open(users="U07HY9VPHEE")
        channel_id = dm_response["channel"]["id"]

        # Send the results back to the user
        await client.chat_postMessage(
            channel=channel_id,
            text=f"Here is some further reading: \n \n \n {reading_recs} \n \n \n --- \n \n \n"
        )

        # Close the "Processing..." modal
        await client.views_update(
            view_id=response["view"]["id"],
            view={
                "type": "modal",
                "callback_id": "completed_modal",
                "title": {"type": "plain_text", "text": "Completed"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "Your request has been processed and the information has been sent to you via direct message."}
                    }
                ]
            }
        )

    # Handle errors in getting submission of topics to learn more
    except Exception as e:
        logger.error(f"Error in handling view submission: {e}")
        await client.views_update(
            view_id=response["view"]["id"],
            view={
                "type": "modal",
                "callback_id": "error_modal",
                "title": {"type": "plain_text", "text": "Error"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "We encountered an error while processing your request. Please try again later."}
                    }
                ]
            }
        )


# Function to start the app with an event loop
async def start_app():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_app())