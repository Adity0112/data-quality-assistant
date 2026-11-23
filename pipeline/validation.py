
from pipeline.ingestion import get_table_row_count

from pipeline.schema_check import (
    run_schema_check
)

from pipeline.null_duplicate_check import (
    run_null_duplicate_check
)

from pipeline.datatypecheck import (
    run_datatype_check
)

from config.settings import (
    old_data_table,
    new_data_table
)


# ------------------------------------------------
# Expected Employee Schema
# ------------------------------------------------

expected_schema = {

    "ID": "INT",
    "Name": "STRING",
    "Age": "INT",
    "Salary": "DOUBLE",
    "Department": "STRING"

}


# ------------------------------------------------
# 1. Row Count Validation
# ------------------------------------------------

def check_row_count():

    old_count = get_table_row_count(old_data_table)

    new_count = get_table_row_count(new_data_table)

    return {

        "old_row_count": old_count,

        "new_row_count": new_count,

        "row_count_match": old_count == new_count

    }


# ------------------------------------------------
# 2. Main Validation Pipeline
# ------------------------------------------------

def run_validation():

    print("\n========== VALIDATION STARTED ==========\n")


    # STEP 1: Row Count Validation

    row_count_result = check_row_count()

    print("1. Row Count Validation Completed")


    # STEP 2: Schema Validation

    schema_result = run_schema_check()

    print("2. Schema Validation Completed")


    # STEP 3: Null and Duplicate Validation

    quality_result = run_null_duplicate_check(
        new_data_table
    )

    print("3. Null and Duplicate Validation Completed")


    # STEP 4: Datatype Validation

    datatype_result = run_datatype_check(
        new_data_table,
        expected_schema
    )

    print("4. Datatype Validation Completed")


    # STEP 5: Final Validation Status

    validation_status = all([

        row_count_result["row_count_match"],

        not schema_result["has_changes"],

        not quality_result["has_quality_issues"],

        not datatype_result["has_datatype_issues"]

    ])


    # STEP 6: Generate Final Report

    final_report = {

        "old_table": old_data_table,

        "new_table": new_data_table,

        "row_count_validation": row_count_result,

        "schema_validation": schema_result,

        "null_duplicate_validation": quality_result,

        "datatype_validation": datatype_result,

        "overall_status": (

            "PASSED"

            if validation_status

            else "FAILED"

        )

    }


    # STEP 7: Print Final Report

    print("\n========== FINAL VALIDATION REPORT ==========\n")

    print("Old Table:", old_data_table)

    print("New Table:", new_data_table)

    print(
        "Row Count:",
        "PASSED" if row_count_result["row_count_match"]
        else "FAILED"
    )

    print(
        "Schema:",
        "FAILED" if schema_result["has_changes"]
        else "PASSED"
    )

    print(
        "Null Check:",
        "FAILED" if quality_result["null_check"]["has_nulls"]
        else "PASSED"
    )

    print(
        "Duplicate Check:",
        "FAILED" if quality_result["duplicate_check"]["has_duplicates"]
        else "PASSED"
    )

    print(
        "Datatype:",
        "FAILED" if datatype_result["has_datatype_issues"]
        else "PASSED"
    )

    print("\nOVERALL STATUS:", final_report["overall_status"])

    print("\n============================================\n")


    return final_report
