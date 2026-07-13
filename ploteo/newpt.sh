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
# LEVANTAR NUEVO EVENTO (Sintaxis corregida sin conflicto de comillas)
# =========================================================================
# Abrimos la nueva ventana xterm flotante de forma segura
xterm -geometry 90x25 -T "Procesamiento de Evento - NewPT" -e bash -c "
    echo '=== INICIANDO EXTRACCION DE PARAMETROS ===';
    python3 '$DIR_TRABAJO/consulta_evento.py' '$EVENT_ID';
    
    if [ -f '$DIR_TRABAJO/evento_data.txt' ]; then
        echo '';
        echo '=== GENERANDO MAPAS ===';
        python3 '$DIR_TRABAJO/capturar.py';
    else
        echo ''
        echo '============================================================'
        echo '[X] ERROR: No se encontraron datos validos para este ID.'
        echo '[!] NOTA: NewPT solo procesa soluciones PREFERIDAS.'
        echo '[!] Asegurate de confirmar -Confirm o Commit- el origen en'
        echo '    SeisComP antes de volver a presionar NewPT.'
        echo '============================================================'
        echo ''
        echo 'Esta ventana se cerrara automaticamente en 8 segundos...'
        sleep 8
    fi
" &