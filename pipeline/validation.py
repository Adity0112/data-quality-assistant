
import json

from config.settings import (
    new_data_table,
    bronze_history_table
)

from pipeline.ingestion import (
    get_full_table_name,
    execute_query
)

from pipeline.snapshot_manager import (
    save_bronze_snapshot,
    get_bronze_history,
    validate_snapshot_id
)

from reports.quality_report import (
    generate_quality_report,
    print_quality_report
)


# ------------------------------------------------
# 1. GET SNAPSHOT ROW COUNT
# ------------------------------------------------

def get_snapshot_row_count(snapshot_id):

    snapshot_id = validate_snapshot_id(snapshot_id)

    history_table = get_full_table_name(
        bronze_history_table
    )

    query = f"""
        SELECT COUNT(*)
        FROM {history_table}
        WHERE snapshot_id = '{snapshot_id}'
    """

    result = execute_query(query)

    return result[0][0]


# ------------------------------------------------
# 2. ROW COUNT COMPARISON
# ------------------------------------------------

def check_row_count(
    current_snapshot_id,
    previous_snapshot_id=None
):

    current_snapshot_id = validate_snapshot_id(
        current_snapshot_id
    )

    current_count = get_snapshot_row_count(
        current_snapshot_id
    )

    if previous_snapshot_id is None:

        return {
            "current_row_count": current_count,
            "previous_row_count": None,
            "row_count_difference": None,
            "message": "No previous snapshot available."
        }

    previous_snapshot_id = validate_snapshot_id(
        previous_snapshot_id
    )

    previous_count = get_snapshot_row_count(
        previous_snapshot_id
    )

    return {
        "current_row_count": current_count,
        "previous_row_count": previous_count,
        "row_count_difference": current_count - previous_count
    }


# ------------------------------------------------
# 3. GET SNAPSHOT HISTORY
# ------------------------------------------------

def get_history_summary():

    history = get_bronze_history()

    print("\n========== BRONZE SNAPSHOT HISTORY ==========\n")

    for snapshot in history:

        print("Snapshot ID:", snapshot["snapshot_id"])

        print("Timestamp:", snapshot["snapshot_timestamp"])

        print("Total Records:", snapshot["total_records"])

        print("----------------------------------")

    return history


# ------------------------------------------------
# 4. MAIN VALIDATION PIPELINE
# ------------------------------------------------

def run_validation():

    print("\n==========================================")

    print(" DATA QUALITY & IMPACT ANALYSIS ASSISTANT")

    print("==========================================\n")

    try:

        # STEP 1: GET PREVIOUS SNAPSHOT

        print("Getting previous snapshot history...")

        previous_history = get_bronze_history()

        previous_snapshot_id = (
            previous_history[0]["snapshot_id"]
            if previous_history
            else None
        )

        print(
            "Previous Snapshot:",
            previous_snapshot_id
        )

        # STEP 2: SAVE CURRENT DATASET SNAPSHOT

        print("\nSaving current dataset snapshot...")

        snapshot_result = save_bronze_snapshot(
            new_data_table
        )

        current_snapshot_id = snapshot_result["snapshot_id"]

        print("Snapshot saved successfully.")

        print("Snapshot ID:", current_snapshot_id)

        # STEP 3: ROW COUNT VALIDATION

        print("\n1. Running Row Count Comparison...")

        row_count_result = check_row_count(
            current_snapshot_id,
            previous_snapshot_id
        )

        # STEP 4: GENERATE QUALITY REPORT

        print("\n2. Running Data Quality Checks...")

        quality_report = generate_quality_report(
            snapshot_id=current_snapshot_id,
            previous_snapshot_id=previous_snapshot_id
        )

        # STEP 5: GET SNAPSHOT HISTORY

        print("\n3. Retrieving Snapshot History...")

        history_result = get_history_summary()

        # STEP 6: BUILD FINAL REPORT

        final_report = {

            "source_table": new_data_table,

            "current_snapshot": snapshot_result,

            "previous_snapshot_id": previous_snapshot_id,

            "row_count_validation": row_count_result,

            "quality_report": quality_report,

            "historical_snapshots": history_result,

            "overall_status": quality_report["overall_status"]

        }

        # STEP 7: PRINT FINAL REPORT

        print("\n==========================================")

        print(" FINAL DATA QUALITY REPORT")

        print("==========================================\n")

        print("Source Table:", new_data_table)

        print("Current Snapshot:", current_snapshot_id)

        print("Previous Snapshot:", previous_snapshot_id)

        print(
            "Current Records:",
            row_count_result["current_row_count"]
        )

        print(
            "Previous Records:",
            row_count_result["previous_row_count"]
        )

        print(
            "Row Count Difference:",
            row_count_result["row_count_difference"]
        )

        print(
            "Overall Status:",
            final_report["overall_status"]
        )

        print_quality_report(quality_report)

        print("\n==========================================")

        print("VALIDATION PIPELINE COMPLETED")

        print("==========================================\n")

        return final_report

    except Exception as error:

        print("\nERROR IN VALIDATION PIPELINE")

        print(str(error))

        raise


# ------------------------------------------------
# 5. APPLICATION ENTRY POINT
# ------------------------------------------------

if __name__ == "__main__":

    report = run_validation()

    print("\n========== JSON REPORT ==========\n")

    print(
        json.dumps(
            report,
            indent=4,
            default=str
        )
    )
