from openai import OpenAI
import os
from dotenv import load_dotenv
from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI
from llama_index.readers.web import SpiderWebReader
from llama_index.core import VectorStoreIndex

# Get environment variables
load_dotenv()

# Get OpenAI API Key
openai_api_key = os.environ.get("OPENAI_API_KEY")

# create a function to chat to the OpenAI Agent
def chat(message):

    response = agent.chat(message)

    text_only = response.response
    return text_only

# Tool used to see details of tech stack
def check_stack():
    """Use this tool to answer questions about specific technologies"""
    tech_stack = """
    Frontend:
        - React.js: https://reactjs.org/docs/
        - TypeScript: https://www.typescriptlang.org/docs/
        - Webpack: https://webpack.js.org/concepts/

    Backend:
        - Node.js: https://nodejs.org/en/docs/
        - Express.js: https://expressjs.com/en/starter/basic-routing.html
        - GraphQL: https://graphql.org/learn/

    Database:
        - PostgreSQL: https://www.postgresql.org/docs/
        - Redis: https://redis.io/documentation
        - Prisma ORM: https://www.prisma.io/docs/getting-started

    DevOps/Infrastructure:
        - Docker: https://docs.docker.com/
        - Kubernetes: https://kubernetes.io/docs/
        - Terraform: https://www.terraform.io/docs

    CI/CD:
        - GitHub Actions: https://docs.github.com/en/actions
        - Jenkins: https://www.jenkins.io/doc/
        - CircleCI: https://circleci.com/docs/

    Monitoring & Logging:
        - Prometheus: https://prometheus.io/docs/introduction/overview/
        - Grafana: https://grafana.com/docs/grafana/latest/
        - ELK Stack (Elasticsearch, Logstash, Kibana): https://www.elastic.co/guide/index.html

    Security:
        - OWASP: https://owasp.org/www-project-top-ten/
        - Vault: https://www.vaultproject.io/docs
        - Snyk: https://docs.snyk.io/
    """
    return tech_stack

# operationalize stack_tool
stack_tool = FunctionTool.from_defaults(fn=check_stack)

# initialize llm
llm = OpenAI(model="gpt-4o", 
            logprobs=None,
            default_headers={})

# define DuckDuckGo tool
tool_spec = DuckDuckGoSearchToolSpec()

# Get product documentation via Spider web crawler
spider_reader = SpiderWebReader(
    api_key=os.environ.get("SPIDER_API_KEY"),
    mode="scrape",
    # params={} # Optional parameters see more on https://spider.cloud/docs/api
)

urls = ["https://owasp.org/www-project-top-ten/", "https://www.vaultproject.io/docs", "https://docs.snyk.io/"]
all_documents = []
for url in urls:
        documents = spider_reader.load_data(url=url)
        all_documents.extend(documents)

# Create an index from the documents
index = VectorStoreIndex.from_documents(all_documents)

# Create a query engine from the index
query_engine = index.as_query_engine()

# turn the query engine into a RAG tool
documentation_rag_tool = QueryEngineTool.from_defaults(
    query_engine, name="documentation_rag_tool", description="Useful for answering questions about OWASP, Vaultproject, and Snyk"
)

# initialize ReAct agent
agent = OpenAIAgent.from_tools(tool_spec.to_tool_list() + [stack_tool] + [documentation_rag_tool], llm=llm, verbose=True)