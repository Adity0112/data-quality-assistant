
from pipeline.schema_check import run_schema_check
from pipeline.null_duplicate_check import run_null_duplicate_check
from pipeline.snapshot_manager import validate_snapshot_id


def generate_quality_report(snapshot_id, previous_snapshot_id=None):

    snapshot_id = validate_snapshot_id(snapshot_id)

    if previous_snapshot_id:
        previous_snapshot_id = validate_snapshot_id(
            previous_snapshot_id
        )

        if previous_snapshot_id == snapshot_id:
            raise ValueError(
                "Previous and current snapshot IDs must be different."
            )

    # Run NULL and duplicate checks
    null_duplicate_result = run_null_duplicate_check(snapshot_id)

    schema_result = None
    datatype_result = None

    # Compare schemas when a previous snapshot exists
    if previous_snapshot_id:

        schema_result = run_schema_check(
            previous_snapshot_id,
            snapshot_id
        )

        datatype_result = {
            "datatype_changes": schema_result["changed_datatypes"],
            "has_datatype_issues": bool(
                schema_result["changed_datatypes"]
            ),
            "total_issues": len(
                schema_result["changed_datatypes"]
            )
        }

    # Calculate issue status
    has_null_issues = (
        null_duplicate_result["null_check"]["has_null_values"]
    )

    has_duplicate_issues = (
        null_duplicate_result["duplicate_check"]["has_duplicates"]
    )

    has_datatype_issues = (
        datatype_result["has_datatype_issues"]
        if datatype_result else False
    )

    has_schema_changes = (
        schema_result["has_changes"]
        if schema_result else False
    )

    has_quality_issues = (
        has_null_issues
        or has_duplicate_issues
        or has_schema_changes
    )

    # Prepare final report
    report = {
        "snapshot_id": snapshot_id,
        "previous_snapshot_id": previous_snapshot_id,

        "overall_status": (
            "ISSUES_FOUND"
            if has_quality_issues
            else "PASSED"
        ),

        "quality_checks": {
            "null_check": null_duplicate_result["null_check"],
            "duplicate_check": null_duplicate_result["duplicate_check"],
            "datatype_check": datatype_result,
            "schema_check": schema_result
        },

        "summary": {
            "has_null_issues": has_null_issues,
            "has_duplicate_issues": has_duplicate_issues,
            "has_datatype_issues": has_datatype_issues,
            "has_schema_changes": has_schema_changes,
            "has_quality_issues": has_quality_issues
        }
    }

    return report


def print_quality_report(report):

    print("\n" + "=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)

    print("Current Snapshot:", report["snapshot_id"])
    print("Previous Snapshot:", report["previous_snapshot_id"])
    print("Overall Status:", report["overall_status"])

    print("\nQUALITY SUMMARY")
    print("-" * 40)

    for key, value in report["summary"].items():
        print(f"{key}: {value}")

    schema_result = report["quality_checks"]["schema_check"]

    if schema_result:

        print("\nSCHEMA COMPARISON")
        print("-" * 40)

        print("Added Columns:", schema_result["added_columns"])
        print("Removed Columns:", schema_result["removed_columns"])
        print("Changed Datatypes:", schema_result["changed_datatypes"])
        print("Unchanged Columns:", schema_result["unchanged_columns"])

    else:
        print("\nSchema comparison skipped: no previous snapshot.")
        
    print("=" * 60)
