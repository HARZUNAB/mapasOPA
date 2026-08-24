#!/bin/bash
# =============================================================================
# newpt.sh - Lanzador de producción NewPT (generado por instalar_newpt.sh)
# Independiente de la ubicación: funciona en cualquier carpeta sin permisos root.
# Uso: newpt.sh <ID_del_evento>   (ejemplo: newpt.sh csn_sc62026nkkbb;
#       escriba el ID real sin los signos < >)
# =============================================================================

EVENT_ID=$1
DIR_TRABAJO="$(dirname "$(readlink -f "$0")")"
export NEWPT_DATA_DIR="$DIR_TRABAJO"

# Cargar configuración de base de datos si existe (.env generado por el instalador)
if [ -f "$DIR_TRABAJO/.env" ]; then
    set -a
    source "$DIR_TRABAJO/.env"
    set +a
fi

BIN_CAPTURAR="$DIR_TRABAJO/bin/newpt_capturar/newpt_capturar"
BIN_CONSULTA="$DIR_TRABAJO/bin/newpt_consulta/newpt_consulta"

# =========================================================================
# LIMPIEZA AUTOMÁTICA DE EVENTOS ANTERIORES
# =========================================================================
# 1. Cerramos cualquier ventana gráfica abierta por una ejecución previa
pkill -f "$BIN_CAPTURAR" 2>/dev/null

# 2. Cerramos cualquier terminal xterm temporal previa de NewPT que haya quedado colgada
pkill -f "xterm.*Procesamiento de Evento - NewPT" 2>/dev/null

# Pequeña pausa para asegurar que el sistema libere los recursos antes de reabrir
sleep 0.2

# =========================================================================
# LEVANTAR NUEVO EVENTO (consulta -> generación de mapas)
# =========================================================================
xterm -geometry 90x25 -T "Procesamiento de Evento - NewPT" -e bash -c "
    echo '=== INICIANDO EXTRACCION DE PARAMETROS ===';
    '$BIN_CONSULTA' '$EVENT_ID';

    if [ -f '$DIR_TRABAJO/evento_data.txt' ]; then
        echo '';
        echo '=== GENERANDO MAPAS ===';
        '$BIN_CAPTURAR';
    else
        echo ''
        echo '============================================================'
        echo '[X] ERROR: No se encontraron datos validos para este ID.'
        echo '[!] NOTA: NewPT solo procesa soluciones PREFERIDAS.'
        echo '[!] Asegurate de confirmar -Confirm o Commit- el origen en'
        echo '    SeisComP antes de volver a presionar NewPT.'
        echo '============================================================'
        echo ''
        echo 'Presiona ENTER para cerrar esta ventana...'
        read
    fi
" &