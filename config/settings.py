
import os
from pathlib import Path
from dotenv import load_dotenv


# ------------------------------------------------
# 1. Project Configuration
# ------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)


# ------------------------------------------------
# 2. Databricks Credentials
# ------------------------------------------------

databricks_host = os.getenv("DATABRICKS_HOST")

databricks_http_path = os.getenv("DATABRICKS_HTTP_PATH")

databricks_tokken = os.getenv("DATABRICKS_TOKEN")


# ------------------------------------------------
# 3. Database Configuration
# ------------------------------------------------

catalog_name = os.getenv("CATALOG_NAME", "workspace")

schema_name = os.getenv("SCHEMA_NAME", "default")


# ------------------------------------------------
# 4. Dataset Configuration
# ------------------------------------------------

new_data_table = os.getenv(
    "NEW_DATA_TABLE",
    "aa_dataset_tickets_multi_lang_5_2_50_version"
)


# ------------------------------------------------
# 5. Bronze History Configuration
# ------------------------------------------------

bronze_history_table = os.getenv(
    "BRONZE_HISTORY_TABLE",
    "bronze_tickets_history"
)

snapshot_schema_table = os.getenv(
    "SNAPSHOT_SCHEMA_TABLE",
    "bronze_snapshot_schema"
)


# ------------------------------------------------
# 6. Application Configuration
# ------------------------------------------------

APP_TITLE = "Data Quality & Impact Analysis Assistant"

DEBUG = True
