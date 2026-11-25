
from pipeline.ingestion import (
    get_full_table_name,
    execute_query
)

from pipeline.snapshot_manager import validate_snapshot_id

from config.settings import snapshot_schema_table


# ------------------------------------------------
# 1. GET SCHEMA OF A SNAPSHOT
# ------------------------------------------------

def get_snapshot_schema(snapshot_id):

    snapshot_id = validate_snapshot_id(snapshot_id)

    schema_table = get_full_table_name(snapshot_schema_table)

    query = f"""
        SELECT column_name, data_type
        FROM {schema_table}
        WHERE snapshot_id = '{snapshot_id}'
    """

    rows = execute_query(query)

    if not rows:
        raise ValueError(
            f"No schema found for snapshot: {snapshot_id}"
        )

    schema = {}

    for row in rows:

        column_name = row[0]
        data_type = row[1]

        schema[column_name] = data_type

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

def check_data_types(previous_snapshot_id, current_snapshot_id):

    previous_snapshot_id = validate_snapshot_id(
        previous_snapshot_id
    )

    current_snapshot_id = validate_snapshot_id(
        current_snapshot_id
    )

    if previous_snapshot_id == current_snapshot_id:
        raise ValueError(
            "Previous and current snapshot IDs must be different."
        )

    previous_schema = get_snapshot_schema(
        previous_snapshot_id
    )

    current_schema = get_snapshot_schema(
        current_snapshot_id
    )

    # Normalize column names for comparison
    previous_columns = {
        column.lower(): {
            "column_name": column,
            "data_type": data_type
        }
        for column, data_type in previous_schema.items()
    }

    current_columns = {
        column.lower(): {
            "column_name": column,
            "data_type": data_type
        }
        for column, data_type in current_schema.items()
    }

    previous_names = set(previous_columns.keys())
    current_names = set(current_columns.keys())

    # ------------------------------------------------
    # 4. FIND NEW AND REMOVED COLUMNS
    # ------------------------------------------------

    new_columns = []

    for column in current_names - previous_names:

        details = current_columns[column]

        new_columns.append({
            "column_name": details["column_name"],
            "data_type": details["data_type"]
        })

    removed_columns = []

    for column in previous_names - current_names:

        details = previous_columns[column]

        removed_columns.append({
            "column_name": details["column_name"],
            "data_type": details["data_type"]
        })

    # ------------------------------------------------
    # 5. CHECK DATA TYPE CHANGES
    # ------------------------------------------------

    datatype_changes = []
    valid_columns = []

    common_columns = previous_names.intersection(
        current_names
    )

    for column in common_columns:

        previous_type = previous_columns[column]["data_type"]
        current_type = current_columns[column]["data_type"]

        if normalize_data_type(previous_type) != normalize_data_type(current_type):

            datatype_changes.append({
                "column_name": current_columns[column]["column_name"],
                "previous_type": previous_type,
                "current_type": current_type,
                "issue": "Data type changed"
            })

        else:

            valid_columns.append(
                current_columns[column]["column_name"]
            )

    # ------------------------------------------------
    # 6. RETURN RESULTS
    # ------------------------------------------------

    has_datatype_issues = len(datatype_changes) > 0

    has_schema_changes = (
        bool(new_columns)
        or bool(removed_columns)
        or has_datatype_issues
    )

    return {
        "previous_snapshot_id": previous_snapshot_id,
        "current_snapshot_id": current_snapshot_id,

        "new_columns": new_columns,
        "removed_columns": removed_columns,

        "datatype_changes": datatype_changes,
        "valid_columns": sorted(valid_columns),

        "has_datatype_issues": has_datatype_issues,
        "has_schema_changes": has_schema_changes,

        "total_issues": (
            len(new_columns)
            + len(removed_columns)
            + len(datatype_changes)
        )
    }


# ------------------------------------------------
# 7. MAIN DATATYPE CHECK FUNCTION
# ------------------------------------------------

def run_datatype_check(previous_snapshot_id, current_snapshot_id):

    return check_data_types(
        previous_snapshot_id,
        current_snapshot_id
    )
