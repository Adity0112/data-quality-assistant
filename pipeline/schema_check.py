
from pipeline.ingestion import (
    get_full_table_name,
    execute_query
)

from pipeline.snapshot_manager import validate_snapshot_id

from config.settings import snapshot_schema_table


# ------------------------------------------------
# 1. GET SCHEMA FOR A SNAPSHOT
# ------------------------------------------------

def get_snapshot_schema(snapshot_id):

    snapshot_id = validate_snapshot_id(snapshot_id)

    schema_table = get_full_table_name(snapshot_schema_table)

    query = f"""
        SELECT
            column_name,
            data_type
        FROM {schema_table}
        WHERE snapshot_id = '{snapshot_id}'
    """

    rows = execute_query(query)

    schema = {}

    for row in rows:

        column_name = row[0]
        data_type = row[1]

        schema[column_name] = data_type

    if not schema:
        raise ValueError(
            f"No schema found for snapshot: {snapshot_id}"
        )

    return schema


# ------------------------------------------------
# 2. NORMALIZE DATA TYPES
# ------------------------------------------------

def normalize_data_type(data_type):

    data_type = data_type.lower().strip()

    type_aliases = {
        "int": "integer",
        "long": "bigint",
        "varchar": "string",
        "text": "string",
        "bool": "boolean"
    }

    return type_aliases.get(data_type, data_type)


# ------------------------------------------------
# 3. COMPARE TWO SNAPSHOT SCHEMAS
# ------------------------------------------------

def compare_snapshot_schemas(snapshot_id_1, snapshot_id_2):

    snapshot_id_1 = validate_snapshot_id(snapshot_id_1)
    snapshot_id_2 = validate_snapshot_id(snapshot_id_2)

    if snapshot_id_1 == snapshot_id_2:
        raise ValueError(
            "Please provide two different snapshot IDs."
        )

    schema_1 = get_snapshot_schema(snapshot_id_1)
    schema_2 = get_snapshot_schema(snapshot_id_2)

    # Normalize column names for comparison.
    columns_1 = {
        column.lower(): {
            "column_name": column,
            "data_type": data_type
        }
        for column, data_type in schema_1.items()
    }

    columns_2 = {
        column.lower(): {
            "column_name": column,
            "data_type": data_type
        }
        for column, data_type in schema_2.items()
    }

    names_1 = set(columns_1.keys())
    names_2 = set(columns_2.keys())

    added_columns = []
    removed_columns = []
    changed_datatypes = []
    unchanged_columns = []

    # ------------------------------------------------
    # 4. CHECK ADDED AND CHANGED COLUMNS
    # ------------------------------------------------

    for column in names_2:

        if column not in names_1:

            added_columns.append({
                "column_name": columns_2[column]["column_name"],
                "new_type": columns_2[column]["data_type"]
            })

        else:

            old_type = columns_1[column]["data_type"]
            new_type = columns_2[column]["data_type"]

            if normalize_data_type(old_type) != normalize_data_type(new_type):

                changed_datatypes.append({
                    "column_name": columns_2[column]["column_name"],
                    "old_type": old_type,
                    "new_type": new_type
                })

            else:

                unchanged_columns.append(
                    columns_2[column]["column_name"]
                )

    # ------------------------------------------------
    # 5. CHECK REMOVED COLUMNS
    # ------------------------------------------------

    for column in names_1:

        if column not in names_2:

            removed_columns.append({
                "column_name": columns_1[column]["column_name"],
                "old_type": columns_1[column]["data_type"]
            })

    # ------------------------------------------------
    # 6. GENERATE RESULT
    # ------------------------------------------------

    has_changes = bool(
        added_columns
        or removed_columns
        or changed_datatypes
    )

    return {
        "snapshot_1": snapshot_id_1,
        "snapshot_2": snapshot_id_2,

        "added_columns": added_columns,
        "removed_columns": removed_columns,
        "changed_datatypes": changed_datatypes,
        "unchanged_columns": sorted(unchanged_columns),

        "has_changes": has_changes,

        "total_changes": (
            len(added_columns)
            + len(removed_columns)
            + len(changed_datatypes)
        )
    }


# ------------------------------------------------
# 7. RUN SCHEMA CHECK
# ------------------------------------------------

def run_schema_check(snapshot_id_1, snapshot_id_2):

    return compare_snapshot_schemas(
        snapshot_id_1,
        snapshot_id_2
    )
