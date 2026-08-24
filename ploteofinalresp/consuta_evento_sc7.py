#!/usr/bin/env python3
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Version  SeisComp7
def consultar_por_fecha_creacion(id_origen):
    connection_params = {
        "host": "10.54.217.69",
        "database": "seiscomp",
        "user": "sysop",
        "password": "sysop"
    }

    # === LIMPIEZA PREVENTIVA ===
    ruta_tmp = "/home/sysop/ploteo/evento_data.txt"
    if os.path.exists(ruta_tmp):
        try:
            os.remove(ruta_tmp)
        except OSError:
            pass

    fecha_creacion = None

    # Extractor de estampa de tiempo para formatos (Origin/ y NLL.)
    try:
        if "Origin/" in id_origen:
            timestamp_str = id_origen.split('/')[-1].split('.')[0]
        elif "NLL." in id_origen:
            timestamp_str = id_origen.split('.')[1]
        else:
            timestamp_str = None

        if timestamp_str:
            timestamp_str = timestamp_str[:14]
            dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
            fecha_creacion = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"[X] Error analizando el formato del ID ({id_origen}): {e}")
        return

    # QUERIES BLINDADOS PARA SEISCOMP 7 (Usando TRIM y casteo explícito ::text)
    if not fecha_creacion:
        sql_query = """
        SELECT 
            TRIM(po_e.m_publicid::text) AS id_evento, o.m_time_value AS ot_utc,
            ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
            o.m_quality_usedphasecount AS fases, ROUND(o.m_quality_standarderror::numeric, 2) AS rms,
            ROUND(o.m_quality_azimuthalgap::numeric, 0) AS azgap, o.m_latitude_value AS latitud, 
            o.m_longitude_value AS longitud, ROUND(o.m_depth_value::numeric, 1) AS profundidad_km, 
            o.m_creationinfo_agencyid AS agencia, o.m_creationinfo_author AS operador, 
            c.m_text AS region, o.m_evaluationstatus AS estatus
        FROM origin o
        INNER JOIN publicobject po_o ON o._oid = po_o._oid
        LEFT JOIN event e ON TRIM(e.m_preferredoriginid::text) = TRIM(po_o.m_publicid::text)
        LEFT JOIN publicobject po_e ON e._oid = po_e._oid
        LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
        LEFT JOIN magnitude m ON po_m._oid = m._oid
        LEFT JOIN comment c ON c._parent_oid = e._oid AND (c.m_id = 'region' OR c.m_id = 'region name')
        WHERE TRIM(po_o.m_publicid::text) = TRIM(%s::text);
        """
        valores_query = (id_origen,)
    else:
        sql_query = """
        SELECT 
            TRIM(po_e.m_publicid::text) AS id_evento, o.m_time_value AS ot_utc,
            ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
            o.m_quality_usedphasecount AS fases, ROUND(o.m_quality_standarderror::numeric, 2) AS rms,
            ROUND(o.m_quality_azimuthalgap::numeric, 0) AS azgap, o.m_latitude_value AS latitud, 
            o.m_longitude_value AS longitud, ROUND(o.m_depth_value::numeric, 1) AS profundidad_km, 
            o.m_creationinfo_agencyid AS agencia, o.m_creationinfo_author AS operador, 
            c.m_text AS region, o.m_evaluationstatus AS estatus
        FROM origin o
        INNER JOIN publicobject po_o ON o._oid = po_o._oid
        LEFT JOIN event e ON TRIM(e.m_preferredoriginid::text) = TRIM(po_o.m_publicid::text)
        INNER JOIN publicobject po_e ON e._oid = po_e._oid
        LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
        LEFT JOIN magnitude m ON po_m._oid = m._oid
        LEFT JOIN comment c ON c._parent_oid = e._oid AND (c.m_id = 'region' OR c.m_id = 'region name')
        WHERE o.m_creationinfo_creationtime >= %s::timestamp - interval '3 second'
          AND o.m_creationinfo_creationtime <= %s::timestamp + interval '3 second'
        LIMIT 1;
        """
        valores_query = (fecha_creacion, fecha_creacion)

    try:
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql_query, valores_query)
        ev = cursor.fetchone()

        # Validación estricta de solución preferida
        if not ev or not ev['id_evento']:
            print(f"\n[X] ATENCIÓN: El ID {id_origen} no es una solución preferida en SeisComP 7.")
            cursor.close()
            conn.close()
            return

        # Formateo adaptativo para magnitudes no calculadas todavía
        mag_final = ev['magnitud'] if ev['magnitud'] is not None else ""
        tipo_mag_final = ev['tipo_magnitud'] if ev['tipo_magnitud'] is not None else "M"

        # Estandarización de coordenadas con sufijos cardinales absolutos requeridos por capturar.py
        fecha_formateada = ev['ot_utc'].strftime("%Y-%m-%d %H:%M:%S")
        
        lat_val = abs(float(ev['latitud']))
        lat_cardinal = f"{lat_val:.2f} S" if float(ev['latitud']) < 0 else f"{lat_val:.2f} N"
        
        lon_val = abs(float(ev['longitud']))
        lon_cardinal = f"{lon_val:.2f} W" if float(ev['longitud']) < 0 else f"{lon_val:.2f} E"
        
        profundidad = f"{int(ev['profundidad_km'])} km"
        status_eval = ev['estatus'] if ev['estatus'] else "confirmed"
        region_name = ev['region'] if ev['region'] else "Unknown Region"

        # Construcción exacta de la hilera compatible con el flujo existente
        linea_salida = (
            f"{fecha_formateada};;;"
            f"{mag_final};"
            f"{tipo_mag_final};"
            f"{ev['fases']};"
            f"{ev['rms']};"
            f"{ev['azgap']};"
            f"{lat_cardinal};"
            f"{lon_cardinal};"
            f"{profundidad};"
            f"from location;"
            f"{status_eval};;"
            f"2;"
            f"{ev['agencia']};"
            f"{ev['operador']};"
            f"{region_name};"
            f"{ev['id_evento']}"
        )
        
        with open(ruta_tmp, "w", encoding="utf-8") as f:
            f.write(linea_salida + "\n")
        
        print(f"[OK] Archivo temporal estandarizado para SeisComP 7 generado.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[X] Error en el procesamiento del evento en SeisComP 7: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    consultar_por_fecha_creacion(sys.argv[1])