
import uuid

from pipeline.ingestion import (
    get_connection,
    get_full_table_name,
    get_table_schema,
    get_table_row_count,
    get_table_preview
)

from config.settings import (
    new_data_table,
    bronze_history_table
)


# ------------------------------------------------
# 1. GET DATASET TABLE
# ------------------------------------------------

def get_dataset_table():

    return get_full_table_name(new_data_table)


# ------------------------------------------------
# 2. VALIDATE COLUMN NAME
# ------------------------------------------------

def get_valid_column(column_name):

    schema = get_table_schema(new_data_table)

    for column in schema:

        if column["column_name"].lower() == column_name.lower():

            return column["column_name"]

    raise ValueError(
        f"Column '{column_name}' does not exist in the dataset."
    )


# ------------------------------------------------
# 3. EXECUTE SELECT QUERY
# ------------------------------------------------

def execute_select(query, parameters=None):

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        if parameters is None:
            cursor.execute(query)

        else:
            cursor.execute(query, parameters)

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchall()

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ------------------------------------------------
# 4. GET ROW USING COLUMN VALUE
# ------------------------------------------------

def get_row(column_name, value):

    column = get_valid_column(column_name)

    table = get_dataset_table()

    query = f"""
        SELECT *
        FROM {table}
        WHERE {quote_column(column)} = ?
        LIMIT 10
    """

    return execute_select(query, [value])


# ------------------------------------------------
# 5. FILTER DATA
# ------------------------------------------------

def filter_data(
    column_name,
    operator,
    value,
    limit=20
):

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 100
    ):

        raise ValueError("Limit must be between 1 and 100.")

    column = get_valid_column(column_name)

    table = get_dataset_table()

    allowed_operators = [
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "LIKE"
    ]

    operator = operator.upper().strip()

    if operator not in allowed_operators:

        raise ValueError("Unsupported filter operator.")

    query = f"""
        SELECT *
        FROM {table}
        WHERE {quote_column(column)} {operator} ?
        LIMIT {limit}
    """

    return execute_select(query, [value])


# ------------------------------------------------
# 6. AGGREGATE DATA
# ------------------------------------------------

def aggregate_data(
    aggregation,
    column_name=None,
    group_by_column=None
):

    aggregation = aggregation.upper().strip()

    allowed_aggregations = [
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX"
    ]

    if aggregation not in allowed_aggregations:

        raise ValueError("Unsupported aggregation.")

    table = get_dataset_table()

    if aggregation == "COUNT" and column_name is None:

        metric = "COUNT(*)"

    else:

        if not column_name:

            raise ValueError(
                f"{aggregation} requires a column name."
            )

        column = get_valid_column(column_name)

        metric = f"{aggregation}({quote_column(column)})"

    if group_by_column:

        group_column = get_valid_column(group_by_column)

        query = f"""
            SELECT
                {quote_column(group_column)} AS group_value,
                {metric} AS result

            FROM {table}

            GROUP BY {quote_column(group_column)}

            ORDER BY result DESC

            LIMIT 100
        """

    else:

        query = f"""
            SELECT {metric} AS result
            FROM {table}
        """

    return execute_select(query)


# ------------------------------------------------
# 7. GET DATASET INFORMATION
# ------------------------------------------------

def get_dataset_info():

    return {

        "table_name": new_data_table,

        "total_records": get_table_row_count(
            new_data_table
        ),

        "columns": get_table_schema(
            new_data_table
        ),

        "preview": get_table_preview(
            new_data_table,
            limit=5
        )

    }


# ------------------------------------------------
# 8. HELPER: QUOTE COLUMN NAME
# ------------------------------------------------

def quote_column(column_name):

    return f"`{column_name.replace('`', '``')}`"


# ------------------------------------------------
# 9. GET RECORD USING UNIQUE ROW ID
# ------------------------------------------------

def get_record_by_id(row_id):

    # Validate UUID.
    try:

        row_id = str(uuid.UUID(row_id))

    except (ValueError, TypeError, AttributeError):

        raise ValueError("Invalid row ID.")

    # Get bronze history table.
    history = get_full_table_name(
        bronze_history_table
    )

    # Search record using unique row ID.
    query = f"""
        SELECT *
        FROM {history}
        WHERE row_id = ?
        LIMIT 1
    """

    records = execute_select(
        query,
        [row_id]
    )

    if not records:

        return {
            "message": "No record found for this row ID.",
            "row_id": row_id
        }

    return records[0]
