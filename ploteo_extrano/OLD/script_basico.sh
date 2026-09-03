#!/bin/bash
# script_basico.sh

#script de consulta a la base de datos de SeisComp
#1. Datos que estás extrayendo (Estructura)
#Tu script actual genera un reporte de texto plano con los siguientes bloques de datos:
#Identificador y Metadata: ID del evento (csn_sc62026njozr) y número de estaciones utilizadas (50).
#Modelo de Tierra: Especifica el modelo (N18-26_4k), vital si en tu otro proyecto necesitas comparar la calidad de la relocalización.
#Parámetros Hipocentrales:
#Magnitud: MLv=3.1 (Magnitud local vectorial).
#Fecha/Hora: 2026/07/10 04:46:53.7 (Fecha origen UTC).
#Coordenadas: 20.24 S, 69.22 W.
#Profundidad: 105 km.
#Análisis de Estaciones (El "Raw Data"):
#Listado de cada estación: PB08, T07A, etc.
#Red (CX, C1).
#Tiempos de arribo (fase P y S).
#Residuos (Res): Esto es oro puro para investigación. Te dice cuánto se desvió la lectura real de la estación respecto al modelo teórico.
#Magnitudes por estación (ML): Permite ver la dispersión de la energía en diferentes azimuts.

# Ruta fija del ejecutable que encontramos
SC_BIN="/home/hriquelmez/seiscomp/bin/scbulletin"
DB_URL="postgresql://sysop:sysop@10.54.217.69/seiscomp"

# Capturamos el ID
EVENT_ID="$2"

# Depuración: Si el ID está vacío, es el problema principal
if [ -z "$EVENT_ID" ]; then
    echo "ERROR CRÍTICO: No se recibió ningún ID de evento."
    echo "El script recibió: '$2'"
    echo "Uso correcto: ./script_basico.sh [param1] [event_id]"
    read -p "Presiona Enter para salir..."
    exit 1
fi

gnome-terminal -- bash -c "
    echo 'Intentando extraer el evento: $EVENT_ID'
    $SC_BIN -d $DB_URL -E '$EVENT_ID'
    if [ \$? -ne 0 ]; then
        echo '--------------------------------------------------'
        echo 'ERROR: scbulletin falló. Revisa la conexión o el ID.'
    fi
    read -p 'Presiona Enter para cerrar...'
"