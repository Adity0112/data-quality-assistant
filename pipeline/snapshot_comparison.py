
from pipeline.snapshot_manager import (
    get_latest_snapshots,
    get_bronze_history,
    validate_snapshot_id
)

from pipeline.null_duplicate_check import (
    check_null_values,
    check_duplicates
)

from pipeline.schema_check import run_schema_check
from pipeline.datatypecheck import run_datatype_check


def compare_snapshots(snapshot_id_1, snapshot_id_2):

    snapshot_id_1 = validate_snapshot_id(snapshot_id_1)
    snapshot_id_2 = validate_snapshot_id(snapshot_id_2)

    if snapshot_id_1 == snapshot_id_2:
        raise ValueError("Please provide two different snapshot IDs.")

    history = get_bronze_history()

    snapshot_map = {
        item["snapshot_id"]: item
        for item in history
    }

    if snapshot_id_1 not in snapshot_map:
        raise ValueError("First snapshot was not found in history.")

    if snapshot_id_2 not in snapshot_map:
        raise ValueError("Second snapshot was not found in history.")

    snapshot_1 = snapshot_map[snapshot_id_1]
    snapshot_2 = snapshot_map[snapshot_id_2]

    # Record comparison
    record_difference = (
        snapshot_2["total_records"] - snapshot_1["total_records"]
    )

    # Null comparison
    null_1 = check_null_values(snapshot_id_1)
    null_2 = check_null_values(snapshot_id_2)

    null_difference = (
        sum(item["null_count"] for item in null_2["null_results"])
        - sum(item["null_count"] for item in null_1["null_results"])
    )

    # Duplicate comparison
    duplicate_1 = check_duplicates(snapshot_id_1)
    duplicate_2 = check_duplicates(snapshot_id_2)

    duplicate_difference = (
        duplicate_2["duplicate_count"]
        - duplicate_1["duplicate_count"]
    )

    # Schema comparison
    schema_comparison = run_schema_check(
        snapshot_id_1,
        snapshot_id_2
    )

    # Datatype comparison
    datatype_comparison = run_datatype_check(
        snapshot_id_1,
        snapshot_id_2
    )

    return {
        "snapshot_1": snapshot_1,
        "snapshot_2": snapshot_2,

        "record_comparison": {
            "snapshot_1_records": snapshot_1["total_records"],
            "snapshot_2_records": snapshot_2["total_records"],
            "difference": record_difference
        },

        "null_comparison": {
            "snapshot_1_total_nulls": sum(
                item["null_count"] for item in null_1["null_results"]
            ),
            "snapshot_2_total_nulls": sum(
                item["null_count"] for item in null_2["null_results"]
            ),
            "difference": null_difference
        },

        "duplicate_comparison": {
            "snapshot_1_duplicates": duplicate_1["duplicate_count"],
            "snapshot_2_duplicates": duplicate_2["duplicate_count"],
            "difference": duplicate_difference
        },

        "schema_comparison": schema_comparison,
        "datatype_comparison": datatype_comparison
    }


def compare_latest_snapshots():

    snapshots = get_latest_snapshots()

    if "message" in snapshots:
        return snapshots

    previous_id = snapshots["previous_snapshot"]["snapshot_id"]
    latest_id = snapshots["latest_snapshot"]["snapshot_id"]

    return compare_snapshots(previous_id, latest_id)
