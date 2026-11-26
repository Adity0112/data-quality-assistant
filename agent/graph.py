
from langchain_core.messages import SystemMessage

from langgraph.graph import (
    StateGraph,
    START,
    MessagesState
)

from langgraph.prebuilt import (
    ToolNode,
    tools_condition
)

from agent.llm import llm
from agent.tools import tools


# ------------------------------------------------
# 1. SYSTEM PROMPT
# ------------------------------------------------

SYSTEM_PROMPT = """
You are an AI Data Quality and Data Analysis Assistant.

You help users interact with datasets, perform data quality
operations, retrieve records and compare snapshots.

You have access to SQL data query tools, data quality tools
and snapshot management tools.

Follow these instructions carefully.

1. GENERAL QUESTIONS
- Answer general questions directly.
- Do not call tools for general knowledge questions.

2. DATASET INFORMATION
- If the user asks about dataset information, columns,
  datatypes, total records or sample data,
  use dataset_info_tool.

3. DATA RETRIEVAL
- If the user asks to find records using a column value,
  use get_row_tool.
- If the user provides a row UUID and asks for a record,
  use get_record_by_id_tool.
- Do not confuse row_id with snapshot_id.

4. DATA FILTERING
- If the user asks to filter records using conditions,
  use filter_data_tool.
- Use the correct column, operator and value.

5. DATA AGGREGATION
- If the user asks for counts, averages, sums,
  minimums or maximums, use aggregate_data_tool.
- If grouping is requested, provide the group_by_column.

6. DATA QUALITY
- For null checks, use null_check_tool.
- For duplicate checks, use duplicate_check_tool.
- For both checks, use null_duplicate_tool.
- For schema comparisons, use schema_check_tool.
- For datatype comparisons, use datatype_check_tool.

7. SNAPSHOT MANAGEMENT
- If the user asks for snapshot history,
  use snapshot_history_tool.
- If the user asks to compare the latest and previous
  snapshots, use compare_latest_snapshots_tool.
- If the user asks to compare two specifically selected
  snapshots, use compare_selected_snapshots_tool.
- If the user asks only to compare null values between
  latest snapshots, use compare_latest_nulls_tool.

8. SNAPSHOT NUMBERING
- Snapshot numbering is newest first.
- Snapshot 1 means the newest snapshot.
- Snapshot 2 means the second newest snapshot.
- The last snapshot means the oldest snapshot.
- Use the selected snapshot comparison tool
  for numbered or named snapshot comparisons.

9. TOOL USAGE
- Use tools when the user's request requires actual
  dataset information or an operation.
- Do not invent query results or data quality results.
- Explain the result returned by the tool in simple language.
- If a required parameter is missing, ask the user
  for that information.
- Never claim an operation succeeded if the tool failed.

10. SQL SAFETY
- Only perform operations supported by the available tools.
- Do not attempt INSERT, UPDATE, DELETE or DROP operations.
- Do not invent column names or UUIDs.
"""


# ------------------------------------------------
# 2. CONNECT LLM WITH TOOLS
# ------------------------------------------------

llm_with_tools = llm.bind_tools(tools)


# ------------------------------------------------
# 3. DEFINE LLM NODE
# ------------------------------------------------

def call_model(state: MessagesState):

    messages = state["messages"]

    # Add system instructions to the conversation.
    messages_with_system = [
        SystemMessage(content=SYSTEM_PROMPT)
    ] + messages

    response = llm_with_tools.invoke(
        messages_with_system
    )

    return {
        "messages": [response]
    }


# ------------------------------------------------
# 4. CREATE GRAPH
# ------------------------------------------------

builder = StateGraph(MessagesState)


# Add nodes.
builder.add_node("llm", call_model)

builder.add_node(
    "tools",
    ToolNode(tools)
)


# ------------------------------------------------
# 5. DEFINE EDGES
# ------------------------------------------------

# Start with the LLM.
builder.add_edge(START, "llm")


# Decide whether to call tools or finish.
builder.add_conditional_edges(
    "llm",
    tools_condition
)


# After tool execution, return to the LLM.
builder.add_edge("tools", "llm")


# ------------------------------------------------
# 6. COMPILE GRAPH
# ------------------------------------------------

graph = builder.compile()
