#!/bin/bash
EVENT_ID=$1
DIR_TRABAJO="/home/hriquelmez/Desarrollo/mapasopa/ploteo"

# =========================================================================
# LIMPIEZA AUTOMÁTICA DE EVENTOS ANTERIORES
# =========================================================================
# 1. Cerramos cualquier ventana gráfica de matplotlib abierta por el script previo
pkill -f "python3 $DIR_TRABAJO/capturar.py" 2>/dev/null

# 2. Cerramos cualquier terminal xterm temporal previa de NewPT que haya quedado colgada
pkill -f "xterm.*Procesamiento de Evento - NewPT" 2>/dev/null

# Pequeña pausa para asegurar que el sistema libere los recursos antes de reabrir
sleep 0.2

# =========================================================================
# LEVANTAR NUEVO EVENTO
# =========================================================================
# Abrimos la nueva ventana xterm flotante. Al cerrarse el mapa, se cerrará sola.
xterm -geometry 90x25 -T "Procesamiento de Evento - NewPT" -e "bash -c '
    echo \"=== INICIANDO EXTRACCIÓN DE PARÁMETROS ===\";
    python3 \"$DIR_TRABAJO/consulta_evento.py\" \"$EVENT_ID\";
    
    if [ -f \"$DIR_TRABAJO/evento_data.txt\" ]; then
        echo \"\";
        echo \"=== GENERANDO MAPAS ===\";
        #echo \"Por favor, interactúa con el mapa. Al cerrarlo finalizará el proceso.\";
        python3 \"$DIR_TRABAJO/capturar.py\";
    else
        echo \"[X] Error: No se pudo generar el archivo de intercambio.\";
        sleep 5;
    fi
'" &