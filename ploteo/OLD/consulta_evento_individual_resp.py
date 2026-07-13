#!/usr/bin/env python3
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def consultar_por_fecha_creacion(id_origen):
    # Parámetros de tu base de datos
    connection_params = {
        "host": "10.54.217.69",
        "database": "seiscomp",
        "user": "sysop",
        "password": "sysop"
    }

    fecha_creacion = None

    # Extractor inteligente de estampa de tiempo para ambos formatos (Origin/ y NLL.)
    try:
        if "Origin/" in id_origen:
            # Formato: Origin/20260713160336.134757
            timestamp_str = id_origen.split('/')[-1].split('.')[0]
        elif "NLL." in id_origen:
            # Formato: NLL.20260713125943.908452
            timestamp_str = id_origen.split('.')[1]
        else:
            # Por si acaso llega un ID limpio de base de datos directamente
            timestamp_str = None

        if timestamp_str:
            # Tomamos los primeros 14 caracteres obligatorios (AAAAMMDDHHMMSS)
            timestamp_str = timestamp_str[:14]
            dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
            fecha_creacion = dt.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        print(f"[X] Error analizando el formato del ID ({id_origen}): {e}")
        return

    # Si no es un ID temporal y es un ID válido en Base de Datos (ej: csn_sc...)
    if not fecha_creacion:
        sql_query = """
        SELECT 
            po_e.m_publicid AS id_evento, o.m_time_value AS ot_utc,
            ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
            o.m_latitude_value AS latitud, o.m_longitude_value AS longitud,
            o.m_depth_value AS profundidad_km, o.m_creationinfo_author AS operador
        FROM origin o
        INNER JOIN publicobject po_o ON o._oid = po_o._oid
        LEFT JOIN event e ON e.m_preferredoriginid = po_o.m_publicid
        LEFT JOIN publicobject po_e ON e._oid = po_e._oid
        LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
        LEFT JOIN magnitude m ON po_m._oid = m._oid
        WHERE po_o.m_publicid = %s;
        """
        valores_query = (id_origen,)
    else:
        # Si es temporal (Origin/ o NLL.), buscamos por la ventana de tiempo de creación
        sql_query = """
        SELECT 
            po_e.m_publicid AS id_evento, o.m_time_value AS ot_utc,
            ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
            o.m_latitude_value AS latitud, o.m_longitude_value AS longitud,
            o.m_depth_value AS profundidad_km, o.m_creationinfo_author AS operador
        FROM origin o
        INNER JOIN publicobject po_o ON o._oid = po_o._oid
        INNER JOIN event e ON e.m_preferredoriginid = po_o.m_publicid
        INNER JOIN publicobject po_e ON e._oid = po_e._oid
        LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
        LEFT JOIN magnitude m ON po_m._oid = m._oid
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
            print(f"[X] No se encontraron datos en el motor sismológico para el ID: {id_origen}")
            return

        print("\n==================================================")
        print(f"         EVENTO IDENTIFICADO (NewPT)             ")
        print("==================================================")
        print(f"ID Evento:       {ev['id_evento']}")
        print(f"Fecha/Hora UTC:  {ev['ot_utc']}")
        print(f"Coordenadas:     Lat: {ev['latitud']} | Lon: {ev['longitud']}")
        print(f"Profundidad:     {ev['profundidad_km']} km")
        print(f"Magnitud:        {ev['magnitud']} ({ev['tipo_magnitud']})")
        print(f"Operador:        {ev['operador']}")
        print("==================================================\n")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[X] Error en la consulta dinámica de base de datos: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    id_recibido = sys.argv[1]
    
    # Volvemos a activar la consulta inversa
    consultar_por_fecha_creacion(id_recibido)