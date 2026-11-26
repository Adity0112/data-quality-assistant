
from langchain_core.tools import tool

# ------------------------------------------------
# DATA QUALITY FUNCTIONS
# ------------------------------------------------

from pipeline.null_duplicate_check import (
    check_null_values,
    check_duplicates,
    run_null_duplicate_check,
    compare_latest_snapshot_nulls
)

from pipeline.schema_check import run_schema_check
from pipeline.datatypecheck import run_datatype_check


# ------------------------------------------------
# SNAPSHOT FUNCTIONS
# ------------------------------------------------

from pipeline.snapshot_manager import (
    get_bronze_history,
    validate_snapshot_id
)

from pipeline.snapshot_comparison import (
    compare_snapshots,
    compare_latest_snapshots
)


# ------------------------------------------------
# DATA QUERY FUNCTIONS
# ------------------------------------------------

from pipeline.data_query import (
    get_dataset_info,
    get_row,
    filter_data,
    aggregate_data,
    get_record_by_id
)


# ================================================================
# PART 1: DATA QUALITY TOOLS
# ================================================================


# ------------------------------------------------
# 1. NULL CHECK TOOL
# ------------------------------------------------

@tool
def null_check_tool(snapshot_id: str):
    """Check null values in a specific snapshot using its snapshot UUID."""
    return check_null_values(snapshot_id)


# ------------------------------------------------
# 2. DUPLICATE CHECK TOOL
# ------------------------------------------------

@tool
def duplicate_check_tool(snapshot_id: str):
    """Check duplicate records in a specific snapshot using its snapshot UUID."""
    return check_duplicates(snapshot_id)


# ------------------------------------------------
# 3. NULL AND DUPLICATE CHECK TOOL
# ------------------------------------------------

@tool
def null_duplicate_tool(snapshot_id: str):
    """Check both null values and duplicate records in a specific snapshot."""
    return run_null_duplicate_check(snapshot_id)


# ------------------------------------------------
# 4. SCHEMA COMPARISON TOOL
# ------------------------------------------------

@tool
def schema_check_tool(snapshot_id_1: str, snapshot_id_2: str):
    """Compare the schemas of two snapshots using their UUIDs."""
    return run_schema_check(snapshot_id_1, snapshot_id_2)


# ------------------------------------------------
# 5. DATATYPE COMPARISON TOOL
# ------------------------------------------------

@tool
def datatype_check_tool(
    previous_snapshot_id: str,
    current_snapshot_id: str
):
    """Compare datatypes between two snapshots using their UUIDs."""
    return run_datatype_check(
        previous_snapshot_id,
        current_snapshot_id
    )


# ================================================================
# PART 2: SNAPSHOT MANAGEMENT TOOLS
# ================================================================


# ------------------------------------------------
# 6. SNAPSHOT HISTORY TOOL
# ------------------------------------------------

@tool
def snapshot_history_tool():
    """
    Get all available snapshots.

    History is ordered newest first:
    Snapshot 1 = Newest
    Last snapshot = Oldest
    """
    return get_bronze_history()


# ------------------------------------------------
# 7. LATEST SNAPSHOT NULL COMPARISON TOOL
# ------------------------------------------------

@tool
def compare_latest_nulls_tool():
    """Compare null values between the latest and previous snapshots."""
    return compare_latest_snapshot_nulls()


# ------------------------------------------------
# 8. LATEST SNAPSHOT COMPARISON TOOL
# ------------------------------------------------

@tool
def compare_latest_snapshots_tool():
    """
    Compare the latest and previous snapshots.

    Checks records, null values, duplicates,
    schema changes and datatype changes.
    """
    return compare_latest_snapshots()


# ------------------------------------------------
# 9. SELECTED SNAPSHOT COMPARISON TOOL
# ------------------------------------------------

