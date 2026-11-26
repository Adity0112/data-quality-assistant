
# from pipeline.ingestion import (
#     get_connection,
#     get_table_schema,
#     get_table_row_count
# )

# from config.settings import new_data_table


# try:
#     print("Testing Databricks connection...")

#     connection = get_connection()
#     print("SUCCESS: Connected to Databricks!")

#     connection.close()

#     print("\nChecking source table...")

#     schema = get_table_schema(new_data_table)

#     print("SUCCESS: Source table found!")
#     print("\nTable Schema:")

#     for column in schema:
#         print(column)

#     row_count = get_table_row_count(new_data_table)

#     print("\nTotal Rows:", row_count)

# except Exception as error:
#     print("\nTEST FAILED")
#     print("Error:", error)





# from config.settings import new_data_table

# from pipeline.snapshot_manager import (
#     save_bronze_snapshot,
#     get_bronze_history
# )


# print("Testing snapshot creation...")

# try:

#     result = save_bronze_snapshot(new_data_table)

#     print("\nSnapshot created successfully!")

#     print("Snapshot ID:", result["snapshot_id"])

#     print("\nChecking snapshot history...")

#     history = get_bronze_history()

#     for snapshot in history:

#         print(snapshot)

# except Exception as error:

#     print("\nSNAPSHOT TEST FAILED")

#     print("Error:", error)

#     raise



# null_duplicate_check



# print("\n========== TESTING LLM CONNECTION ==========")

# from agent.llm import llm

# print("LLM object created successfully!")

# response = llm.invoke("Hello! Introduce yourself briefly.")

# print("\nLLM RESPONSE:")
# print(response.content)

# print("\n========== TEST COMPLETED ==========")



# from agent.graph import graph

# print("\n========== TEST 1: GENERAL QUESTION ==========")

# response = graph.invoke({
#     "messages": [
#         ("user", "What is data quality?")
#     ]
# })

# print("\nAI RESPONSE:")

# print(response["messages"][-1].content)



# from agent.tools import compare_latest_nulls_tool

# print("\n========== NULL COMPARISON TEST ==========")

# result = compare_latest_nulls_tool.invoke({})

# print("\nPREVIOUS SNAPSHOT:")
# print(result["previous_snapshot_id"])

# print("\nLATEST SNAPSHOT:")
# print(result["latest_snapshot_id"])

# print("\nTOTAL NULL COUNTS:")
# print("Previous:", result["previous_total_nulls"])
# print("Latest:", result["latest_total_nulls"])
# print("Difference:", result["total_null_difference"])

# print("\nCOLUMN-WISE COMPARISON:")

# for item in result["comparison"]:

#     print(
#         item["column_name"],
#         "| Previous:", item["previous_null_count"],
#         "| Latest:", item["latest_null_count"],
#         "| Difference:", item["difference"],
#         "| Status:", item["status"]
#     )

# print("\nHas null changes:", result["has_null_changes"])

# print("\n========== TEST COMPLETED ==========")




# from pipeline.snapshot_manager import save_bronze_snapshot

# result = save_bronze_snapshot(
#     "aa_dataset_tickets_multi_lang_5_2_50_version"
# )

# print(result)

# from pipeline.snapshot_manager import get_snapshot_data

# snapshot_id = result["snapshot_id"]

# records = get_snapshot_data(snapshot_id)

# print("Total records:", len(records))

# print("First record:")
# print(records[0])

# print("Generated row ID:")
# print(records[0]["row_id"])

# row_ids = [record["row_id"] for record in records]

# print("Total IDs:", len(row_ids))
# print("Unique IDs:", len(set(row_ids)))
# print("All IDs are unique:", len(row_ids) == len(set(row_ids)))


# from pipeline.data_query import get_record_by_id

# print("\n========== TEST: GET RECORD BY ROW ID ==========")

# row_id = "fbc40fb3-6a1f-4867-b238-ded4af885b91"

# record = get_record_by_id(row_id)

# print(record)




# from agent.tools import tools

# print("\n========== REGISTERED AGENT TOOLS ==========")

# for index, agent_tool in enumerate(tools, start=1):

#     print(f"{index}. {agent_tool.name}")

# print("\nTotal tools:", len(tools))



from langchain_core.messages import HumanMessage

from agent.graph import graph


questions = [

    "Tell me about yourself as a data quality assistant.",

    "Give me information about my dataset.",

    "How many records have high priority?",

    "Show me tickets where priority is high.",

    "Count records grouped by language.",

    "Show me the record with row ID 99379c32-2a28-49fb-abb9-0abae6e99375."

]


for question in questions:

    print("\n" + "=" * 60)
    print("QUESTION:", question)

    try:

        response = graph.invoke({
            "messages": [
                HumanMessage(content=question)
            ]
        })

        print("\nAI RESPONSE:")

        print(
            response["messages"][-1].content
        )

    except Exception as e:

        print("\nERROR:", str(e))
