#!/usr/bin/env python3
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def consultar_por_fecha_creacion(id_origen):
    connection_params = {
        "host": "10.54.217.69",
        "database": "seiscomp",
        "user": "sysop",
        "password": "sysop"
    }

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

    # Selección de Query SQL según el tipo de ID recibido
    if not fecha_creacion:
        sql_query = """
        SELECT 
            po_e.m_publicid AS id_evento, o.m_time_value AS ot_utc,
            ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
            o.m_quality_usedphasecount AS fases, ROUND(o.m_quality_standarderror::numeric, 2) AS rms,
            ROUND(o.m_quality_azimuthalgap::numeric, 0) AS azgap, o.m_latitude_value AS latitud, 
            o.m_longitude_value AS longitud, ROUND(o.m_depth_value::numeric, 1) AS profundidad_km, 
            o.m_creationinfo_agencyid AS agencia, o.m_creationinfo_author AS operador, ed.m_text AS region,
            o.m_evaluationstatus AS estatus
        FROM origin o
        INNER JOIN publicobject po_o ON o._oid = po_o._oid
        LEFT JOIN event e ON e.m_preferredoriginid = po_o.m_publicid
        LEFT JOIN publicobject po_e ON e._oid = po_e._oid
        LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
        LEFT JOIN magnitude m ON po_m._oid = m._oid
        LEFT JOIN eventdescription ed ON ed._parent_oid = e._oid AND ed.m_type = 'region name'
        WHERE po_o.m_publicid = %s;
        """
        valores_query = (id_origen,)
    else:
        sql_query = """
        SELECT 
            po_e.m_publicid AS id_evento, o.m_time_value AS ot_utc,
            ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
            o.m_quality_usedphasecount AS fases, ROUND(o.m_quality_standarderror::numeric, 2) AS rms,
            ROUND(o.m_quality_azimuthalgap::numeric, 0) AS azgap, o.m_latitude_value AS latitud, 
            o.m_longitude_value AS longitud, ROUND(o.m_depth_value::numeric, 1) AS profundidad_km, 
            o.m_creationinfo_agencyid AS agencia, o.m_creationinfo_author AS operador, ed.m_text AS region,
            o.m_evaluationstatus AS estatus
        FROM origin o
        INNER JOIN publicobject po_o ON o._oid = po_o._oid
        INNER JOIN event e ON e.m_preferredoriginid = po_o.m_publicid
        INNER JOIN publicobject po_e ON e._oid = po_e._oid
        LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
        LEFT JOIN magnitude m ON po_m._oid = m._oid
        LEFT JOIN eventdescription ed ON ed._parent_oid = e._oid AND ed.m_type = 'region name'
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

        if not ev:
            print(f"[X] No se encontraron datos para el ID: {id_origen}")
            return

        # --- FORMATEO ESTRICTO REQUERIDO POR CAPTURAR.PY ---
        fecha_formateada = ev['ot_utc'].strftime("%Y-%m-%d %H:%M:%S")
        
        # Formatear latitud y longitud con sufijos cardinales absolutos
        lat_val = abs(float(ev['latitud']))
        lat_cardinal = f"{lat_val:.2f} S" if float(ev['latitud']) < 0 else f"{lat_val:.2f} N"
        
        lon_val = abs(float(ev['longitud']))
        lon_cardinal = f"{lon_val:.2f} W" if float(ev['longitud']) < 0 else f"{lon_val:.2f} E"
        
        profundidad = f"{int(ev['profundidad_km'])} km"
        status_eval = ev['estatus'] if ev['estatus'] else "confirmed"
        region_name = ev['region'] if ev['region'] else "Unknown Region"

        # Construcción de la hilera con el orden exacto de 19 campos
        linea_salida = (
            f"{fecha_formateada};;;"
            f"{ev['magnitud']};"
            f"{ev['tipo_magnitud']};"
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

        """
        # 1. Despliegue en consola estándar
        print("\n==================================================")
        print("         EVENTO PROCESADO EN CONSOLA             ")
        print("==================================================")
        print(linea_salida)
        print("==================================================\n")
        """
        
        # 2. Generación del archivo temporal para capturar.py con ruta absoluta estricta
        ruta_tmp = "/home/hriquelmez/Desarrollo/mapasopa/ploteo/evento_data.txt"
        
        with open(ruta_tmp, "w", encoding="utf-8") as f:
            f.write(linea_salida + "\n")
        
        print(f"[OK] Archivo temporal generado.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[X] Error en el procesamiento del evento: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    consultar_por_fecha_creacion(sys.argv[1])