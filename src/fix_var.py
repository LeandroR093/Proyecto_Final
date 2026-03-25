path = r"c:\Users\Farmatodo Kike\Documents\4Geeks Data science\Proyecto_Final\src\app.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

fixed_content = content.replace("empresa_seleccionada", "ticker")

with open(path, "w", encoding="utf-8") as f:
    f.write(fixed_content)

print("Replaced successfully")
