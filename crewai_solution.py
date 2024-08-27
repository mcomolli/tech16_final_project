import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Set up llm
llm = OpenAI(temperature=0.1, openai_api_key=os.environ.get('openai_api_key'))

