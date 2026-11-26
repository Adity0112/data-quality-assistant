
from databricks_langchain import ChatDatabricks
from databricks.sdk import WorkspaceClient

from config.settings import (
    databricks_host,
    databricks_tokken
)


# ----------------------------------
# 1. CONNECT TO DATABRICKS
# ----------------------------------

workspace_client = WorkspaceClient(
    host=databricks_host,
    token=databricks_tokken
)


# ----------------------------------
# 2. INITIALIZE LLM
# ----------------------------------

llm = ChatDatabricks(
    endpoint="databricks-meta-llama-3-1-8b-instruct",
    workspace_client=workspace_client,
    temperature=0.1,
    max_tokens=1000
)
