import sqlite3

db_path = r"c:\Users\Farmatodo Kike\Documents\4Geeks Data science\Proyecto_Final\src\sp500_market_data.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tablas encontradas: {tables}")
    
    for table in tables:
        t_name = table[0]
        print(f"\n--- Tabla: {t_name} ---")
        cursor.execute(f"PRAGMA table_info({t_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f" Columna: {col[1]} ({col[2]})")
            
        # Sample row
        cursor.execute(f"SELECT * FROM {t_name} LIMIT 1;")
        row = cursor.fetchone()
        print(f" Muestra: {row}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
