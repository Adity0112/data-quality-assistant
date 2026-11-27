
import re

from pipeline.ingestion import (
    get_full_table_name,
    execute_query,
    get_table_schema
)


# ============================================================
# 1. HELPER FUNCTIONS
# ============================================================

def validate_column_name(column_name):
    """
    Validate a column name before using it in SQL.
    """

    if not isinstance(column_name, str):
        raise ValueError("Column name must be a string.")

    if not re.fullmatch(r"[A-Za-z0-9_]+", column_name):
        raise ValueError(f"Invalid column name: {column_name}")

    return column_name


def _get_schema_columns(table_name, catalog=None, schema=None):
    """
    Return table schema as:
    {
        "column_name": "data_type"
    }
    """

    result = get_table_schema(
        table_name,
        catalog=catalog,
        schema=schema
    )

    columns = {}

    for column in result:
        column_name = column.get("column_name")
        data_type = column.get("data_type", "")

        columns[column_name.lower()] = {
            "column_name": column_name,
            "data_type": str(data_type).lower()
        }

    return columns


def _get_rows(result):
    """
    Convert query results into a list of dictionaries.

    Supports common result formats returned by database helpers.
    """

    if result is None:
        return []

    if isinstance(result, list):
        if not result:
            return []

        if isinstance(result[0], dict):
            return result

        if hasattr(result[0], "asDict"):
            return [row.asDict() for row in result]

        return result

    if hasattr(result, "to_dict"):
        return result.to_dict(orient="records")

    if hasattr(result, "fetchall"):
        rows = result.fetchall()

        if hasattr(result, "description") and result.description:
            columns = [col[0] for col in result.description]
            return [
                dict(zip(columns, row))
                for row in rows
            ]

        return rows

    return result


def _is_string_type(data_type):
    """
    Check whether a Databricks data type is a string type.
    """

    return any(
        data_type.startswith(value)
        for value in ["string", "varchar", "char"]
    )


def _get_column_expression(column_name, data_type):
    """
    Normalize string columns for comparison.
    Other data types remain unchanged.
    """

    if _is_string_type(data_type):
        return f"LOWER(TRIM(CAST(`{column_name}` AS STRING)))"

    return f"`{column_name}`"


# ============================================================
# 2. GET COMPARABLE SCHEMA
# ============================================================

def get_comparable_schema(
    table1,
    table2,
    catalog=None,
    schema=None
):
    """
    Find common columns between two tables.
    """

    schema1 = _get_schema_columns(table1, catalog, schema)
    schema2 = _get_schema_columns(table2, catalog, schema)

    common_columns = []

    for column in schema1:

        if column in schema2:

            common_columns.append({
                "table1_column": schema1[column]["column_name"],
                "table2_column": schema2[column]["column_name"],
                "table1_type": schema1[column]["data_type"],
                "table2_type": schema2[column]["data_type"]
            })

    return {
        "table1": table1,
        "table2": table2,
        "table1_columns": list(schema1.values()),
        "table2_columns": list(schema2.values()),
        "common_columns": common_columns
    }


# ============================================================
# 3. VALIDATE COLUMN MAPPING
# ============================================================

def validate_column_mapping(
    schemas,
    table1,
    table2,
    column_mapping,
    numeric=False
):
    """
    Validate the column mapping between two tables.

    Example:
    {
        "queue": "queue",
        "priority": "priority"
    }
    """

    if not isinstance(column_mapping, dict):
        raise ValueError("column_mapping must be a dictionary.")

    schema1 = _get_schema_columns(table1)
    schema2 = _get_schema_columns(table2)

    validated_mapping = {}

    for source_column, target_column in column_mapping.items():

        validate_column_name(source_column)
        validate_column_name(target_column)

        source_key = source_column.lower()
        target_key = target_column.lower()

        if source_key not in schema1:
            raise ValueError(
                f"Column '{source_column}' not found in {table1}."
            )

        if target_key not in schema2:
            raise ValueError(
                f"Column '{target_column}' not found in {table2}."
            )

        if numeric:

            source_type = schema1[source_key]["data_type"]
            target_type = schema2[target_key]["data_type"]

            numeric_types = (
                "int",
                "bigint",
                "smallint",
                "tinyint",
                "float",
                "double",
                "decimal",
                "long",
                "short"
            )

            if not any(source_type.startswith(t) for t in numeric_types):
                raise ValueError(
                    f"Column '{source_column}' in {table1} "
                    f"is not numeric."
                )

            if not any(target_type.startswith(t) for t in numeric_types):
                raise ValueError(
                    f"Column '{target_column}' in {table2} "
                    f"is not numeric."
                )

        validated_mapping[source_column] = target_column

    return validated_mapping


