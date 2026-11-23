
from pipeline.ingestion import get_table_schema

from config.settings import new_data_table


# ------------------------------------------------
# 1. Check Data Types
# ------------------------------------------------

def check_data_types(table_name, expected_schema):

    # Fetch actual schema from Databricks
    actual_schema = get_table_schema(table_name)

    actual_columns = {
        column["column_name"]: column["data_type"]
        for column in actual_schema
    }

    datatype_issues = []
    valid_columns = []

    # Compare expected and actual data types
    for column, expected_type in expected_schema.items():

        # Check whether column exists
        if column not in actual_columns:

            datatype_issues.append({

                "column_name": column,

                "expected_type": expected_type,

                "actual_type": None,

                "issue": "Column missing"

            })

            continue

        actual_type = actual_columns[column]

        # Compare data types
        if actual_type.lower() != expected_type.lower():

            datatype_issues.append({

                "column_name": column,

                "expected_type": expected_type,

                "actual_type": actual_type,

                "issue": "Data type mismatch"

            })

        else:

            valid_columns.append(column)

    return {

        "datatype_issues": datatype_issues,

        "valid_columns": valid_columns,

        "has_datatype_issues": bool(datatype_issues),

        "total_issues": len(datatype_issues)

    }


# ------------------------------------------------
# 2. Run Datatype Validation
# ------------------------------------------------

def run_datatype_check(table_name, expected_schema):

    result = check_data_types(
        table_name,
        expected_schema
    )

    return result
