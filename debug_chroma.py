
try:
    import chromadb
    print(f"ChromaDB imported successfully: {chromadb.__version__}")
except Exception as e:
    print(f"Error importing chromadb: {e}")
    import traceback
    traceback.print_exc()

try:
    import sqlite3
    print(f"Sqlite3 version: {sqlite3.sqlite_version}")
except Exception as e:
    print(f"Error importing sqlite3: {e}")
