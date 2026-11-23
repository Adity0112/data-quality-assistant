
from pipeline.ingestion import get_table_schema

from config.settings import (
    old_data_table,
    new_data_table
)


# ------------------------------------------------
# 1. Compare Old and New Table Schemas
# ------------------------------------------------

def compare_schemas(old_table, new_table):

    # Fetch schemas directly from Databricks
    old_schema = get_table_schema(old_table)

    new_schema = get_table_schema(new_table)

    # Convert schema lists into dictionaries
    old_columns = {
        column["column_name"]: column["data_type"]
        for column in old_schema
    }

    new_columns = {
        column["column_name"]: column["data_type"]
        for column in new_schema
    }

    # Find removed columns
    removed_columns = []

    for column, data_type in old_columns.items():

        if column not in new_columns:

            removed_columns.append({

                "column_name": column,

                "data_type": data_type

            })

    # Find added columns
    added_columns = []

    for column, data_type in new_columns.items():

        if column not in old_columns:

            added_columns.append({

                "column_name": column,

                "data_type": data_type

            })

    # Find changed data types
    changed_types = []

    for column in old_columns:

        if column in new_columns:

            old_type = old_columns[column]

            new_type = new_columns[column]

            if old_type.lower() != new_type.lower():

                changed_types.append({

                    "column_name": column,

                    "old_type": old_type,

                    "new_type": new_type

                })

    # Find unchanged columns
    unchanged_columns = []

    for column in old_columns:

        if (
            column in new_columns
            and old_columns[column].lower()
            == new_columns[column].lower()
        ):

            unchanged_columns.append(column)

    # Return comparison result
    return {

        "old_table": old_table,

        "new_table": new_table,

        "added_columns": added_columns,

        "removed_columns": removed_columns,

        "changed_types": changed_types,

        "unchanged_columns": unchanged_columns,

        "has_changes": bool(
            added_columns
            or removed_columns
            or changed_types
        )

    }


# ------------------------------------------------
# 2. Run Schema Validation
# ------------------------------------------------

def run_schema_check():

    result = compare_schemas(
        old_data_table,
        new_data_table
    )

    return result
