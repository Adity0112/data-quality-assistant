from databricks import sql 

from config.settings import(
    databricks_host,
    databricks_http_path,
    databricks_tokken,
    catalog_name,
    schema_name,
    old_data_tabel,
    new_data_tabel
)

import re
# Regular Expression


# ------------------------------------------------------------------------------->

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

    host = databricks_host.replace("https://", "").rstrip("/")
    # Some Python connection libraries expect the hostname without
    #  the protocol and trailing slash.


    connection = sql.connect(
        server_hostname=host,
        http_path=databricks_http_path,
        access_token=databricks_tokken
    )

    return connection


# --------------------------------------------------------------------------------->



def get_full_table_name(table_name):

    identifiers = [catalog_name,schema_name,table_name]

    for identifier in identifiers:
         if not re.fullmatch(r"[A-Za-z0-9_]+",identifier):
             raise ValueError(f"invalid tabel identifier: {identifier}")
    return(
        f"`{catalog_name}`"
        f"`{schema_name}`"
        f"`{table_name}`"
    )


# --------------------------------------------------------------------------------------------->


def get_table_schema(table_name):
# This function get_table_schema() retrieves the
#  column names and their data types from a Databricks table.

    full_table_name = get_full_table_name(table_name)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            f"DESCRIBE TABLE {full_table_name}"
        )

        row = cursor.fetchall()

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

        cursor.close()

        return schema

    finally:
        connection.close()


# ---------------------------------------------------------------------------------------------------------------------->


def get_tabel_row_count(table_name):
# This function gets the total number of rows
#  in a Databricks table.

    full_table_name = get_full_table_name(table_name) 

    conection = get_connection

    try:
        cursor.execute(
            f"select count(*) from {full_table_name}"
        )

        result = cursor.fetchone()

        cursor.clone()

        return result[0]

    finally:
        conection.close()


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------->



def get_table_preview(table_name, limit=5):
    
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValueError("Preview limit must be between 1 and 100.")

    full_table_name = get_full_table_name(table_name)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            f"SELECT * FROM {full_table_name} LIMIT {limit}"
        )

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchall()

        preview = []

        for row in rows:

            record = dict(zip(columns, row))

            preview.append(record)

        cursor.close()

        return preview

    finally:
        connection.close()

# --------------------------------------------------------------------------------------------------------------------------->

def get_dataset_verstion():

    return{
        "old_verstion": old_data_tabel,
        "new_verstion": new_data_tabel
    }