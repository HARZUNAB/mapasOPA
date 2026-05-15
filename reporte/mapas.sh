#!/bin/bash

DIR_LOGICA="/home/sysop/scriptmapas"
DIR_TRABAJO="/home/sysop/imagenturno"

CSV_INPUT="$1"
SUB_CARPETA="$2"
CARPETA_IMG="${DIR_TRABAJO}/figuras_turno/${SUB_CARPETA}"
DAT_OUTPUT="${DIR_TRABAJO}/${CSV_INPUT%.*}_tmp.dat"

# Activa el entorno
if [ -f "${DIR_TRABAJO}/.venv/bin/activate" ]; then
    source "${DIR_TRABAJO}/.venv/bin/activate"
fi

mkdir -p "$CARPETA_IMG"
cd "$DIR_TRABAJO"

echo "--- Iniciando procesamiento ---"
export PYTHONPATH=$PYTHONPATH:$DIR_LOGICA

# Ejecución de Python
python3 "$DIR_LOGICA/proc_query.py" "$CSV_INPUT" "$DAT_OUTPUT"
python3 "$DIR_LOGICA/perfilesOPA.py" "$CSV_INPUT" "$DAT_OUTPUT" "$CARPETA_IMG"

#echo "--- Organizando archivos técnicos ---"
# Copia el CSV y mueve el DAT a su destino final (la carpeta de imágenes)
[ -f "$CSV_INPUT" ] && cp "$CSV_INPUT" "$CARPETA_IMG/datos.csv"
[ -f "$DAT_OUTPUT" ] && mv "$DAT_OUTPUT" "$CARPETA_IMG/catalogo.dat"

# LIMPIEZA FINAL
# =======================================================
#echo "--- Limpiando archivos temporales de la raíz ---"

# Borra el CSV original de la raíz de trabajo
if [ -f "$CSV_INPUT" ]; then
    rm "$CSV_INPUT"
    #echo "  Eliminado de raíz: $CSV_INPUT"
fi
###
# Borra el archivo de variables temporales de la interfaz
#if [ -f "temp_vars.txt" ]; then
    #rm "temp_vars.txt"
    #echo "  Eliminado de raíz: temp_vars.txt"
#fi

#echo "✅ Proceso y limpieza completados en $SUB_CARPETA"
echo "✅ Proceso completado en $SUB_CARPETA"