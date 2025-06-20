import snowflake.connector
import pandas as pd
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Configuration Snowflake
config = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
}

def get_cursor():
    conn = snowflake.connector.connect(**config)
    cursor = conn.cursor()
    return cursor


def get_table(table_name="DEMO_SEG_CLIENT", limit=10):
    cursor = get_cursor()
    if limit > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    else:
        cursor.execute(f"SELECT * FROM {table_name}")
    sample = cursor.fetch_pandas_all()
    return sample   


if __name__ == "__main__":
    print(get_table())
