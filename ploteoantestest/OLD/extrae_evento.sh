#!/bin/bash
# Usamos scbulletin, que lee el evento activo sin necesitar consultas SQL complejas
INPUT_ID="$2"
TEMP_FILE="$(dirname "$(readlink -f "$0")")/evento_data.txt"

# scbulletin toma el ID y genera el formato de reporte. 
# Si el ID que envía scolv falla, intentamos extraer solo la parte numérica del ID.
CLEAN_ID=$(echo "$INPUT_ID" | sed 's/Origin\///')

# Ejecutamos scbulletin. Si falla, el archivo quedará vacío, pero vamos a forzar una salida.
/home/hriquelmez/seiscomp/bin/scbulletin -d postgresql://sysop:sysop@10.54.217.69/seiscomp -E "$CLEAN_ID" > /tmp/bulletin_raw.txt 2>/dev/null

# Intentamos extraer la última línea válida del reporte
# y la guardamos en el formato que capturar.py necesita
grep -v "BEGIN" /tmp/bulletin_raw.txt | grep -v "END" | tail -n 1 > "$TEMP_FILE"

# Si el archivo está vacío (falló), imprimimos un error útil
if [ ! -s "$TEMP_FILE" ]; then
    echo "ERROR: scbulletin no pudo extraer datos para $CLEAN_ID. Revisa si el ID es correcto."
    exit 1
fi

# Lanzamos capturar.py
/usr/bin/python3 "/home/hriquelmez/Desarrollo/mapasopa/ploteo/capturar.py"