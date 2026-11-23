
import os
from pathlib import Path
from dotenv import load_dotenv

# Find .env in the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

# Databricks credentials
databricks_host = os.getenv("DATABRICKS_HOST")
databricks_http_path = os.getenv("DATABRICKS_HTTP_PATH")
databricks_tokken = os.getenv("DATABRICKS_TOKEN")

# Database configuration
catalog_name = os.getenv("CATALOG_NAME")
schema_name = os.getenv("SCHEMA_NAME")

# Dataset configuration
old_data_table = os.getenv("OLD_DATA_TABLE")
new_data_table = os.getenv("NEW_DATA_TABLE")

APP_TITLE = "Data Quality & Impact Analysis Assistant"
DEBUG = True
