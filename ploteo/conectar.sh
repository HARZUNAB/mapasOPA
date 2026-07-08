#!/bin/bash

#USUARIO="sysop"
#IP_SERVIDOR="10.54.217.146"
#DIR_PROYECTO="/home/sysop/imagenturno"

# EJECUCIÓN REMOTA
#ssh -C -t "${USUARIO}@${IP_SERVIDOR}" "
#    DIR_LOGICA='/home/sysop/scriptmapas'
#    DIR_TRABAJO='/home/sysop/imagenturno'
#    
#    export PYTHONPATH=\$PYTHONPATH:\$DIR_LOGICA
#    export EVENTQUERY_SETTINGS='/home/sysop/.eventselect.ini'
#    
#    cd \$DIR_TRABAJO || exit 1
#    [ -f './.venv/bin/activate' ] && source './.venv/bin/activate'
#
#    python3 \$DIR_LOGICA/interfaz_query.py | tee ./temp_vars.txt
#    
#    if [ -f './temp_vars.txt' ]; then
#        CSV_GEN=\$(grep 'RESULT_FILE=' ./temp_vars.txt | tail -n 1 | cut -d'=' -f2 | tr -d '\\r')
#        CARPETA_REMOTA=\$(grep 'DIR_NAME=' ./temp_vars.txt | tail -n 1 | cut -d'=' -f2 | tr -d '\\r')
#        
#        if [ ! -z \"\$CSV_GEN\" ]; then
#            \$DIR_LOGICA/mapas.sh \"\$CSV_GEN\" \"\$CARPETA_REMOTA\"
#        fi
#    fi
#"

USUARIO="sysop"
IP_SERVIDOR="10.54.217.146"
DIR_PROYECTO="/home/sysop/imagenturno"

# EJECUCIÓN REMOTA
ssh -C -t "${USUARIO}@${IP_SERVIDOR}" "
    DIR_LOGICA='/home/sysop/scriptmapas'
    DIR_TRABAJO='/home/sysop/imagenturno'
    
    export PYTHONPATH=\$PYTHONPATH:\$DIR_LOGICA
    export EVENTQUERY_SETTINGS='/home/sysop/.eventselect.ini'
    
    cd \$DIR_TRABAJO || exit 1
    [ -f './.venv/bin/activate' ] && source './.venv/bin/activate'

    python3 \$DIR_LOGICA/interfaz_query.py | tee ./temp_vars.txt
    
    if [ -f './temp_vars.txt' ]; then
        CSV_GEN=\$(grep 'RESULT_FILE=' ./temp_vars.txt | tail -n 1 | cut -d'=' -f2 | tr -d '\\r')
        CARPETA_REMOTA=\$(grep 'DIR_NAME=' ./temp_vars.txt | tail -n 1 | cut -d'=' -f2 | tr -d '\\r')
        
        if [ ! -z \"\$CSV_GEN\" ]; then
            \$DIR_LOGICA/mapas.sh \"\$CSV_GEN\" \"\$CARPETA_REMOTA\"
        fi
    fi
"


# CAPTURA DEL NOMBRE
sleep 2
NOMBRE_CARPETA=$(ssh "${USUARIO}@${IP_SERVIDOR}" "grep 'DIR_NAME=' ${DIR_PROYECTO}/temp_vars.txt | tail -n 1 | cut -d'=' -f2 | tr -d '\r'")

# DESCARGA LOCAL
if [ -z "$NOMBRE_CARPETA" ]; then
    NOMBRE_CARPETA=$(ssh "${USUARIO}@${IP_SERVIDOR}" "ls -td ${DIR_PROYECTO}/figuras_turno/*/ | head -n 1 | xargs basename")
fi

RUTA_LOCAL="$(pwd)/$NOMBRE_CARPETA"
scp -r "${USUARIO}@${IP_SERVIDOR}:${DIR_PROYECTO}/figuras_turno/${NOMBRE_CARPETA}" "./"

echo "======================================================="
echo "✅ DESCARGA LOCAL COMPLETADA"
echo "UBICACIÓN: $RUTA_LOCAL"
echo "======================================================="

# VISOR CON AYUDA INTEGRADA EN LA IMAGEN
if [ -d "./$NOMBRE_CARPETA" ]; then
    # Definimos el texto de ayuda
    AYUDA_TEXTO="Nav: Flechas | Zoom: +/- | Cerrar: Q"
    
    # Quitamos '-x' y agregamos '--title' para recuperar el movimiento con el mouse
    feh -g 1200x900 -B black --scale-down \
        --title "Visor de Perfiles Sísmicos" \
        --info "echo '$AYUDA_TEXTO'" \
        "./$NOMBRE_CARPETA"/*.png &
fi

## VISOR CON AYUDA INTEGRADA EN LA IMAGEN
#if [ -d "./$NOMBRE_CARPETA" ]; then
#    # Definimos el texto de ayuda
#    AYUDA_TEXTO="Nav: Flechas | Zoom: +/- | Cerrar: Q"
    
#    # Lanzamos feh con la opción --info para dibujar el texto sobre la imagen
#    feh -g 1200x900 -B black --scale-down \
#        --info "echo '$AYUDA_TEXTO'" \
#        -x "./$NOMBRE_CARPETA"/*.png &
#fi
