
import uuid

from pipeline.ingestion import (
    get_connection,
    get_full_table_name,
    execute_query,
    get_table_schema
)

from config.settings import (
    bronze_history_table,
    snapshot_schema_table
)


# ------------------------------------------------
# 1. HELPER FUNCTIONS
# ------------------------------------------------

def validate_snapshot_id(snapshot_id):

    if not isinstance(snapshot_id, str):
        raise ValueError("Snapshot ID must be a string.")

    try:
        return str(uuid.UUID(snapshot_id))

    except ValueError:
        raise ValueError("Invalid snapshot UUID.")


def escape_sql_string(value):

    return str(value).replace("'", "''")


def quote_column(column_name):

    return f"`{column_name.replace('`', '``')}`"


# ------------------------------------------------
# 2. CREATE BRONZE HISTORY TABLE
# ------------------------------------------------

def create_history_table(source_table):

    source = get_full_table_name(source_table)
    history = get_full_table_name(bronze_history_table)

    source_schema = get_table_schema(source_table)

    if not source_schema:
        raise ValueError("Source Bronze table has no columns.")

    # Reserved metadata column names.
    reserved_columns = {
        "snapshot_id",
        "snapshot_timestamp",
        "source_table"
    }

    source_columns = {
        column["column_name"].lower()
        for column in source_schema
    }

    if source_columns.intersection(reserved_columns):
        raise ValueError(
            "Source table contains a reserved snapshot column."
        )

    # Create history table if it does not exist.
    query = f"""
        CREATE TABLE IF NOT EXISTS {history}
        USING DELTA
        AS
        SELECT
            *,
            CAST(NULL AS STRING) AS snapshot_id,
            CAST(NULL AS TIMESTAMP) AS snapshot_timestamp,
            CAST(NULL AS STRING) AS source_table
        FROM {source}
        WHERE 1 = 0
    """

    execute_query(query)

    # Get existing history columns.
    history_schema = get_table_schema(bronze_history_table)

    history_columns = {
        column["column_name"].lower()
        for column in history_schema
    }

    # Add missing metadata columns.
    metadata_columns = {
        "snapshot_id": "STRING",
        "snapshot_timestamp": "TIMESTAMP",
        "source_table": "STRING"
    }

    for column_name, data_type in metadata_columns.items():

        if column_name not in history_columns:

            alter_query = f"""
                ALTER TABLE {history}
                ADD COLUMNS ({quote_column(column_name)} {data_type})
            """

            execute_query(alter_query)

            history_columns.add(column_name)

    # Add newly introduced source columns.
    for column in source_schema:

        column_name = column["column_name"]
        data_type = column["data_type"]

        if column_name.lower() not in history_columns:

            alter_query = f"""
                ALTER TABLE {history}
                ADD COLUMNS ({quote_column(column_name)} {data_type})
            """

            execute_query(alter_query)

            history_columns.add(column_name.lower())

    return {
        "history_table": bronze_history_table,
        "status": "CREATED_OR_ALREADY_EXISTS"
    }


# ------------------------------------------------
# 3. CREATE SNAPSHOT SCHEMA TABLE
# ------------------------------------------------

def create_snapshot_schema_table():

    schema_table = get_full_table_name(snapshot_schema_table)

    query = f"""
        CREATE TABLE IF NOT EXISTS {schema_table} (

            snapshot_id STRING,
            source_table STRING,
            column_name STRING,
            data_type STRING,
            snapshot_timestamp TIMESTAMP

        )
        USING DELTA
    """

    execute_query(query)

    return {
        "schema_table": snapshot_schema_table,
        "status": "CREATED_OR_ALREADY_EXISTS"
    }


# ------------------------------------------------
# 4. SAVE SNAPSHOT SCHEMA
# ------------------------------------------------

