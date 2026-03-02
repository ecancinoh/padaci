import os, django, csv
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "padaci.settings")
django.setup()
from clients.models import Cliente

CSV_PATH = r"C:\Users\Emanuel Cancino\OneDrive\1.PADACI SpA\La Canasta\Rutas.csv"
creados = 0
errores = 0

with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        try:
            Cliente.objects.create(
                nombre=row["Nombre del Cliente"].strip(),
                comuna=row["Comuna"].strip(),
                latitud=float(row["Latitud"].strip()),
                longitud=float(row["Longitud"].strip()),
            )
            creados += 1
        except Exception as e:
            print("Error:", list(row.values())[0], "->", e)
            errores += 1

print("Creados:    ", creados)
print("Errores:    ", errores)
print("Total en BD:", Cliente.objects.count())
