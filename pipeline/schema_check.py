from pipeline.ingestion import get_table_schema

from config.settings import (
    old_data_tabel,
    new_data_tabel
)


def compare_schemas(old_tabel, new_tabel):

    # 1. Get schemas of both tables
    old_schema = get_table_schema(old_tabel)
    new_schema = get_table_schema(new_tabel)

    # 2. Convert schema lists into dictionaries
    old_columns = {
        column["column_name"]: column["data_type"]
        for column in old_schema
    }

    new_columns = {
        column["column_name"]: column["data_type"]
        for column in new_schema
    }

    # 3. Find removed columns
    removed_columns = []

    for column, data_type in old_columns.items():

        if column not in new_columns:

            removed_columns.append({
                "column_name": column,
                "data_type": data_type
            })

    # 4. Find added columns
    added_columns = []

    for column, data_type in new_columns.items():

        if column not in old_columns:

            added_columns.append({
                "column_name": column,
                "data_type": data_type
            })

    # 5. Find changed data types
    changed_types = []

    for column in old_columns:

        if column in new_columns:

            old_type = old_columns[column]
            new_type = new_columns[column]

            if old_type.lower() != new_type.lower():

                changed_types.append({
                    "column_name": column,
                    "old_type": old_type,
                    "new_type": new_type
                })

    # 6. Find unchanged columns
    unchanged_columns = []

    for column in old_columns:

        if (
            column in new_columns
            and old_columns[column].lower()
            == new_columns[column].lower()
        ):

            unchanged_columns.append(column)

    # 7. Return comparison result
    return {
        "old_tabel": old_tabel,
        "new_tabel": new_tabel,
        "added_columns": added_columns,
        "removed_columns": removed_columns,
        "changed_types": changed_types,
        "unchanged_columns": unchanged_columns,

        "has_changes": bool(
            added_columns or removed_columns or changed_types
        )
    }


def run_schema_check():

    result = compare_schemas(
        old_data_tabel,
        new_data_tabel
    )

    return result