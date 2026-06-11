#!/bin/bash

#$1 = sept_2024.csv (archvo csv del eventquery)
#$2 = sept_2024.dat (nombre de archivo .dat creado al ejecutar proc_query.py en base al csv anterior)
#$3 = 202409 (fecha si se quisiera imprimir en los titulos de los mapas)
#$4 = 1 (número de gráficos de distribución)

proc_query.py $1 $2 $3 $4
#python3 proc_query_v2.py $1 $2 $3 $4
mapas_planta.py $1 $2 $3 $4
perfiles.py $1 $2 $3 $4
evolucion_magnitud.py $1 $2 $3 $4

echo "Proceso finalizado"
