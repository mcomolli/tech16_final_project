from openai import OpenAI
import os
from dotenv import load_dotenv

# Get environment variables
load_dotenv()

# Get OpenAI API Key
openai_api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

def chat(message):

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI that takes instructions from a human and produces an answer. Be concise in your output."},
            {"role": "user", "content": f"{message}"}
        ]
    )

    text_only = response.choices[0].message.content
    return text_only