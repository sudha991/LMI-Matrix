import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=10.0.176.120;"
    "DATABASE=erp;"
    "UID=erpadmin;"
    "PWD=erp@admin"
)

cursor = conn.cursor()
print("Connected to database!")