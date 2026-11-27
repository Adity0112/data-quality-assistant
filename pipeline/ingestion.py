
from databricks import sql
import re

from config.settings import (
    databricks_host,
    databricks_http_path,
    databricks_tokken,
    catalog_name,
    schema_name,
    new_data_table
)


# ------------------------------------------------
# 1. VALIDATE IDENTIFIERS
# ------------------------------------------------

def validate_identifier(identifier):

    if (
        not isinstance(identifier, str)
        or not re.fullmatch(r"[A-Za-z0-9_]+", identifier)
    ):
        raise ValueError(
            f"Invalid Databricks identifier: {identifier}"
        )

    return identifier


# ------------------------------------------------
# 2. DATABRICKS CONNECTION
# ------------------------------------------------

def get_connection():

    if not all([
        databricks_host,
        databricks_http_path,
        databricks_tokken
    ]):
        raise ValueError(
            "Databricks credentials are missing. "
            "Please check your .env file."
        )

    host = databricks_host.replace(
        "https://", ""
    ).rstrip("/")

    connection = sql.connect(
        server_hostname=host,
        http_path=databricks_http_path,
        access_token=databricks_tokken
    )

    return connection


# ------------------------------------------------
# 3. GET FULL TABLE NAME
# ------------------------------------------------

def get_full_table_name(
    table_name,
    catalog=None,
    schema=None
):

    # Use default catalog and schema
    # when they are not provided

    catalog = catalog or catalog_name
    schema = schema or schema_name

    identifiers = [
        catalog,
        schema,
        table_name
    ]

    for identifier in identifiers:
        validate_identifier(identifier)

    return (
        f"`{catalog}`."
        f"`{schema}`."
        f"`{table_name}`"
    )


# ------------------------------------------------
# 4. EXECUTE SQL QUERY
# ------------------------------------------------

def execute_query(query, parameters=None):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        try:

            if parameters is None:
                cursor.execute(query)

            else:
                cursor.execute(query, parameters)

            if cursor.description is not None:
                return cursor.fetchall()

            return []

        finally:
            cursor.close()

    finally:
        connection.close()


# ------------------------------------------------
# 5. DISCOVER AVAILABLE CATALOGS
# ------------------------------------------------

def get_available_catalogs():

    query = """
        SHOW CATALOGS
    """

    rows = execute_query(query)

    return [
        row[0]
        for row in rows
    ]


# ------------------------------------------------
# 6. DISCOVER AVAILABLE SCHEMAS
# ------------------------------------------------

def get_available_schemas(catalog=None):

    catalog = catalog or catalog_name

    validate_identifier(catalog)

    query = f"""
        SHOW SCHEMAS IN `{catalog}`
    """

    rows = execute_query(query)

    return [
        row[0]
        for row in rows
    ]


# ------------------------------------------------
# 7. DISCOVER AVAILABLE TABLES
# ------------------------------------------------

def get_available_tables(
    catalog=None,
    schema=None
):

    catalog = catalog or catalog_name
    schema = schema or schema_name

    validate_identifier(catalog)
    validate_identifier(schema)

    query = f"""
        SHOW TABLES IN `{catalog}`.`{schema}`
    """

    rows = execute_query(query)

    tables = []

    for row in rows:

        tables.append({
            "catalog": catalog,
            "schema": schema,
            "table_name": row[1],
            "full_table_name": (
                f"{catalog}.{schema}.{row[1]}"
            )
        })

    return tables


# ------------------------------------------------
# 8. GET TABLE SCHEMA
# ------------------------------------------------

def get_table_schema(
    table_name,
    catalog=None,
    schema=None
):

    full_table_name = get_full_table_name(
        table_name,
        catalog,
        schema
    )

    query = f"""
        DESCRIBE TABLE {full_table_name}
    """

    rows = execute_query(query)

    table_schema = []

    for row in rows:

        column_name = row[0]
        data_type = row[1]

        if (
            not column_name
            or column_name.startswith("#")
        ):
            continue

        table_schema.append({
            "column_name": column_name,
            "data_type": data_type
        })

    return table_schema


# ------------------------------------------------
# 9. GET TABLE ROW COUNT
# ------------------------------------------------

def get_table_row_count(
    table_name,
    catalog=None,
    schema=None
):

    full_table_name = get_full_table_name(
        table_name,
        catalog,
        schema
    )

    query = f"""
        SELECT COUNT(*)
        FROM {full_table_name}
    """

    result = execute_query(query)

    return result[0][0]


# ------------------------------------------------
# 10. GET TABLE PREVIEW
# ------------------------------------------------

def get_table_preview(
    table_name,
    limit=5,
    catalog=None,
    schema=None
):

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 100
    ):
        raise ValueError(
            "Preview limit must be between 1 and 100."
        )

    full_table_name = get_full_table_name(
        table_name,
        catalog,
        schema
    )

    query = f"""
        SELECT *
        FROM {full_table_name}
        LIMIT {limit}
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
# 11. GET COMPLETE TABLE PROFILE
# ------------------------------------------------

def get_table_profile(
    table_name,
    catalog=None,
    schema=None
):

    full_table_name = get_full_table_name(
        table_name,
        catalog,
        schema
    )

    table_schema = get_table_schema(
        table_name,
        catalog,
        schema
    )

    total_rows = get_table_row_count(
        table_name,
        catalog,
        schema
    )

    preview = get_table_preview(
        table_name,
        limit=5,
        catalog=catalog,
        schema=schema
    )

    return {
        "table_name": full_table_name,
        "total_rows": total_rows,
        "total_columns": len(table_schema),
        "columns": table_schema,
        "sample_records": preview
    }


# ------------------------------------------------
# 12. GET CURRENT DATASET INFORMATION
# ------------------------------------------------

def get_dataset_version():

    return {
        "current_dataset": new_data_table
    }