@tool
def compare_selected_snapshots_tool(
    snapshot_1: str,
    snapshot_2: str
):
    """
    Compare any two snapshots.

    Accepts:
    - Snapshot positions: "1", "2", "5"
    - "latest"
    - "oldest"
    - Direct snapshot UUIDs

    Snapshot numbering is newest first.

    Examples:
    - Compare snapshot 1 and snapshot 5.
    - Compare latest and oldest.
    - Compare snapshot 2 and snapshot 4.
    """

    history = get_bronze_history()

    if not history:
        return {"error": "No snapshots found."}

    def resolve_snapshot(value):

        value = str(value).strip().lower()

        if value == "latest":
            return history[0]["snapshot_id"]

        if value == "oldest":
            return history[-1]["snapshot_id"]

        if value.startswith("snapshot "):
            value = value.replace("snapshot ", "", 1).strip()

        try:
            position = int(value)

        except ValueError:
            return validate_snapshot_id(value)

        if position < 1 or position > len(history):
            raise ValueError(
                f"Snapshot {position} does not exist. "
                f"Only {len(history)} snapshots are available."
            )

        return history[position - 1]["snapshot_id"]

    snapshot_id_1 = resolve_snapshot(snapshot_1)
    snapshot_id_2 = resolve_snapshot(snapshot_2)

    return compare_snapshots(
        snapshot_id_1,
        snapshot_id_2
    )


# ================================================================
# PART 3: SQL DATA QUERY TOOLS
# ================================================================


# ------------------------------------------------
# 10. DATASET INFORMATION TOOL
# ------------------------------------------------

@tool
def dataset_info_tool():
    """
    Get dataset information including:
    table name, total records, column names,
    datatypes and sample records.
    """
    return get_dataset_info()


# ------------------------------------------------
# 11. GET ROW TOOL
# ------------------------------------------------

@tool
def get_row_tool(column_name: str, value: str):
    """
    Retrieve records from the current dataset
    using an exact column value.

    Example:
    Find tickets where subject is Account Disruption.
    """
    return get_row(
        column_name,
        value
    )


# ------------------------------------------------
# 12. FILTER DATA TOOL
# ------------------------------------------------

@tool
def filter_data_tool(
    column_name: str,
    operator: str,
    value: str,
    limit: int = 20
):
    """
    Filter dataset records using a column,
    comparison operator and value.

    Supported operators:
    =, !=, >, >=, <, <=, LIKE

    Example:
    Find records where priority = high.
    """
    return filter_data(
        column_name,
        operator,
        value,
        limit
    )


# ------------------------------------------------
# 13. AGGREGATE DATA TOOL
# ------------------------------------------------

@tool
def aggregate_data_tool(
    aggregation: str,
    column_name: str = None,
    group_by_column: str = None
):
    """
    Perform SQL aggregations on the current dataset.

    Supported aggregations:
    COUNT, SUM, AVG, MIN, MAX

    Examples:
    - Count all records.
    - Count records grouped by priority.
    - Count records grouped by language.
    - Find the average or maximum of a numeric column.
    """
    return aggregate_data(
        aggregation,
        column_name,
        group_by_column
    )


# ------------------------------------------------
# 14. GET RECORD BY UNIQUE ROW ID TOOL
# ------------------------------------------------

@tool
def get_record_by_id_tool(row_id: str):
    """
    Retrieve one complete record from bronze history
    using its unique row UUID.

    Example:
    Find the record with row ID
    fbc40fb3-6a1f-4867-b238-ded4af885b91.
    """
    return get_record_by_id(row_id)


# ================================================================
# PART 4: REGISTER ALL TOOLS
# ================================================================

tools = [

    # Data quality
    null_check_tool,
    duplicate_check_tool,
    null_duplicate_tool,
    schema_check_tool,
    datatype_check_tool,

    # Snapshot management
    snapshot_history_tool,
    compare_latest_nulls_tool,
    compare_latest_snapshots_tool,
    compare_selected_snapshots_tool,

    # SQL data querying
    dataset_info_tool,
    get_row_tool,
    filter_data_tool,
    aggregate_data_tool,
    get_record_by_id_tool

]
