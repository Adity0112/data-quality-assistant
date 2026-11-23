
from pipeline.ingestion import (
    get_full_table_name,
    execute_query
)


# ------------------------------------------------
# 1. Check Null Values
# ------------------------------------------------

def check_null_values(table_name):

    full_table_name = get_full_table_name(table_name)

    # Get column names from Databricks
    from pipeline.ingestion import get_table_schema

    schema = get_table_schema(table_name)

    if not schema:
        raise ValueError("Table contains no columns.")

    # Build SQL expressions for each column
    null_expressions = []

    for column in schema:

        column_name = column["column_name"]

        # Safely quote column identifier
        safe_column = (
            "`" + column_name.replace("`", "``") + "`"
        )

        null_expressions.append(
            f"SUM(CASE WHEN {safe_column} IS NULL "
            f"THEN 1 ELSE 0 END) AS {safe_column}"
        )

    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            {", ".join(null_expressions)}
        FROM {full_table_name}
    """

    result = execute_query(query)

    total_rows = result[0][0]

    null_report = []

    total_null_values = 0

    for index, column in enumerate(schema):

        null_count = result[0][index + 1] or 0

        null_percentage = (
            (null_count / total_rows) * 100
            if total_rows > 0 else 0
        )

        total_null_values += null_count

        null_report.append({

            "column_name": column["column_name"],

            "null_count": int(null_count),

            "null_percentage": round(
                null_percentage, 2
            ),

            "has_nulls": bool(null_count > 0)

        })

    return {

        "total_rows": total_rows,

        "null_report": null_report,

        "total_null_values": total_null_values,

        "has_nulls": bool(total_null_values > 0)

    }


# ------------------------------------------------
# 2. Check Duplicate Records
# ------------------------------------------------

def check_duplicates(table_name):

    full_table_name = get_full_table_name(table_name)

    query = f"""
        SELECT
            COUNT(*) AS total_rows,

            COUNT(*) - COUNT(DISTINCT *) AS duplicate_count

        FROM {full_table_name}
    """

    result = execute_query(query)

    total_rows = result[0][0]
    duplicate_count = result[0][1]

    duplicate_percentage = (

        (duplicate_count / total_rows) * 100

        if total_rows > 0 else 0

    )

    return {

        "total_rows": total_rows,

        "duplicate_count": duplicate_count,

        "duplicate_percentage": round(
            duplicate_percentage, 2
        ),

        "has_duplicates": bool(duplicate_count > 0)

    }


# ------------------------------------------------
# 3. Run Null and Duplicate Validation
# ------------------------------------------------

def run_null_duplicate_check(table_name):

    null_result = check_null_values(table_name)

    duplicate_result = check_duplicates(table_name)

    return {

        "null_check": null_result,

        "duplicate_check": duplicate_result,

        "has_quality_issues": (

            null_result["has_nulls"]

            or duplicate_result["has_duplicates"]

        )

    }
