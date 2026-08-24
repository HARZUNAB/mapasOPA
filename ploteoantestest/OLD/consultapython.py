#!/usr/bin/env python3
import csv
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


def extraer_catalogo_csv(fecha_inicio, fecha_fin, archivo_salida):
    # Parámetros de conexión verificados
    connection_params = {
        "host": "10.54.217.69",
        "database": "seiscomp",
        "user": "sysop",
        "password": "sysop"
    }

    # Consulta SQL modificada para buscar directamente por el ID de Origen enviado por scolv
    sql_query = """
    SELECT 
        po_e.m_publicid AS id_evento,
        o.m_time_value AS ot_utc,
        ROUND(m.m_magnitude_value::numeric, 1) AS magnitud,
        m.m_type AS tipo_magnitud,
        o.m_quality_usedphasecount AS fases,
        ROUND(o.m_quality_standarderror::numeric, 2) AS rms,
        ROUND(o.m_quality_azimuthalgap::numeric, 0) AS azgap,
        ROUND(o.m_latitude_value::numeric, 4) AS latitud,
        ROUND(o.m_longitude_value::numeric, 4) AS longitud,
        ROUND(o.m_depth_value::numeric, 1) AS profundidad_km,
        o.m_creationinfo_agencyid AS agencia,
        o.m_creationinfo_author AS operador,
        ed.m_text AS region
    FROM 
        origin o
    -- Enlazamos el origen con su ID público (que es el que recibimos de scolv)
    INNER JOIN
        publicobject po_o ON o._oid = po_o._oid
    -- Buscamos el evento que tiene este origen como preferido (u origen asociado)
    LEFT JOIN
        event e ON e.m_preferredoriginid = po_o.m_publicid
    LEFT JOIN
        publicobject po_e ON e._oid = po_e._oid
    -- Buscamos la magnitud preferida de ese evento asociado
    LEFT JOIN
        publicobject po_m ON e.m_preferredmagnitudeid = po_m.m_publicid
    LEFT JOIN
        magnitude m ON po_m._oid = m._oid
    -- Descripción de la región
    LEFT JOIN 
        eventdescription ed ON ed._parent_oid = e._oid AND ed.m_type = 'region name'
    WHERE 
        po_o.m_publicid = %s;
    """

    try:
        print(f"\n[+] Conectando a la base de datos en 10.54.217.69...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(sql_query, (fecha_inicio, fecha_fin))
        eventos = cursor.fetchall()

        if not eventos:
            print("[-] No se encontraron eventos en ese rango de fechas.")
            cursor.close()
            conn.close()
            return

        print(f"[+] {len(eventos)} eventos encontrados. Generando archivo CSV...")

        cabeceras = eventos[0].keys()

        with open(archivo_salida, mode="w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=cabeceras)
            escritor.writeheader()
            escritor.writerows(eventos)

        print(f"[✓] Archivo CSV generado con éxito: '{archivo_salida}'")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[X] Ocurrió un error en la base de datos o escritura: {e}")


if __name__ == "__main__":
    print("=== Extractor de Catálogo de Eventos SeisComP (Filtro por Fechas) ===")
    
    f_inicio = input("Ingrese fecha de inicio (AAAA-MM-DD): ").strip()
    f_fin = input("Ingrese fecha de fin (AAAA-MM-DD): ").strip()

    try:
        datetime.strptime(f_inicio, "%Y-%m-%d")
        datetime.strptime(f_fin, "%Y-%m-%d")

        timestamp_inicio = f"{f_inicio} 00:00:00"
        timestamp_fin = f"{f_fin} 23:59:59"

        nombre_archivo = f"catalogo_{f_inicio}_al_{f_fin}.csv"
        
        extraer_catalogo_csv(timestamp_inicio, timestamp_fin, nombre_archivo)

    except ValueError:
        print("[X] Error: Las fechas deben tener estrictamente el formato AAAA-MM-DD.")