def save_snapshot_schema(
    snapshot_id,
    source_table,
    source_schema
):

    snapshot_id = validate_snapshot_id(snapshot_id)

    create_snapshot_schema_table()

    schema_table = get_full_table_name(snapshot_schema_table)

    values = []

    for column in source_schema:

        values.append(
            f"""
            (
                '{escape_sql_string(snapshot_id)}',
                '{escape_sql_string(source_table)}',
                '{escape_sql_string(column["column_name"])}',
                '{escape_sql_string(column["data_type"])}',
                CURRENT_TIMESTAMP()
            )
            """
        )

    if not values:
        raise ValueError("Source schema is empty.")

    query = f"""
        INSERT INTO {schema_table}
        VALUES {", ".join(values)}
    """

    execute_query(query)

    return {
        "snapshot_id": snapshot_id,
        "saved_columns": len(values),
        "status": "SUCCESS"
    }


# ------------------------------------------------
# 5. SAVE BRONZE SNAPSHOT
# ------------------------------------------------

def save_bronze_snapshot(source_table):

    # Read source schema.
    source_schema = get_table_schema(source_table)

    if not source_schema:
        raise ValueError("Source table has no columns.")

    # Ensure history table exists.
    create_history_table(source_table)

    source = get_full_table_name(source_table)
    history = get_full_table_name(bronze_history_table)

    # Generate unique snapshot ID.
    snapshot_id = str(uuid.uuid4())

    # Get source column names.
    columns = [
        quote_column(column["column_name"])
        for column in source_schema
    ]

    column_list = ", ".join(columns)

    safe_snapshot_id = escape_sql_string(snapshot_id)
    safe_source_table = escape_sql_string(source_table)

    # Insert source records into history table.
    insert_query = f"""
        INSERT INTO {history}
        (
            {column_list},
            snapshot_id,
            snapshot_timestamp,
            source_table
        )

        SELECT
            {column_list},
            '{safe_snapshot_id}',
            CURRENT_TIMESTAMP(),
            '{safe_source_table}'

        FROM {source}
    """

    execute_query(insert_query)

    # Save schema information.
    save_snapshot_schema(
        snapshot_id,
        source_table,
        source_schema
    )

    return {
        "source_table": source_table,
        "history_table": bronze_history_table,
        "snapshot_id": snapshot_id,
        "total_columns": len(source_schema),
        "status": "SUCCESS"
    }


# ------------------------------------------------
# 6. GET BRONZE SNAPSHOT HISTORY
# ------------------------------------------------

def get_bronze_history():

    history = get_full_table_name(bronze_history_table)

    query = f"""
        SELECT
            snapshot_id,
            snapshot_timestamp,
            source_table,
            COUNT(*) AS total_records

        FROM {history}

        WHERE snapshot_id IS NOT NULL

        GROUP BY
            snapshot_id,
            snapshot_timestamp,
            source_table

        ORDER BY snapshot_timestamp DESC
    """

    rows = execute_query(query)

    history_records = []

    for row in rows:

        history_records.append({
            "snapshot_id": row[0],
            "snapshot_timestamp": str(row[1]),
            "source_table": row[2],
            "total_records": row[3]
        })

    return history_records


# ------------------------------------------------
# 7. GET SNAPSHOT DATA
# ------------------------------------------------

def get_snapshot_data(snapshot_id):

    snapshot_id = validate_snapshot_id(snapshot_id)

    history = get_full_table_name(bronze_history_table)

    query = f"""
        SELECT *
        FROM {history}
        WHERE snapshot_id = '{snapshot_id}'
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        try:

            cursor.execute(query)

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
            cursor.close()

    finally:
        connection.close()


# ------------------------------------------------
# 8. GET LATEST TWO SNAPSHOTS
# ------------------------------------------------

def get_latest_snapshots():

    history = get_bronze_history()

    if len(history) < 2:

        return {
            "message": "At least two snapshots are required for comparison.",
            "snapshots": history
        }

    return {
        "previous_snapshot": history[1],
        "latest_snapshot": history[0]
    }
