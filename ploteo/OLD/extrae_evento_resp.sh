#!/bin/bash
SC_BIN="/home/hriquelmez/seiscomp/bin/scbulletin"
DB_URL="postgresql://sysop:sysop@10.54.217.69/seiscomp"
EVENT_ID="$2"
TEMP_FILE="$(dirname "$(readlink -f "$0")")/evento_data.txt"
#TEMP_FILE="/tmp/evento_data.txt"

if [ -z "$EVENT_ID" ]; then
    echo "Uso: $0 [param] [event_id]"
    exit 1
fi

# Ejecutamos scbulletin y procesamos con awk ignorando espacios múltiples
$SC_BIN -d $DB_URL -E "$EVENT_ID" | grep "MLv=" | awk -v eid="$EVENT_ID" '
{
    # Encontrar la posición de "MLv="
    for (i=1; i<=NF; i++) {
        if ($i ~ /MLv=/) {
            split($i, m, "="); mag = m[2];
            fecha = $(i+1);
            hora = $(i+2);
            lat = $(i+3) " " $(i+4);
            lon = $(i+5) " " $(i+6);
            prof = $(i+7) " km";
            break;
        }
    }
    # Reemplazar / por - en la fecha
    gsub(/\//, "-", fecha);
    
    # Imprimir formato
    printf "%s %s;;;%s;MLv;53;0.3;188;%s;%s;%s;-;C;;7;CSN;yole;Chile-Argentina Border Region;%s\n", 
           fecha, hora, mag, lat, lon, prof, eid
}' > "$TEMP_FILE"

cat "$TEMP_FILE"