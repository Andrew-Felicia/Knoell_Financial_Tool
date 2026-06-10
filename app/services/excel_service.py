import pandas as pd

# a tool that creates a fake file in memory. Instead of saving an Excel file to disk and 
# reading it back, you can create it directly in RAM. Much faster for exports
from io import BytesIO
from ..models import db, ExcelTable, TableRow



# User uploads Excel file
#         │
#         ▼
# read_excel_file()       ← turns .xlsx into a DataFrame
#         │
#         ▼
# detect_columns()        ← figures out column types
#         │
#         ▼
# import_dataframe_to_db() ← saves everything to PostgreSQL
#         │
#         ▼
#   (data lives in DB)
#         │
#         ▼ (when user clicks Export)
# export_table_to_excel() ← reads from DB, creates .xlsx in memory
#         │
#         ▼
#   sent to browser as download



def read_excel_file(file_path: str) -> pd.DataFrame:
    """Read an Excel file, clean column names, replace NaN with None."""
    #using dataframe to record the excel data.
    #What is a DataFrame?
    # A DataFrame is pandas' way of representing a table — rows and columns, just like Excel.
    df = pd.read_excel(file_path, engine="openpyxl")

    #Cleans up column names. This is a list comprehension — a compact Python loop. It goes through every column name and:
    # str(c) — converts it to a string (in case someone put a number as a column name)
    # .strip() — removes any accidental spaces at the start or end
    # So "  Name  " becomes "Name", and 123 becomes "123".

    #Replaces all empty cells (NaN) with None. This matters because:
    # Excel empty cells → pandas reads them as NaN (Not a Number)
    # NaN cannot be stored in JSON (which is what TableRow.data uses)
    # None can be stored in JSON as null
    # So this line makes every empty cell JSON-safe.
    df.columns = [str(c).strip() for c in df.columns]

    return df.where(pd.notna(df), None)



# What it does:
# Looks at each column in the DataFrame and figures out what data type it is, 
# then returns a list describing all columns. This list gets saved into ExcelTable.columns as JSON.
#confusing about this.
def detect_columns(df: pd.DataFrame) -> list:
    """Return column metadata: [{"name": "Age", "type": "number"}, ...]"""
    type_map = {"int64": "number", "float64": "number",
                "bool": "boolean", "object": "text"}
    return [
        {"name": col, "type": "date" if "datetime" in str(dt) else type_map.get(str(dt), "text")}
        for col, dt in df.dtypes.items()
    ]


# This is the core import function. It takes a DataFrame and saves it permanently to PostgreSQL.
def import_dataframe_to_db(df, table_name: str, user_id: int) -> ExcelTable:
    """Save a DataFrame as ExcelTable + TableRow records."""

    # Creates the ExcelTable record (the metadata) and adds it to the session. 
    # A session is like a shopping basket — you add things to it, 
    # and nothing actually goes to the database until you call commit().
    table = ExcelTable(name=table_name, columns=detect_columns(df),
                       row_count=len(df), created_by=user_id)
    db.session.add(table)

    # This is subtle but important. flush() sends the INSERT to PostgreSQL without committing. 
    # Why? Because we need the table.id that PostgreSQL generates, so we can use it in the rows below. 
    # Without flush(), table.id would still be None at this point.
    db.session.flush()  # get the ID without committing yet

    #bulk_save_objects() — inserts all rows in one efficient database operation instead of one 
    #INSERT per row. For a 10,000 row Excel file this is dramatically faster.
    db.session.bulk_save_objects([
        TableRow(table_id=table.id, row_index=i, data=row.to_dict())
        for i, row in df.iterrows()
    ])


    #commit() finalizes everything — both the ExcelTable and all the TableRow records are now 
    #permanently saved. Returns the ExcelTable object so the caller can use it (e.g. to get its ID for a redirect).
    db.session.commit()

    return table

def export_table_to_excel(table: ExcelTable) -> BytesIO:
    """Convert a stored table back to an .xlsx file in memory."""

    #table.rows — fetches all TableRow records for this table (SQLAlchemy relationship)
    # sorted(..., key=lambda r: r.row_index) — sorts them by original row order. Without this, 
    # rows might come back in random database order
    # r.data — extracts just the JSON data from each row
    rows = [r.data for r in sorted(table.rows, key=lambda r: r.row_index)]

    #Creates an empty in-memory "file". No file is written to disk — everything stays in RAM.
    buffer = BytesIO()

    #pd.DataFrame(rows) — converts the list of dictionaries back into a DataFrame
    # ExcelWriter(buffer) — creates an Excel writer that writes into the buffer instead of a real file
    # .to_excel(writer, index=False) — writes the DataFrame as an Excel sheet. index=False means don't 
    # add a row number column (0, 1, 2...) — keep it clean.
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False)

    #seek(0) rewinds the buffer back to the start — like rewinding a tape. After writing, 
    # the "read head" is at the end. If you returned it without rewinding, Flask would send an empty file. 
    # After seek(0) it's ready to be read from the beginning and sent to the browser as a download.
    buffer.seek(0)
    return buffer