# ============================================================
# 4. COMPARE RECORD COUNTS
# ============================================================

def compare_record_counts(
    table1,
    table2,
    catalog=None,
    schema=None
):
    """
    Compare total record counts of two tables.
    """

    full_table1 = get_full_table_name(
        table1,
        catalog=catalog,
        schema=schema
    )

    full_table2 = get_full_table_name(
        table2,
        catalog=catalog,
        schema=schema
    )

    query = f"""
        SELECT
            (SELECT COUNT(*) FROM {full_table1}) AS table1_count,
            (SELECT COUNT(*) FROM {full_table2}) AS table2_count
    """

    rows = _get_rows(execute_query(query))

    if not rows:
        raise RuntimeError("Could not retrieve record counts.")

    result = rows[0]

    count1 = int(result["table1_count"])
    count2 = int(result["table2_count"])

    return {
        "table1": table1,
        "table2": table2,
        "table1_count": count1,
        "table2_count": count2,
        "difference": count1 - count2,
        "match": count1 == count2
    }


# ============================================================
# 5. BUILD AGGREGATION QUERY
# ============================================================

def build_aggregation_query(
    table_name,
    column_mapping,
    table_key,
    metric_functions,
    catalog=None,
    schema=None
):
    """
    Build an aggregation SQL query.

    column_mapping:
        Source column -> target column

    metric_functions:
        Example:
        {
            "total_amount": "SUM"
        }
    """

    full_table = get_full_table_name(
        table_name,
        catalog=catalog,
        schema=schema
    )

    group_columns = []

    for column in column_mapping:

        validate_column_name(column)

        group_columns.append(f"`{column}`")

    metrics = []

    for column, function in metric_functions.items():

        validate_column_name(column)

        allowed_functions = {
            "SUM",
            "AVG",
            "MIN",
            "MAX",
            "COUNT"
        }

        function = function.upper()

        if function not in allowed_functions:
            raise ValueError(
                f"Unsupported aggregation function: {function}"
            )

        metrics.append(
            f"{function}(`{column}`) AS `{column}_{function.lower()}`"
        )

    select_columns = group_columns + metrics

    query = f"""
        SELECT
            {", ".join(select_columns)}
        FROM {full_table}
        GROUP BY {", ".join(group_columns)}
    """

    return query


# ============================================================
# 6. COMPARE NUMERIC METRICS
# ============================================================

def compare_numeric_metrics(
    table1,
    table2,
    column_mapping,
    metric_functions=None,
    catalog=None,
    schema=None
):
    """
    Compare numeric aggregate metrics between two tables.
    """

    if metric_functions is None:
        metric_functions = ["SUM", "AVG", "MIN", "MAX"]

    full_table1 = get_full_table_name(
        table1,
        catalog=catalog,
        schema=schema
    )

    full_table2 = get_full_table_name(
        table2,
        catalog=catalog,
        schema=schema
    )

    schema1 = _get_schema_columns(table1, catalog, schema)
    schema2 = _get_schema_columns(table2, catalog, schema)

    results = []

    for source_column, target_column in column_mapping.items():

        validate_column_name(source_column)
        validate_column_name(target_column)

        if source_column.lower() not in schema1:
            raise ValueError(
                f"Column '{source_column}' not found in {table1}."
            )

        if target_column.lower() not in schema2:
            raise ValueError(
                f"Column '{target_column}' not found in {table2}."
            )

        for function in metric_functions:

            function = function.upper()

            if function not in {"SUM", "AVG", "MIN", "MAX", "COUNT"}:
                raise ValueError(
                    f"Unsupported metric function: {function}"
                )

            query = f"""
                SELECT
                    (SELECT {function}(`{source_column}`)
                     FROM {full_table1}) AS value1,

                    (SELECT {function}(`{target_column}`)
                     FROM {full_table2}) AS value2
            """

            rows = _get_rows(execute_query(query))

            if not rows:
                continue

            value1 = rows[0]["value1"]
            value2 = rows[0]["value2"]

            results.append({
                "table1_column": source_column,
                "table2_column": target_column,
                "metric": function,
                "table1_value": value1,
                "table2_value": value2,
                "match": value1 == value2
            })

    return results


