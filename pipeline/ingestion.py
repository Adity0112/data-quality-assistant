
from databricks import sql
import re

from config.settings import (
    databricks_host,
    databricks_http_path,
    databricks_tokken,
    catalog_name,
    schema_name,
    old_data_table,
    new_data_table
)


# ------------------------------------------------
# 1. Databricks Connection
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
# 2. Validate and Get Full Table Name
# ------------------------------------------------

def get_full_table_name(table_name):

    identifiers = [
        catalog_name,
        schema_name,
        table_name
    ]

    for identifier in identifiers:

        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"[A-Za-z0-9_]+", identifier)
        ):
            raise ValueError(
                f"Invalid table identifier: {identifier}"
            )

    return (
        f"`{catalog_name}`."
        f"`{schema_name}`."
        f"`{table_name}`"
    )


# ------------------------------------------------
# 3. Execute SQL Query
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

            return cursor.fetchall()

        finally:
            cursor.close()

    finally:
        connection.close()


# ------------------------------------------------
# 4. Get Table Schema
# ------------------------------------------------

def get_table_schema(table_name):

    full_table_name = get_full_table_name(table_name)

    query = f"""
        DESCRIBE TABLE {full_table_name}
    """

    rows = execute_query(query)

    schema = []

    for row in rows:

        column_name = row[0]
        data_type = row[1]

        if not column_name or column_name.startswith("#"):
            continue

        schema.append({
            "column_name": column_name,
            "data_type": data_type
        })

    return schema


# ------------------------------------------------
# 5. Get Table Row Count
# ------------------------------------------------

def get_table_row_count(table_name):

    full_table_name = get_full_table_name(table_name)

    query = f"""
        SELECT COUNT(*)
        FROM {full_table_name}
    """

    result = execute_query(query)

    return result[0][0]


# ------------------------------------------------
# 6. Get Table Preview
# ------------------------------------------------

def get_table_preview(table_name, limit=5):

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 100
    ):
        raise ValueError(
            "Preview limit must be between 1 and 100."
        )

    full_table_name = get_full_table_name(table_name)

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
# 7. Get Dataset Versions
# ------------------------------------------------

def get_dataset_version():

    return {
        "old_version": old_data_table,
        "new_version": new_data_table
    }
