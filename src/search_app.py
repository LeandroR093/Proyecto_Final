with open(r"c:\Users\Farmatodo Kike\Documents\4Geeks Data science\Proyecto_Final\src\app.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "open" in line or "diccionario" in line:
            print(f"{i}: {line.strip()}")
