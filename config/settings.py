import os 
# Retrieves environment variables
from dotenv import load_dotenv

load_dotenv()  
# 	Reads settings from your .env file.

databricks_host = os.getenv("")
databricks_http_path = os.getenv("")
databricks_tokken = os.getenv("")

catalog_name =""
schema_name = ""

old_data_tabel = ""
new_data_tabel = ""


APP_TITLE = "Data Quality & Impact Analysis Assistant"

DEBUG = True