# ============================================================
# 7. COMPARE CATEGORY DISTRIBUTIONS
# ============================================================

def compare_category_distributions(
    table1,
    table2,
    column_mapping,
    catalog=None,
    schema=None,
    limit=20
):
    """
    Compare category distributions between two tables.
    """

    full_table1 = get_full_table_name(
        table1,
        catalog=catalog,
        schema=schema
    )

    full_table2 = get_full_table_name(
        table2,
        catalog=catalog,
        schema=schema
    )

    results = []

    for source_column, target_column in column_mapping.items():

        validate_column_name(source_column)
        validate_column_name(target_column)

        query = f"""
            WITH source_counts AS (
                SELECT
                    LOWER(TRIM(CAST(`{source_column}` AS STRING))) AS category,
                    COUNT(*) AS source_count
                FROM {full_table1}
                GROUP BY
                    LOWER(TRIM(CAST(`{source_column}` AS STRING)))
            ),

            target_counts AS (
                SELECT
                    LOWER(TRIM(CAST(`{target_column}` AS STRING))) AS category,
                    COUNT(*) AS target_count
                FROM {full_table2}
                GROUP BY
                    LOWER(TRIM(CAST(`{target_column}` AS STRING)))
            )

            SELECT
                COALESCE(s.category, t.category) AS category,
                COALESCE(s.source_count, 0) AS source_count,
                COALESCE(t.target_count, 0) AS target_count
            FROM source_counts s
            FULL OUTER JOIN target_counts t
                ON s.category <=> t.category
            ORDER BY category
            LIMIT {int(limit)}
        """

        rows = _get_rows(execute_query(query))

        results.append({
            "table1_column": source_column,
            "table2_column": target_column,
            "categories": rows
        })

    return results


# ============================================================
# 8. GENERATE COMPARISON REPORT
# ============================================================

def generate_comparison_report(
    count_results=None,
    numeric_results=None,
    category_results=None
):
    """
    Generate a combined comparison report.
    """

    count_results = count_results or {}
    numeric_results = numeric_results or []
    category_results = category_results or []

    numeric_matches = sum(
        1 for item in numeric_results
        if item.get("match")
    )

    category_matches = 0
    category_mismatches = 0

    for result in category_results:

        for category in result.get("categories", []):

            if category.get("source_count") == category.get("target_count"):
                category_matches += 1
            else:
                category_mismatches += 1

    return {
        "record_count_comparison": count_results,
        "numeric_comparison": numeric_results,
        "category_comparison": category_results,
        "summary": {
            "record_counts_match": count_results.get("match"),
            "numeric_metrics_total": len(numeric_results),
            "numeric_metrics_matched": numeric_matches,
            "numeric_metrics_mismatched": (
                len(numeric_results) - numeric_matches
            ),
            "category_matches": category_matches,
            "category_mismatches": category_mismatches
        }
    }


# ============================================================
# 9. VALIDATE AGGREGATED TABLE
# ============================================================

