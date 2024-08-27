from openai import OpenAI
import os
from dotenv import load_dotenv
from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec
from llama_index.core.tools import FunctionTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI

# Get environment variables
load_dotenv()

# Get OpenAI API Key
openai_api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

def chat(message):

    # Code for non-agent model interaction
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "system", "content": """You are a seasoned product manager who is an expert at interacting with both engineers and businesspeople. 
    #                                          Translate whatever technical material is sent to you into language a salesperson can easily digest and find useful. 
    #                                          Be concise, replying with no more than 4 brief bullet points"""},
    #         {"role": "user", "content": f"{message}"}
    #     ]
    # )

    response = agent.chat(message)

    text_only = response.response
    return text_only

# define sample Tool
def multiply(a: int, b: int) -> int:
    """Multiple two integers and returns the result integer"""
    return a * b

def check_stack():
    """Use this tool to answer questions about specific technologies"""
    return "AWS EC2, AWS S3, AWS RDS (PostgreSQL), Docker, Kubernetes (K3s or Amazon EKS), TensorFlow, PyTorch, Scikit-learn, Apache Kafka, Apache Spark, MLflow, TensorFlow Serving, Node.js, Express, React.js, GitHub, GitHub Actions, Terraform, Prometheus, Grafana, ELK Stack (Elasticsearch, Logstash, Kibana), AWS IAM, TLS 1.3, AES-256 encryption, Jupyter Notebooks, Slack, Figma"

multiply_tool = FunctionTool.from_defaults(fn=multiply)

stack_tool = FunctionTool.from_defaults(fn=check_stack)

# initialize llm
llm = OpenAI(model="gpt-4o")

# define DuckDuckGo tool
tool_spec = DuckDuckGoSearchToolSpec()

# initialize ReAct agent
agent = OpenAIAgent.from_tools(tool_spec.to_tool_list() + [stack_tool], llm=llm, verbose=True)