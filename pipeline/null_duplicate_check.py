
from pipeline.ingestion import (
    get_full_table_name,
    execute_query
)

from pipeline.snapshot_manager import (
    validate_snapshot_id,
    get_latest_snapshots
)

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


# ------------------------------------------------
# 6. COMPARE NULL VALUES BETWEEN LATEST SNAPSHOTS
# ------------------------------------------------

def compare_latest_snapshot_nulls():

    # Get latest and previous snapshots
    snapshots = get_latest_snapshots()

    if "message" in snapshots:
        return snapshots

    latest_snapshot = snapshots["latest_snapshot"]
    previous_snapshot = snapshots["previous_snapshot"]

    latest_id = latest_snapshot["snapshot_id"]
    previous_id = previous_snapshot["snapshot_id"]

    # Run null checks on both snapshots
    latest_result = check_null_values(latest_id)
    previous_result = check_null_values(previous_id)

    # Convert results into dictionaries
    latest_nulls = {
        item["column_name"]: item["null_count"]
        for item in latest_result["null_results"]
    }

    previous_nulls = {
        item["column_name"]: item["null_count"]
        for item in previous_result["null_results"]
    }

    # Get all columns from both snapshots
    all_columns = sorted(
        set(latest_nulls) | set(previous_nulls)
    )

    comparison = []

    # Compare null counts column by column
    for column in all_columns:

        previous_count = previous_nulls.get(column)
        latest_count = latest_nulls.get(column)

        if previous_count is not None and latest_count is not None:

            difference = latest_count - previous_count

            if difference > 0:
                status = "NULLS_INCREASED"

            elif difference < 0:
                status = "NULLS_DECREASED"

            else:
                status = "NO_CHANGE"

        elif column in latest_nulls:

            difference = None
            status = "NEW_COLUMN"

        else:

            difference = None
            status = "REMOVED_COLUMN"

        comparison.append({
            "column_name": column,
            "previous_null_count": previous_count,
            "latest_null_count": latest_count,
            "difference": difference,
            "status": status
        })

    # Calculate total null cells across all columns
    previous_total = sum(previous_nulls.values())
    latest_total = sum(latest_nulls.values())

    total_difference = latest_total - previous_total

    # Return comparison report
    return {
        "previous_snapshot_id": previous_id,
        "latest_snapshot_id": latest_id,

        "previous_total_rows": previous_result["total_rows"],
        "latest_total_rows": latest_result["total_rows"],

        "previous_total_nulls": previous_total,
        "latest_total_nulls": latest_total,

        "total_null_difference": total_difference,

        "comparison": comparison,

        "has_null_changes": any(
            item["status"] != "NO_CHANGE"
            for item in comparison
        )
    }
