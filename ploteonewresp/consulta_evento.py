#!/usr/bin/env python3
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Version  SeisComp6
def consultar_por_fecha_creacion(id_origen):
    connection_params = {
        "host": "10.54.217.69",
        "database": "seiscomp",
        "user": "sysop",
        "password": "sysop"
    }

    # === LIMPIEZA PREVENTIVA ===
    # Borramos inmediatamente cualquier residuo anterior para evitar ploteos fantasmas
    ruta_tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evento_data.txt")
    if os.path.exists(ruta_tmp):
        try:
            os.remove(ruta_tmp)
        except OSError:
            pass

    try:
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1) Intento directo: el ID es el publicID de un ORIGEN.
        #    Se enlaza con su evento vía m_preferredoriginid (sin depender de
        #    heurísticas de tiempo, que descartaban eventos válidos).
        sql_por_origen = """
        SELECT 
            TRIM(po_e.m_publicid::text) AS id_evento, o.m_time_value AS ot_utc,
            ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
            o.m_quality_usedphasecount AS fases, ROUND(o.m_quality_standarderror::numeric, 2) AS rms,
            ROUND(o.m_quality_azimuthalgap::numeric, 0) AS azgap, o.m_latitude_value AS latitud, 
            o.m_longitude_value AS longitud, ROUND(o.m_depth_value::numeric, 1) AS profundidad_km, 
            o.m_creationinfo_agencyid AS agencia, o.m_creationinfo_author AS operador, ed.m_text AS region,
            o.m_evaluationstatus AS estatus
        FROM origin o
        INNER JOIN publicobject po_o ON o._oid = po_o._oid
        LEFT JOIN event e ON TRIM(e.m_preferredoriginid::text) = TRIM(po_o.m_publicid::text)
        LEFT JOIN publicobject po_e ON e._oid = po_e._oid
        LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
        LEFT JOIN magnitude m ON po_m._oid = m._oid
        LEFT JOIN eventdescription ed ON ed._parent_oid = e._oid AND ed.m_type = 'region name'
        WHERE TRIM(po_o.m_publicid::text) = TRIM(%s::text);
        """
        cursor.execute(sql_por_origen, (id_origen,))
        origen = cursor.fetchone()

        ev = None

        if origen is not None:
            # El origen existe: se valida si es la solución preferida actual
            if origen['id_evento']:
                ev = origen
            else:
                print(f"\n[X] ATENCIÓN: El origen {id_origen} NO es la solución preferida actual de su evento.")
                print("[!] Confirma (Confirm/Commit) el origen en SeisComP antes de volver a presionar NewPT.")
                cursor.close()
                conn.close()
                return

        # 2) Fallback: el ID es el publicID de un EVENTO (usamos su origen preferido)
        if not ev:
            sql_por_evento = """
            SELECT 
                TRIM(po_e.m_publicid::text) AS id_evento, o.m_time_value AS ot_utc,
                ROUND(m.m_magnitude_value::numeric, 1) AS magnitud, m.m_type AS tipo_magnitud,
                o.m_quality_usedphasecount AS fases, ROUND(o.m_quality_standarderror::numeric, 2) AS rms,
                ROUND(o.m_quality_azimuthalgap::numeric, 0) AS azgap, o.m_latitude_value AS latitud, 
                o.m_longitude_value AS longitud, ROUND(o.m_depth_value::numeric, 1) AS profundidad_km, 
                o.m_creationinfo_agencyid AS agencia, o.m_creationinfo_author AS operador, ed.m_text AS region,
                o.m_evaluationstatus AS estatus
            FROM event e
            INNER JOIN publicobject po_e ON e._oid = po_e._oid
            LEFT JOIN publicobject po_o ON po_o.m_publicid = e.m_preferredoriginid
            LEFT JOIN origin o ON o._oid = po_o._oid
            LEFT JOIN publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
            LEFT JOIN magnitude m ON po_m._oid = m._oid
            LEFT JOIN eventdescription ed ON ed._parent_oid = e._oid AND ed.m_type = 'region name'
            WHERE TRIM(po_e.m_publicid::text) = TRIM(%s::text)
            LIMIT 1;
            """
            cursor.execute(sql_por_evento, (id_origen,))
            ev = cursor.fetchone()

        # CONTROL ESTRICTO: Si no hay fila, el ID no existe como origen ni evento
        if not ev or not ev['id_evento']:
            print(f"\n[X] ATENCIÓN: No se encontró ningún origen ni evento con el ID {id_origen}.")
            cursor.close()
            conn.close()
            return

        # --- FORMATEO ADAPTATIVO DE MAGNITUD ---
        # Si la magnitud no se ha calculado (es None), asignamos un string vacío o '0.0'
        # El script capturar.py interpretará esto automáticamente como "M s/d" en el título del gráfico
        mag_final = ev['magnitud'] if ev['magnitud'] is not None else ""
        tipo_mag_final = ev['tipo_magnitud'] if ev['tipo_magnitud'] is not None else "M"

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

        print(f"[OK] Archivo temporal generado.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[X] Error en el procesamiento del evento: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    consultar_por_fecha_creacion(sys.argv[1])