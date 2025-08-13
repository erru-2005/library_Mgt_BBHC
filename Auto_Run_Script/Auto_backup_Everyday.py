import pandas as pd
import os
import glob
 # Your MongoDB connection
from openpyxl import load_workbook
from datetime import datetime
from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['library_db']
    print("Connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
# --- MongoDB Collection ---
issued_books = db['issued_books']

# --- Backup Folder ---
backup_folder = r"D:/Library_Issued_Backup"
os.makedirs(backup_folder, exist_ok=True)  # Create folder if missing

# --- Max backups to keep ---
MAX_BACKUPS = 5


def get_next_backup_filename():
    print("get_next_backup_filename READED")
    """
    Get next backup file name based on existing backups.
    Files are named: issued_books_backup1.xlsx, backup2.xlsx, etc.
    """
    existing_files = sorted(
        glob.glob(os.path.join(backup_folder, "issued_books_backup*.xlsx")),
        key=os.path.getmtime
    )

    # If we have more than MAX_BACKUPS - 1, delete oldest
    while len(existing_files) >= MAX_BACKUPS:
        oldest_file = existing_files.pop(0)
        try:
            os.remove(oldest_file)
            print(f"Deleted old backup: {oldest_file}")
        except Exception as e:
            print(f"Error deleting {oldest_file}: {e}")

    # Determine the next backup number
    all_numbers = []
    for file in existing_files:
        try:
            num = int(os.path.splitext(os.path.basename(file))[0].replace("issued_books_backup", ""))
            all_numbers.append(num)
        except ValueError:
            pass

    next_num = max(all_numbers, default=0) + 1
    return os.path.join(backup_folder, f"issued_books_backup{next_num}.xlsx")


def export_issued_books_to_excel():
    try:
        # Fetch all documents except _id
        try:
            data = list(issued_books.find({}, {"_id": 0}))
        except Exception as e:
            print(f"[MongoDB ERROR] Could not fetch issued_books: {e}")
            return

        if not data:
            print("No data found in issued_books collection.")
            return

        # Flatten nested fields for cleaner Excel columns
        flattened_data = []
        for doc in data:
            flattened_data.append({
                "Roll No": doc.get("student", {}).get("rollno", ""),
                "Section": doc.get("student", {}).get("section", ""),
                "Student Name": doc.get("student", {}).get("studentName", ""),
                "Accession No": doc.get("book", {}).get("accession_number", ""),
                "Author": doc.get("book", {}).get("author", ""),
                "Barcode": doc.get("book", {}).get("barcode", ""),
                "Department": doc.get("book", {}).get("department", ""),
                "Dept Code": doc.get("book", {}).get("department_code", ""),
                "Book ID": doc.get("book", {}).get("id", ""),
                "Title": doc.get("book", {}).get("title", ""),
                "Status": doc.get("status", ""),
                "Issued At": doc.get("issued_at", ""),
                "Returned At": doc.get("returned_at", "")
            })

        excel_file_path = get_next_backup_filename()

        try:
            # Convert to DataFrame and save to Excel
            df = pd.DataFrame(flattened_data)
            df.to_excel(excel_file_path, index=False)
        except Exception as e:
            print(f"[Pandas/Excel ERROR] Could not write Excel file: {e}")
            return

        try:
            # Format Excel with column width adjustment
            wb = load_workbook(excel_file_path)
            ws = wb.active

            for col in ws.columns:
                max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

            wb.save(excel_file_path)
        except Exception as e:
            print(f"[Excel Formatting ERROR] Could not format Excel file: {e}")
            return

        print(f"Issued books data exported to {excel_file_path}")

    except Exception as e:
        print(f"[GENERAL ERROR] An unexpected error occurred: {e}")
export_issued_books_to_excel()