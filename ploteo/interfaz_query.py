import subprocess
import sys
import os
import re
from datetime import datetime

# CONFIGURACIÓN
EJECUTABLE_EVENTQUERY = "/home/sysop/bin/eventquery"

def solicitar(nombre, ejemplo, tipo_dato, obligatorio=False):
    while True:
        prompt = f"🔹 {nombre:<25} (Ej: {ejemplo})"
        prompt += "\t[OBLIGATORIO]: " if obligatorio else "\t[ENTER para omitir]: "
        
        entrada = input(prompt).strip()

        if not entrada:
            if obligatorio:
                print(f"   Error: El campo '{nombre}' no puede estar vacío.")
                continue
            return None
        
        # VALIDACIONES
        if tipo_dato == "tiempo_corto":
            # Validamos que sean exactamente 14 dígitos
            if re.match(r"^\d{14}$", entrada):
                try:
                    # Intentamos convertir para validar que el mes/día/hora sean reales
                    dt = datetime.strptime(entrada, "%Y%m%d%H%M%S")
                    # Retornamos el formato que necesita el comando: YYYY-MM-DDThh:mm:ss
                    return dt.strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    print("   Error: Fecha o hora inválida (ej. mes 13 o día 32).")
            else:
                print("   Error: Use el formato AAAAMMDDHHMMSS (14 dígitos).")
        
        elif tipo_dato == "numero":
            try:
                float(entrada)
                return entrada
            except ValueError:
                print("   Error: Ingrese un valor numérico válido.")
        
        elif tipo_dato == "csv":
            if entrada.lower().endswith(".csv"): return entrada
            print("   Error: Debe terminar en .csv")
            
        elif tipo_dato == "texto":
            return entrada

print("\n" + "="*70)
print("             INGRESO DE PARÁMETROS PARA EL CATÁLOGO")
print("="*70)

# PARÁMETROS TEMPORALES SIMPLIFICADOS
while True:
    print("Ingrese tiempo en formato: AAAAMMDDHHMMSS")
    start = solicitar("Start Time", "20260501000000", "tiempo_corto", obligatorio=True)
    end   = solicitar("End Time",   "20260507235959", "tiempo_corto", obligatorio=True)
    
    # Validar que Fin > Inicio
    # (Ya vienen convertidos a formato ISO desde solicitar)
    t_start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
    t_end   = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")
    
    if t_end > t_start:
        break
    else:
        print("\n ❌ ERROR LÓGICO: La fecha de FIN debe ser posterior a la de INICIO.")
        print("   Por favor, ingrese el rango de tiempo nuevamente.\n")

# OTROS OBLIGATORIOS
output = solicitar("Nombre archivo salida", "datos.csv", "csv", obligatorio=True)
directorio = solicitar("Nombre carpeta imágenes", "analista", "texto", obligatorio=True)

# OPCIONALES (Tabulados y compactos)
print("-" * 70)
min_lat = solicitar("Latitud Mínima", "-38.5", "numero")
max_lat = solicitar("Latitud Máxima", "-32.0", "numero")
min_lon = solicitar("Longitud Mínima", "-75.0", "numero")
max_lon = solicitar("Longitud Máxima", "-69.5", "numero")
min_dep = solicitar("Profundidad Mínima", "0", "numero")
max_dep = solicitar("Profundidad Máxima", "150", "numero")
min_mag = solicitar("Magnitud Mínima", "3.0", "numero")
max_mag = solicitar("Magnitud Máxima", "9.0", "numero")

# CONSTRUCCIÓN DEL COMANDO
comando = [EJECUTABLE_EVENTQUERY, "--start-time", start, "--end-time", end]

opcionales = [
    ("--min-latitude", min_lat), ("--max-latitude", max_lat),
    ("--min-longitude", min_lon), ("--max-longitude", max_lon),
    ("--min-depth", min_dep), ("--max-depth", max_dep),
    ("--min-magnitude", min_mag), ("--max-magnitude", max_mag)
]

for flag, valor in opcionales:
    if valor is not None:
        comando.extend([flag, valor])

comando.append(output)

print("\n" + "="*70)
print(f" EJECUTANDO: {' '.join(comando)}")
print("="*70 + "\n")

try:
    subprocess.run(comando, check=True)
    print(f"RESULT_FILE={output}")
    print(f"DIR_NAME={directorio}")
    print(f"\nConsulta finalizada con éxito.")
except Exception as e:
    print(f"\n Error: {e}")
    sys.exit(1)