def validate_aggregated_table(
    source_table,
    gold_table,
    group_columns,
    gold_count_column="total_tickets",
    catalog=None,
    schema=None
):
    """
    Validate an aggregated Gold table against its source table.

    Example:

    Source:
        aa_dataset_tickets_multi_lang_5_2_50_version

    Gold:
        gold_ticket_summary

    Group columns:
        queue, priority, language, type

    Gold count column:
        total_tickets

    String group columns are normalized using:
        LOWER(TRIM(CAST(column AS STRING)))

    This handles differences such as:
        Technical Support
        technical support
    """

    if not group_columns:
        raise ValueError("group_columns cannot be empty.")

    for column in group_columns:
        validate_column_name(column)

    validate_column_name(gold_count_column)

    full_source = get_full_table_name(
        source_table,
        catalog=catalog,
        schema=schema
    )

    full_gold = get_full_table_name(
        gold_table,
        catalog=catalog,
        schema=schema
    )

    source_schema = _get_schema_columns(
        source_table,
        catalog,
        schema
    )

    gold_schema = _get_schema_columns(
        gold_table,
        catalog,
        schema
    )

    # --------------------------------------------------------
    # Validate columns
    # --------------------------------------------------------

    for column in group_columns:

        if column.lower() not in source_schema:
            raise ValueError(
                f"Grouping column '{column}' not found in source table."
            )

        if column.lower() not in gold_schema:
            raise ValueError(
                f"Grouping column '{column}' not found in Gold table."
            )

    if gold_count_column.lower() not in gold_schema:
        raise ValueError(
            f"Count column '{gold_count_column}' not found in Gold table."
        )

    # --------------------------------------------------------
    # Build normalized expressions
    # --------------------------------------------------------

    source_expressions = []
    gold_expressions = []

    source_group_by = []
    gold_group_by = []

    for column in group_columns:

        source_type = source_schema[column.lower()]["data_type"]
        gold_type = gold_schema[column.lower()]["data_type"]

        source_expression = _get_column_expression(
            column,
            source_type
        )

        gold_expression = _get_column_expression(
            column,
            gold_type
        )

        source_expressions.append(
            f"{source_expression} AS `{column}`"
        )

        gold_expressions.append(
            f"{gold_expression} AS `{column}`"
        )

        # IMPORTANT:
        # Use the same normalized expression in GROUP BY.
        source_group_by.append(source_expression)
        gold_group_by.append(gold_expression)

    # --------------------------------------------------------
    # Build join conditions
    # --------------------------------------------------------

    join_conditions = []

    for column in group_columns:

        join_conditions.append(
            f"s.`{column}` <=> g.`{column}`"
        )

    join_condition = " AND ".join(join_conditions)

    # --------------------------------------------------------
    # Build output columns
    # --------------------------------------------------------

    output_columns = []

    for column in group_columns:

        output_columns.append(
            f"COALESCE(s.`{column}`, g.`{column}`) AS `{column}`"
        )

    output_columns.extend([
        "COALESCE(s.source_count, 0) AS source_count",
        "COALESCE(g.gold_count, 0) AS gold_count",
        "COALESCE(g.gold_row_count, 0) AS gold_row_count"
    ])

    # --------------------------------------------------------
    # Final SQL query
    # --------------------------------------------------------

    query = f"""
        WITH source_summary AS (

            SELECT
                {", ".join(source_expressions)},
                COUNT(*) AS source_count

            FROM {full_source}

            GROUP BY
                {", ".join(source_group_by)}
        ),

        gold_summary AS (

            SELECT
                {", ".join(gold_expressions)},
                SUM(COALESCE(`{gold_count_column}`, 0)) AS gold_count,
                COUNT(*) AS gold_row_count

            FROM {full_gold}

            GROUP BY
                {", ".join(gold_group_by)}
        ),

        comparison AS (

            SELECT
                {", ".join(output_columns)}

            FROM source_summary s

            FULL OUTER JOIN gold_summary g

                ON {join_condition}
        )

        SELECT
            *,

            CASE

                WHEN source_count = 0
                    THEN 'EXTRA_IN_GOLD'

                WHEN gold_count = 0
                    THEN 'MISSING_IN_GOLD'

                WHEN source_count <> gold_count
                    THEN 'COUNT_MISMATCH'

                ELSE 'MATCH'

            END AS status

        FROM comparison

        ORDER BY status
    """

    details = _get_rows(execute_query(query))

    # --------------------------------------------------------
    # Calculate summary
    # --------------------------------------------------------

    total_categories = len(details)

    matched = 0
    count_mismatches = 0
    missing_in_gold = 0
    extra_in_gold = 0
    duplicate_gold_rows = 0

    for row in details:

        status = row.get("status")

        if status == "MATCH":
            matched += 1

        elif status == "COUNT_MISMATCH":
            count_mismatches += 1

        elif status == "MISSING_IN_GOLD":
            missing_in_gold += 1

        elif status == "EXTRA_IN_GOLD":
            extra_in_gold += 1

        if int(row.get("gold_row_count") or 0) > 1:
            duplicate_gold_rows += 1

    validation_passed = (
        count_mismatches == 0
        and missing_in_gold == 0
        and extra_in_gold == 0
        and duplicate_gold_rows == 0
    )

    summary = {
        "total_categories": total_categories,
        "matched": matched,
        "count_mismatches": count_mismatches,
        "missing_in_gold": missing_in_gold,
        "extra_in_gold": extra_in_gold,
        "duplicate_gold_rows": duplicate_gold_rows,
        "validation_passed": validation_passed
    }

    return {
        "source_table": source_table,
        "gold_table": gold_table,
        "group_columns": group_columns,
        "summary": summary,
        "details": details
    }
