
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


# questions = [

#     "Tell me about yourself as a data quality assistant.",

#     "Give me information about my dataset.",

#     "How many records have high priority?",

#     "Show me tickets where priority is high.",

#     "Count records grouped by language.",

#     "Show me the record with row ID 99379c32-2a28-49fb-abb9-0abae6e99375."

# ]


# for question in questions:

#     print("\n" + "=" * 60)
#     print("QUESTION:", question)

#     try:

#         response = graph.invoke({
#             "messages": [
#                 HumanMessage(content=question)
#             ]
#         })

#         print("\nAI RESPONSE:")

#         print(
#             response["messages"][-1].content
#         )

#     except Exception as e:

#         print("\nERROR:", str(e))



# from pipeline.ingestion import (
#     get_available_catalogs,
#     get_available_schemas,
#     get_available_tables,
#     get_table_profile
# )


# # ----------------------------------
# # TEST 1: GET AVAILABLE CATALOGS
# # ----------------------------------

# print("\n========== TEST 1: CATALOGS ==========")

# catalogs = get_available_catalogs()

# for catalog in catalogs:
#     print(catalog)


# # ----------------------------------
# # TEST 2: GET AVAILABLE SCHEMAS
# # ----------------------------------

# print("\n========== TEST 2: SCHEMAS ==========")

# schemas = get_available_schemas("workspace")

# for schema in schemas:
#     print(schema)


# # ----------------------------------
# # TEST 3: GET AVAILABLE TABLES
# # ----------------------------------

# print("\n========== TEST 3: TABLES ==========")

# tables = get_available_tables(
#     catalog="workspace",
#     schema="default"
# )

# for table in tables:
#     print(table)


# # ----------------------------------
# # TEST 4: PROFILE A TABLE
# # ----------------------------------
# print("\n========== TEST 4: TABLE PROFILE ==========")

# if tables:

#     selected_table = tables[0]["table_name"]

#     profile = get_table_profile(
#         table_name=selected_table,
#         catalog="workspace",
#         schema="default"
#     )

#     print("\nComplete Profile:")
#     print(profile)

#     print("\nAvailable Keys:")
#     print(profile.keys())

# else:
#     print("No tables found.")



# from pipeline.comparison import (
#     compare_table_metrics,
#     generate_comparison_report
# )


# # Map equivalent business columns

# column_mapping = {

#     "quantity": {
#         "aa_dataset_tickets_multi_lang_5_2_50_version": "subject",
#         "bronze_tickets": "priority"
#     },

#     # "revenue": {
#     #     "table1": "total_amount",
#     #     "table2": "revenue"
#     # }
# }


# # Compare both product tables

# results = compare_table_metrics(

#     aa_dataset_tickets_multi_lang_5_2_50_version="subject",

#     bronze_tickets="priority",

#     column_mapping=column_mapping,

#     catalog="workspace",

#     schema="default"
# )


# # Generate report

# report = generate_comparison_report(results)


# print("\n========== COMPARISON REPORT ==========")

# print(report)


# from pipeline.ingestion import (
#     get_full_table_name,
#     execute_query
# )

# table1 = "aa_dataset_tickets_multi_lang_5_2_50_version"
# table2 = "gold_ticket_summary"

# for table in [table1, table2]:

#     full_table_name = get_full_table_name(
#         table,
#         "workspace",
#         "default"
#     )

#     query = f"""
#         SELECT COUNT(*) AS total_records
#         FROM {full_table_name}
#     """

#     result = execute_query(query)

#     print(table, ":", result[0][0])


# from pipeline.comparison import (
#     compare_record_counts,
#     generate_comparison_report
# )

# count_results = compare_record_counts(

#     table1="aa_dataset_tickets_multi_lang_5_2_50_version",

#     table2="gold_ticket_summary",

#     catalog="workspace",

#     schema="default"
# )

# print("\n========== RECORD COUNT COMPARISON ==========")

# print(count_results)


# from pipeline.ingestion import get_table_schema

# tables = [
#     "aa_dataset_tickets_multi_lang_5_2_50_version",
#     "gold_ticket_summary"
# ]

# for table in tables:

#     print(f"\n========== {table} ==========")

#     schema = get_table_schema(
#         table,
#         catalog="workspace",
#         schema="default"
#     )

#     for column in schema:
#         print(
#             column["column_name"],
#             "->",
#             column["data_type"]
#         )


# from pipeline.comparison import validate_aggregated_table


# result = validate_aggregated_table(

#     source_table="aa_dataset_tickets_multi_lang_5_2_50_version",

#     gold_table="gold_ticket_summary",

#     group_columns=[
#         "queue",
#         "priority",
#         "language",
#         "type"
#     ],

#     gold_count_column="total_tickets",

#     catalog="workspace",

#     schema="default"
# )


# print("\n========== VALIDATION SUMMARY ==========")

# for key, value in result["summary"].items():
#     print(f"{key}: {value}")


# print("\n========== MISMATCH DETAILS ==========")

# for item in result["details"]:

#     if item["validation_status"] != "MATCH":
#         print(item)

# from pipeline.comparison import validate_aggregated_table

# result = validate_aggregated_table(
#     source_table="aa_dataset_tickets_multi_lang_5_2_50_version",
#     gold_table="gold_ticket_summary",
#     group_columns=[
#         "queue",
#         "priority",
#         "language",
#         "type"
#     ],
#     gold_count_column="total_tickets"
# )

# print("SUMMARY:")
# print(result["summary"])

# print("\nDETAILS:")
# for row in result["details"][:10]:
#     print(row)

from pipeline.data_query import get_schema_tables

result = get_schema_tables()

print("Total tables:", result["total_tables"])

for table in result["tables"]:
    print(table)