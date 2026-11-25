
from pipeline.ingestion import (
    get_full_table_name,
    execute_query
)

from pipeline.snapshot_manager import validate_snapshot_id

from config.settings import (
    bronze_history_table,
    snapshot_schema_table
)


# ------------------------------------------------
# 1. GET SNAPSHOT TABLE
# ------------------------------------------------

def get_snapshot_table():

    return get_full_table_name(bronze_history_table)


# ------------------------------------------------
# 2. GET COLUMNS FOR A PARTICULAR SNAPSHOT
# ------------------------------------------------

def get_snapshot_columns(snapshot_id):

    snapshot_id = validate_snapshot_id(snapshot_id)

    schema_table = get_full_table_name(snapshot_schema_table)

    query = f"""
        SELECT column_name

        FROM {schema_table}

        WHERE snapshot_id = '{snapshot_id}'

        ORDER BY column_name
    """

    rows = execute_query(query)

    columns = [row[0] for row in rows]

    if not columns:
        raise ValueError(
            "No schema information found for this snapshot."
        )

    return columns


# ------------------------------------------------
# 3. CHECK NULL VALUES
# ------------------------------------------------

def check_null_values(snapshot_id):

    snapshot_id = validate_snapshot_id(snapshot_id)

    history_table = get_snapshot_table()

    columns = get_snapshot_columns(snapshot_id)

    null_expressions = []

    for column in columns:

        safe_column = f"`{column.replace('`', '``')}`"

        null_expressions.append(
            f"SUM(CASE WHEN {safe_column} IS NULL "
            f"THEN 1 ELSE 0 END) AS `{column}`"
        )

    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            {", ".join(null_expressions)}

        FROM {history_table}

        WHERE snapshot_id = '{snapshot_id}'
    """

    rows = execute_query(query)

    if not rows or rows[0][0] == 0:
        raise ValueError("Snapshot contains no records.")

    total_rows = rows[0][0]

    null_results = []

    for index, column in enumerate(columns, start=1):

        null_count = rows[0][index]

        null_percentage = (
            null_count / total_rows
        ) * 100

        null_results.append({
            "column_name": column,
            "null_count": null_count,
            "null_percentage": round(null_percentage, 2)
        })

    return {
        "snapshot_id": snapshot_id,
        "total_rows": total_rows,
        "null_results": null_results,
        "has_null_values": any(
            item["null_count"] > 0
            for item in null_results
        )
    }


# ------------------------------------------------
# 4. CHECK DUPLICATE ROWS
# ------------------------------------------------

def check_duplicates(snapshot_id):

    snapshot_id = validate_snapshot_id(snapshot_id)

    history_table = get_snapshot_table()

    columns = get_snapshot_columns(snapshot_id)

    column_list = ", ".join(
        f"`{column.replace('`', '``')}`"
        for column in columns
    )

    query = f"""
        SELECT
            (
                SELECT COUNT(*)
                FROM {history_table}
                WHERE snapshot_id = '{snapshot_id}'
            ) AS total_rows,

            COALESCE(SUM(row_count - 1), 0) AS duplicate_count

        FROM (
            SELECT COUNT(*) AS row_count

            FROM {history_table}

            WHERE snapshot_id = '{snapshot_id}'

            GROUP BY {column_list}

            HAVING COUNT(*) > 1
        ) duplicate_groups
    """

    rows = execute_query(query)

    total_rows = rows[0][0]
    duplicate_count = rows[0][1]

    return {
        "snapshot_id": snapshot_id,
        "total_rows": total_rows,
        "duplicate_count": duplicate_count,
        "has_duplicates": duplicate_count > 0
    }


# ------------------------------------------------
# 5. RUN BOTH CHECKS
# ------------------------------------------------

def run_null_duplicate_check(snapshot_id):

    null_result = check_null_values(snapshot_id)

    duplicate_result = check_duplicates(snapshot_id)

    return {
        "snapshot_id": snapshot_id,

        "null_check": null_result,

        "duplicate_check": duplicate_result,

        "has_quality_issues": (
            null_result["has_null_values"]
            or duplicate_result["has_duplicates"]
        )
    }
