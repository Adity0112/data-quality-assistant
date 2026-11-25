
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

from pipeline.null_duplicate_check import (
    check_null_values,
    check_duplicates,
    run_null_duplicate_check
)


snapshot_id = "78485f28-ffe3-4152-9253-617e07ba9d4e"


try:

    print("Testing NULL value check...")

    null_result = check_null_values(snapshot_id)

    print("\nNULL CHECK RESULT:")
    print(null_result)


    print("\nTesting duplicate check...")

    duplicate_result = check_duplicates(snapshot_id)

    print("\nDUPLICATE CHECK RESULT:")
    print(duplicate_result)


    print("\nTesting combined quality check...")

    final_result = run_null_duplicate_check(snapshot_id)

    print("\nFINAL RESULT:")
    print(final_result)

    print("\nQUALITY CHECK TEST PASSED!")

except Exception as error:

    print("\nQUALITY CHECK TEST FAILED!")
    print("Error:", error)

    raise