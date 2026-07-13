#!/bin/bash
DIR="$(dirname "$(readlink -f "$0")")"

if [ "$1" == "--in-terminal" ]; then
    shift
    # Vamos a usar el ID pasado directamente. Si es un Origin, 
    # intentaremos extraer el ID de evento asociado de la forma más directa posible
    INPUT_ID="$1"
    
    # Intento final de resolución: Si es un Origin, extraemos la parte temporal 
    # y buscamos el evento csn_ asociado a esa fecha/hora.
    # Pero primero, intentamos pasar el ID directamente, ya que el problema
    # parece ser que tu script extrae_evento.sh no encuentra el ID.
    
    echo "Procesando ID: $INPUT_ID"
    "$DIR/extrae_evento.sh" param "$INPUT_ID"
    
    # Verificamos si el archivo NO está vacío (tamaño > 0)
    if [ -s "$DIR/evento_data.txt" ]; then
        echo "Archivo generado. Lanzando capturar.py..."
        /usr/bin/python3 "$DIR/capturar.py"
    else
        echo "[ERROR] evento_data.txt está vacío."
    fi

    # Solo ponemos el read aquí al final de todo, para que siempre veas qué pasó
    read -p "Proceso finalizado. Presiona Enter para cerrar..."
    
else
    x-terminal-emulator -e bash -c "$0 --in-terminal '$1'"
fi