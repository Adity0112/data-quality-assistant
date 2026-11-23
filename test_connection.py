
from pipeline.ingestion import (
    get_connection,
    get_dataset_version,
    get_table_row_count
)


# ------------------------------------------------
# 1. Test Databricks Connection
# ------------------------------------------------

def test_connection():

    print("\n========== DATABRICKS CONNECTION TEST ==========\n")

    connection = None

    try:

        connection = get_connection()

        print("SUCCESS: Connected to Databricks!")

        # Check configured dataset tables
        versions = get_dataset_version()

        print("\n========== DATASET TABLE CHECK ==========\n")

        for name, table in versions.items():

            print(f"\n{name}: {table}")

            count = get_table_row_count(table)

            print(f"Row count: {count}")

            print("STATUS: SUCCESS")

        print("\n========== CONNECTION TEST COMPLETED ==========\n")

        return True

    except Exception as e:

        print("\nCONNECTION OR TABLE ERROR:")
        print(str(e))

        return False

    finally:

        if connection is not None:
            connection.close()


# ------------------------------------------------
# 2. Application Entry Point
# ------------------------------------------------

if __name__ == "__main__":

    test_connection()
