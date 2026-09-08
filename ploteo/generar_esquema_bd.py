#!/usr/bin/env python3
"""
Genera el esquema de la base de datos SeisComp6 (documentación de referencia).

Todo el acceso a la BD es SOLO LECTURA (catálogos de metadatos, readonly=True).
No se ejecuta consulta de datos ni se modifica nada en la BD.

Entregables en documentos/:
  - ESQUEMA_BD_SeisComp6.html  diagrama interactivo (SVG, zoom/pan con el ratón)
  - ESQUEMA_BD_SeisComp6.md    referencia completa (todas las columnas por tabla)
  - ESQUEMA_BD_SeisComp6.html.static.html  versión estática (para exportar a ODT)
"""

import os
import subprocess
import sys
from datetime import date

import psycopg2

DIR = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(DIR, "documentos")
os.makedirs(DOCS, exist_ok=True)

# ---------------------------------------------------------------------------
# Alcance: las tablas del subsistema sísmico + inventario, enfocadas en la
# solución preferida (event.m_preferredoriginid), que es lo que analiza un
# analista en NewPT. "originreference" va como contexto (el evento puede tener
# varios orígenes, pero se trabaja el preferido).
# ---------------------------------------------------------------------------
TABLAS = [
    # base
    "object", "publicobject",
    # núcleo sísmico
    "event", "origin", "magnitude", "eventdescription", "originreference",
    # cadena del origen preferido
    "arrival", "pick", "amplitude", "stationmagnitude",
    "stationmagnitudecontribution", "dataused", "reading",
    # inventario de estaciones
    "network", "station", "sensorlocation", "stream",
]

GRUPOS = [
    ("BASE",         ["object", "publicobject"]),
    ("NÚCLEO SÍSMICO", ["event", "origin", "magnitude", "eventdescription", "originreference"]),
    ("CADENA DEL ORIGEN PREFERIDO",
     ["arrival", "pick", "amplitude", "stationmagnitude",
      "stationmagnitudecontribution", "dataused", "reading"]),
    ("INVENTARIO DE ESTACIONES", ["network", "station", "sensorlocation", "stream"]),
]

# Columnas clave que se muestran en el diagrama (no sustituyen al Markdown,
# que trae TODAS las columnas). La flecha "->" indica hacia qué enlaza.
CLAVE = {
    "object":              ["_oid"],
    "publicobject":        ["_oid", "m_publicid  [único]"],
    "event":               ["_oid", "m_preferredoriginid ->", "m_preferredmagnitudeid ->",
                            "m_type"],
    "origin":              ["_oid", "m_time_value", "m_latitude_value",
                            "m_longitude_value", "m_depth_value", "m_evaluationstatus"],
    "magnitude":           ["_oid", "_parent_oid", "m_magnitude_value", "m_type", "m_originid"],
    "eventdescription":    ["_oid", "_parent_oid ->", "m_text", "m_type='region name'"],
    "originreference":     ["_oid", "_parent_oid ->", "m_originid ->"],
    "arrival":             ["_oid", "_parent_oid ->", "m_pickid ->", "m_phase_code",
                            "m_timeused", "m_weight"],
    "pick":                ["_oid", "m_time_value", "m_waveformid_* ->estación",
                            "m_phasehint_code", "m_onset", "m_polarity", "m_evaluationstatus"],
    "amplitude":           ["_oid", "_parent_oid", "m_amplitude_value", "m_type",
                            "m_pickid ->", "m_waveformid_*"],
    "stationmagnitude":    ["_oid", "_parent_oid", "m_originid ->", "m_magnitude_value",
                            "m_type", "m_amplitudeid ->", "m_waveformid_*"],
    "stationmagnitudecontribution": ["_oid", "_parent_oid ->", "m_stationmagnitudeid ->",
                                     "m_residual", "m_weight"],
    "dataused":            ["_oid", "_parent_oid ->", "m_wavetype", "m_stationcount",
                            "m_componentcount"],
    "reading":             ["_oid", "_parent_oid ->"],
    "network":             ["_oid", "m_code", "m_type", "m_description"],
    "station":             ["_oid", "_parent_oid ->", "m_code", "m_latitude",
                            "m_longitude", "m_elevation", "m_type"],
    "sensorlocation":      ["_oid", "_parent_oid ->", "m_code", "m_latitude",
                            "m_longitude", "m_elevation"],
    "stream":              ["_oid", "_parent_oid ->", "m_code",
                            "m_sampleratenumerator", "m_sampleratedenominator", "m_depth"],
}

# Descripciones por tabla para el anexo:
#   resumen   -> una línea que acompaña a las columnas en la referencia.
#   contenido -> qué datos viven en la tabla.
#   uso       -> para qué se utiliza dentro del esquema.
ANEXO = {
    "object": {
        "resumen": "Raíz común de todos los objetos del sistema.",
        "contenido": "Dos columnas: `_oid` (identidad global única) y `_timestamp`. Toda tabla "
                     "de dominio hereda este `_oid`: el objeto se reparte en una fila en `object` "
                     "y otra en la tabla específica con el mismo `_oid`.",
        "uso": "Da la identidad compartida: es la forma de relacionar \"la misma cosa\" entre "
               "tablas (event, origin, pick, etc.) sin depender de textos. El `_parent_oid` de "
               "las tablas hijas apunta a un `_oid` de acá.",
    },
    "publicobject": {
        "resumen": "Traduce `_oid` ↔ ID público.",
        "contenido": "`_oid` (idéntico al de `object`) y `m_publicid`, el identificador público "
                     "textual (p. ej. `Origin/2026-09-07_...`), único e indexado.",
        "uso": "Es el \"puente de nombres\" del esquema: las referencias entre objetos se guardan "
               "como texto (`m_preferredoriginid`, `m_pickid`, etc.) y `publicobject` permite "
               "traducir ese texto al `_oid` numérico (o al revés) con un único lookup por índice. "
               "Por eso aparece unido con `object` en la base del diagrama.",
    },
    "event": {
        "resumen": "El sismo agregado, tal como lo ve el analista.",
        "contenido": "Datos generales del evento: tipo (`m_type`), incertidumbre (`m_typecertainty`), "
                     "agencia/autor, y los punteros a la solución oficial: `m_preferredoriginid`, "
                     "`m_preferredmagnitudeid`, `m_preferredfocalmechanismid`.",
        "uso": "Puerta de entrada del análisis: de acá sale la cadena de la SOLUCIÓN PREFERIDA que "
               "NewPT consulta. Si el ID que se pasa es de un evento, el script busca su "
               "`m_preferredoriginid` para plotear ese origen.",
    },
    "origin": {
        "resumen": "Una solución de hipocentro (un \"origen\").",
        "contenido": "Resultado de una localización: tiempo origen (`m_time_value`), latitud, "
                     "longitud, profundidad, RMS (`m_quality_standarderror`), gap azimutal, cantidad "
                     "de fases usadas (`m_quality_usedphasecount`), agencia/autor y estado de "
                     "evaluación (`m_evaluationstatus`).",
        "uso": "El ORIGEN PREFERIDO es el corazón de la cadena: arrastra sus `arrival` (llegadas), "
               "`amplitude`, `stationmagnitude` (magnitudes por estación) y `dataused`. Es la "
               "solución que el analista debe Confirmar en SeisComP; si el ID copiado no es el "
               "preferido actual, NewPT avisa.",
    },
    "magnitude": {
        "resumen": "La magnitud del evento.",
        "contenido": "Valor numérico (`m_magnitude_value`), tipo (ML, Md, Mw…), y referencia al "
                     "origen del que se calculó (`m_originid`).",
        "uso": "Representa la magnitud PREFERIDA (`event.m_preferredmagnitudeid`) y agrupa las "
               "contribuciones por estación de `stationmagnitudecontribution`. NewPT la muestra "
               "en el título del ploteo.",
    },
    "eventdescription": {
        "resumen": "Textos descriptivos del evento.",
        "contenido": "Filas con `m_type` (por ejemplo `region name`) y el texto asociado "
                     "(`m_text`), vinculadas al evento por `_parent_oid`.",
        "uso": "Fuente del nombre de la región que aparece en el título del gráfico de NewPT: se "
               "toma la fila con `m_type = 'region name'`.",
    },
    "originreference": {
        "resumen": "Enlace evento ↔ origen (contexto).",
        "contenido": "Cada fila asocia un evento con uno de sus orígenes vía `m_originid` (por ID "
                     "público); `_parent_oid` apunta al evento.",
        "uso": "Aclara que un evento \"tiene asociados\" varios orígenes. Explica por qué NewPT "
               "valida que el origen pegado sea el preferido antes de generar el ploteo.",
    },
    "arrival": {
        "resumen": "Llegada de una fase usada en la localización.",
        "contenido": "Observación del cálculo del origen: fase (`m_phase_code`, p. ej. `P`/`S`), si "
                     "se usó en la localización (`m_timeused`), peso (`m_weight`) y el pick que la "
                     "respalda (`m_pickid`).",
        "uso": "Hilvana ORIGEN → PICK: cada llegada del origen preferido apunta al `pick` que le da "
               "la hora de esa fase. Contar las `arrival` con `m_timeused` da el número de fases "
               "usadas del evento.",
    },
    "pick": {
        "resumen": "Detección de una fase en un canal (tiene hora y canal).",
        "contenido": "Tiempo de la detección (`m_time_value`), canal completo vía "
                     "`m_waveformid_networkcode/stationcode/locationcode/streamcode`, fase estimada "
                     "(`m_phasehint_code`), onset, polaridad y estado de evaluación.",
        "uso": "Responde \"EN QUÉ ESTACIÓN se registró cada fase\": el canal "
               "(`m_waveformid_stationcode` + `networkcode`) se resuelve contra `station`/`network`. "
               "Es el eslabón final de la cadena preferida y la clave del proyecto de revisar los "
               "picks por evento.",
    },
    "amplitude": {
        "resumen": "Amplitud medida sobre una señal.",
        "contenido": "Valor de amplitud y tipo, asociada a un pick (`m_pickid`), al origen "
                     "(`_parent_oid`) y con canal de origen (`m_waveformid_*`).",
        "uso": "Da las mediciones de amplitud por fase, base para magnitudes tipo Mw por estación; "
               "alimenta `stationmagnitude`.",
    },
    "stationmagnitude": {
        "resumen": "Magnitud calculada por estación.",
        "contenido": "Magnitud por estación (`m_magnitude_value`, `m_type`), que referencia el "
                     "origen del evento (`m_originid`) y la amplitud usada (`m_amplitudeid`).",
        "uso": "Es la contribución individual de cada estación a la magnitud; sirve para auditar "
               "cómo se calculó la magnitud del evento.",
    },
    "stationmagnitudecontribution": {
        "resumen": "Detalle de la contribución de cada estación a la magnitud.",
        "contenido": "Residual, peso y punteros: `_parent_oid` hacia la `magnitude` y "
                     "`m_stationmagnitudeid` hacia el `stationmagnitude` que contribuye.",
        "uso": "Permite reconstruir cómo se obtuvo la magnitud preferida a partir de las magnitudes "
               "por estación (auditoría del cálculo).",
    },
    "dataused": {
        "resumen": "Resumen de datos empleados en el origen.",
        "contenido": "Por tipo de onda (`m_wavetype`, p. ej. `P`, `S`): conteo de estaciones "
                     "(`m_stationcount`) y componentes (`m_componentcount`) usados, bajo "
                     "`_parent_oid` del origen.",
        "uso": "Da el detalle \"qué datos se usaron para localizar el origen preferido\".",
    },
    "reading": {
        "resumen": "Lecturas asociadas a un pick.",
        "contenido": "Filas auxiliares enlazadas por `_parent_oid` a un `pick`.",
        "uso": "Información complementaria del proceso automático de lecturas; no participa de "
               "forma crítica en la cadena preferida.",
    },
    "network": {
        "resumen": "Red sismológica (nivel superior del inventario).",
        "contenido": "Código de red (`m_code`, p. ej. `CO`), tipo y descripción.",
        "uso": "Agrupa estaciones; el `pick.m_waveformid_networkcode` se resuelve contra el "
               "`m_code` de acá para saber la red del canal.",
    },
    "station": {
        "resumen": "Estación sismológica.",
        "contenido": "Código (`m_code`, p. ej. `HEL`), latitud, longitud, elevación, tipo, y "
                     "pertenencia a la red vía `_parent_oid`.",
        "uso": "Destino directo de `pick.m_waveformid_stationcode`: responde qué estación registró "
               "cada fase; es la referencia geográfica del inventario.",
    },
    "sensorlocation": {
        "resumen": "Emplazamiento dentro de una estación.",
        "contenido": "Código de emplazamiento (`m_code`, p. ej. `00`), coordenadas y elevación "
                     "propias, bajo `_parent_oid` de la estación.",
        "uso": "Segundo nivel del inventario: distingue posiciones/deploy dentro de la misma "
               "estación para asignar el canal correcto del pick.",
    },
    "stream": {
        "resumen": "Canal (stream) de un emplazamiento.",
        "contenido": "Código de canal (`m_code`, p. ej. `HHZ`), frecuencia de muestreo "
                     "(numerador/denominador), profundidad, ganancia y período de operación, bajo "
                     "`_parent_oid` del emplazamiento.",
        "uso": "Nivel hoja del inventario: el `pick.m_waveformid_streamcode` se resuelve acá y "
               "materializa la señal física del canal.",
    },
}

# Relaciones que se dibujan en el diagrama.
# (tabla_origen, columna_origen, tabla_destino, columna_destino, nota, resaltada,
#  card_origen, card_destino)
# La cardinalidad indica cuántas filas de ESA tabla participan en la relación
# (1 = una, N = varias, 0..1 = como máximo una/opcional).
RELACIONES = [
    ("object", "_oid", "publicobject", "_oid", "mismo _oid", False, "1", "1"),
    ("publicobject", "_oid", "origin", "_oid", "mismo _oid", False, "1", "1"),
    ("publicobject", "_oid", "event", "_oid", "mismo _oid", False, "1", "1"),
    ("publicobject", "_oid", "magnitude", "_oid", "mismo _oid", False, "1", "1"),
    ("publicobject", "_oid", "pick", "_oid", "mismo _oid", False, "1", "1"),
    ("event", "m_preferredoriginid", "origin", "m_publicid", "ORIGEN PREFERIDO", True, "N", "0..1"),
    ("event", "m_preferredmagnitudeid", "magnitude", "m_publicid", "magnitud preferida", True, "N", "0..1"),
    ("event", "_oid", "eventdescription", "_parent_oid", "descripciones del evento", False, "1", "N"),
    ("event", "_oid", "originreference", "_parent_oid", "origenes del evento", False, "1", "N"),
    ("originreference", "m_originid", "origin", "m_publicid", "un origen alternativo", False, "N", "1"),
    ("origin", "_oid", "arrival", "_parent_oid", "llegadas del origen", True, "1", "N"),
    ("arrival", "m_pickid", "pick", "m_publicid", "pick usado", True, "N", "0..1"),
    ("pick", "m_waveformid_stationcode", "station", "m_code", "qué estación", True, "N", "1"),
    ("origin", "_oid", "amplitude", "_parent_oid", "amplitudes del origen", False, "1", "N"),
    ("amplitude", "m_pickid", "pick", "m_publicid", "sobre ese pick", False, "N", "1"),
    ("origin", "m_publicid", "stationmagnitude", "m_originid", "magnitud por estación", True, "1", "N"),
    ("stationmagnitude", "m_amplitudeid", "amplitude", "m_publicid", "usa esa amplitud", False, "N", "0..1"),
    ("magnitude", "_oid", "stationmagnitudecontribution", "_parent_oid", "contribuciones", False, "1", "N"),
    ("stationmagnitudecontribution", "m_stationmagnitudeid", "stationmagnitude", "m_publicid", "de cada estación", False, "N", "1"),
    ("origin", "_oid", "dataused", "_parent_oid", "datos usados", False, "1", "N"),
    ("pick", "_oid", "reading", "_parent_oid", "lecturas del pick", False, "1", "N"),
    ("network", "_oid", "station", "_parent_oid", "st. pertenece a la red", False, "1", "N"),
    ("station", "_oid", "sensorlocation", "_parent_oid", "emplazamientos", False, "1", "N"),
    ("sensorlocation", "_oid", "stream", "_parent_oid", "canales (streams)", False, "1", "N"),
]


def conectar():
    conn = psycopg2.connect(
        host=os.environ.get("NEWPT_DB_HOST", "10.54.217.69"),
        database=os.environ.get("NEWPT_DB_DATABASE", "seiscomp"),
        user=os.environ.get("NEWPT_DB_USER", "sysop"),
        password=os.environ.get("NEWPT_DB_PASSWORD", "sysop"),
        connect_timeout=10)
    conn.set_session(readonly=True, autocommit=True)
    return conn


def extraer_esquema(conn):
    """Devuelve {tabla: [ (columna, tipo), ... ]} e índices por tabla."""
    cur = conn.cursor()
    esquema = {}
    indices = {}
    for t in TABLAS:
        cur.execute(
            """SELECT column_name, data_type FROM information_schema.columns
               WHERE table_schema='public' AND table_name=%s
               ORDER BY ordinal_position""", (t,))
        esquema[t] = cur.fetchall()
        cur.execute(
            """SELECT indexname, indexdef FROM pg_indexes
               WHERE schemaname='public' AND tablename=%s
               ORDER BY indexname""", (t,))
        indices[t] = cur.fetchall()
    return esquema, indices


def llaves_por_tabla(indices):
    """Columnas que son llave por tabla, derivadas de pg_indexes.

    PRIMARY KEY (índice *_pkey) marca las columnas como "llave"; los demás
    índices UNIQUE las marcan como "única". Se conserva el orden de aparición.
    """
    import re
    re_btree = re.compile(r"USING\s+btree\s*\(([^)]*)\)")
    out = {}
    for t, idx in indices.items():
        info = {}
        for name, defn in idx:
            es_pk = name.endswith("_pkey")
            es_uniq = defn.startswith("CREATE UNIQUE INDEX")
            if not (es_pk or es_uniq):
                continue
            m = re_btree.search(defn)
            if not m:
                continue
            for c in m.group(1).split(","):
                c = c.strip().strip('"')
                if not c:
                    continue
                if es_pk:
                    info[c] = "llave"
                elif c not in info:
                    info[c] = "única"
        out[t] = info
    return out


# ---------------------------------------------------------------------------
# Render SVG + HTML interactivo
# ---------------------------------------------------------------------------
ANCHO_CAJA = 250
ALTO_LINEA = 15
PAD_TITULO = 34
RADIO = 10


def layout(esquema):
    """Distribuye las cajas en 4 columnas (por grupo) y devuelve posiciones."""
    anchos = {}
    altos = {}
    for t in TABLAS:
        n = len(CLAVE[t])
        anchos[t] = ANCHO_CAJA
        altos[t] = PAD_TITULO + n * ALTO_LINEA + 16
    # Columnas: 0=base, 1=núcleo, 2=cadena, 3=inventario
    col_de_grupo = {"BASE": 0, "NÚCLEO SÍSMICO": 1,
                    "CADENA DEL ORIGEN PREFERIDO": 2, "INVENTARIO DE ESTACIONES": 3}
    max_ancho = 300
    pos = {}
    y_grupo = {}
    for g, ts in GRUPOS:
        col = col_de_grupo[g]
        x = col * (max_ancho + 90) + 40
        y = 90
        y_grupo[g] = []
        for t in ts:
            pos[t] = (x, y, anchos[t], altos[t])
            y_grupo[g].append((t, y))
            # separación vertical generosa: deja hueco para dos badges (18 px
            # cada uno) en las flechas que enlazan tablas apiladas en la misma
            # columna, sin que se pisen
            y += altos[t] + 56
    ancho_total = (max_ancho + 90) * 4 + 60
    alto_total = 0
    for g, yg in y_grupo.items():
        for t, y in yg:
            alto_total = max(alto_total, y + altos[t] + 60)
    return pos, y_grupo, ancho_total, alto_total


def esc_xml(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def caja_svg(t, x, y, w, h, color_titulo, color_fondo, resaltada, titulo):
    cols = CLAVE[t]
    stroke = "#e05c00" if resaltada else "#5f6b7a"
    ancho_stroke = "2.5" if resaltada else "1.5"
    lines = ["<g>"]
    if titulo:
        lines.append(f"<title>{titulo}</title>")
    lines.append(
        '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" '
        'fill="%s" stroke="%s" stroke-width="%s"/>'
        % (x, y, w, h, RADIO, color_fondo, stroke, ancho_stroke))
    lines.append(
        '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s"/>'
        % (x, y, w, PAD_TITULO, RADIO, color_titulo))
    # cuadra el borde inferior del encabezado: solo quedan redondeadas las
    # esquinas superiores, así el arco no tapa la primera fila de columnas
    lines.append(
        '<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>'
        % (x, y + RADIO, w, PAD_TITULO - RADIO, color_titulo))
    lines.append(
        '<text x="%d" y="%d" font-family="Arial" font-size="13" '
        'font-weight="bold" fill="#ffffff">%s</text>'
        % (x + 10, y + 20, esc_xml(t)))
    yy = y + PAD_TITULO + 11
    for c in cols:
        resaltar = c.endswith("->") or "waveformid_stationcode" in c
        color = "#b33900" if resaltar else "#2c3440"
        lines.append(
            '<text x="%d" y="%d" font-family="Consolas,monospace" font-size="10.5" '
            'fill="%s">%s</text>'
            % (x + 10, yy, color, esc_xml(c)))
        yy += ALTO_LINEA
    lines.append("</g>")
    return "\n".join(lines)


def flecha_svg(x1, y1, x2, y2, color, nota):
    """Línea con punta de flecha entre dos puntos + etiqueta."""
    import math
    dx, dy = x2 - x1, y2 - y1
    largo = math.hypot(dx, dy) or 1
    ux, uy = dx / largo, dy / largo
    # retrocede 6 px antes del destino (punta)
    xa, ya = x2 - ux * 8, y2 - uy * 8
    s = [f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{xa:.0f}" y2="{ya:.0f}" ']
    s.append(f'stroke="{color}" stroke-width="2" marker-end="url(#arr{color[1:]})"/>')
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if nota:
        s.append(f'<text x="{mx:.0f}" y="{my - 4:.0f}" text-anchor="middle" '
                 f'font-family="Arial" font-size="9" fill="{color}" '
                 f'paint-order="stroke" stroke="#ffffff" stroke-width="3">{esc_xml(nota)}</text>')
    return "\n".join(s)


def seg_atraviesa_rect(x1, y1, x2, y2, rx, ry, rw, rh):
    """True si el segmento toca el rectángulo (muestreo a pasos de ~3 px o
    menos). Permite detectar si un badge/etiqueta cruza una línea de flecha."""
    import math
    # descarte rápido por caja envolvente antes de muestrear
    if (max(x1, x2) < rx or min(x1, x2) > rx + rw or
            max(y1, y2) < ry or min(y1, y2) > ry + rh):
        return False

    def en(x, y):
        return rx <= x <= rx + rw and ry <= y <= ry + rh
    lar = math.hypot(x2 - x1, y2 - y1)
    if lar <= 0:
        return en(x1, y1)
    pasos = max(1, int(lar / 3))
    for i in range(pasos + 1):
        if en(x1 + (x2 - x1) * i / pasos, y1 + (y2 - y1) * i / pasos):
            return True
    return False


def pos_card(px, py, ux, uy, sep, boxes, lineas, asignados, W, H, seg_propios, dims, box_propia=None):
    """Busca el centro del símbolo de cardinalidad en el hueco entre cajas.

    Se prefiere dejar el símbolo SOBRE la línea (desplazamiento perpendicular
    nulo), empezando a `sep` px del borde: las terminaciones quedan ancladas
    al conector. Si ese sitio no está limpio, se recorre una retícula (en
    perpendicular, a pasos finos) y se queda con el mejor candidato.
    Reglas duras: no adentrarse en una caja ajena, no tocar el contenido de
    la caja propia (box_propia) más allá de su banda del borde (8 px), no
    tapar otro símbolo, no salirse del lienzo; las líneas/tramos de OTROS
    conectores que crucen el núcleo cuentan como penalidad (los propios pasan
    por debajo, el símbolo se pinta encima).
    """
    import math
    ancho, alto = dims
    vp = (-uy, ux)

    def eval_cand(cx, cy):
        px0, py0 = cx - ancho / 2, cy - alto / 2
        pw, ph = ancho, alto
        for (x, y, aw, ah) in boxes:
            if box_propia is not None and (x, y, aw, ah) == box_propia:
                # la caja propia solo puede tocarse por la banda del borde
                x_, y_, aw_, ah_ = x + 8, y + 8, aw - 16, ah - 16
                if not (px0 + pw <= x_ or px0 >= x_ + aw_ or
                        py0 + ph <= y_ or py0 >= y_ + ah_):
                    return None
            else:
                if not (px0 + pw <= x - 6 or px0 >= x + aw + 6 or
                        py0 + ph <= y - 6 or py0 >= y + ah + 6):
                    return None
        for (ax, ay, aw, ah) in asignados:
            if not (px0 + pw <= ax or px0 >= ax + aw or
                    py0 + ph <= ay or py0 >= ay + ah):
                return None
        if px0 < 4 or px0 + pw > W - 4 or py0 < 4 or py0 + ph > H - 4:
            return None
        # núcleo: zona central del símbolo; un conector ajeno que la cruce se
        # cuenta como penalidad (se tolera solo si no hay alternativa)
        xc0, yc0, cw, ch = px0 + 7, py0 + 5, pw - 14, ph - 10
        pen = 0
        for li, (lx1, ly1, lx2, ly2) in enumerate(lineas):
            if li in seg_propios:
                continue
            if seg_atraviesa_rect(lx1, ly1, lx2, ly2, xc0, yc0, cw, ch):
                pen += 1
        return pen

    # primera pasada: solo sobre el eje de la línea
    a = sep
    while a <= sep + 56:
        cx, cy = px + ux * a, py + uy * a
        if eval_cand(cx, cy) == 0:
            return cx, cy
        a += 4
    # si no hay sitio limpio sobre el eje, retícula completa (fallback)
    mejor = None
    mejor_dist = None
    for a in range(sep, sep + 84, 8):
        for perp in range(0, 60, 6):
            for signo in (1, -1):
                cx = px + ux * a + vp[0] * perp * signo
                cy = py + uy * a + vp[1] * perp * signo
                r = eval_cand(cx, cy)
                if r is None:
                    continue
                dist = math.hypot(cx - px, cy - py)
                if mejor is None or r < mejor[0] or (r == mejor[0] and dist < mejor_dist):
                    mejor = (r, cx, cy)
                    mejor_dist = dist
    if mejor is None:
        return px + ux * sep, py + uy * sep
    return mejor[1], mejor[2]


def tam_card(txt):
    """Dimensión del área (caja de colisión) del símbolo de cardinalidad."""
    ext = {"1": 14, "N": 16, "0..1": 18, "0..N": 26}
    return ext.get(txt, 18), 20


def _interior_card(txt, color, trazo):
    """Trazos del glifo en coordenadas locales.

    El eje +x (horizontal local) apunta hacia la tabla que el símbolo
    describe; las formas son simétricas respecto del eje x y quedan ancladas
    al extremo de la línea (el conector "muere" dentro del símbolo):
      '1'    → barra perpendicular al conector (una)
      'N'    → pata de cuervo: tres líneas abriéndose hacia la tabla (varias)
      '0..1' → círculo sobre la línea + barra (cero o una)
      '0..N' → círculo sobre la línea + pata de cuervo (cero o varias)
    """
    barra = (f'<path d="M0,-9 L0,9" fill="none" stroke="{color}" '
             f'stroke-width="{trazo}" stroke-linecap="round"/>')
    pie = (f'<path d="M0,-3 L8,-9 M0,0 L10,0 M0,3 L8,9" fill="none" '
           f'stroke="{color}" stroke-width="{trazo}" stroke-linecap="round"/>')
    circulo = (f'<circle cx="2" cy="0" r="4.2" fill="#ffffff" '
               f'stroke="{color}" stroke-width="{trazo}"/>')
    if txt == "1":
        return barra
    if txt == "N":
        return pie
    if txt == "0..1":
        return circulo + (f'<path d="M9,-9 L9,9" fill="none" stroke="{color}" '
                          f'stroke-width="{trazo}" stroke-linecap="round"/>')
    if txt == "0..N":
        return circulo + (f'<path d="M5,-2 L8,-6 M5,0 L10,0 M5,2 L8,6" fill="none" '
                          f'stroke="{color}" stroke-width="{trazo}" '
                          f'stroke-linecap="round"/>')
    return barra


def card_svg(cx, cy, txt, color, ang_deg):
    """Símbolo de crow's foot en la posición (cx,cy) rotado `ang_deg`.

    ang_deg se mide igual que el atributo transform rotate() de SVG (sentido
    horario en pantalla, y positivo hacia abajo) y apunta con +x local hacia
    la tabla que el símbolo describe.
    """
    trazo = 3.2
    return (
        f'<g data-card="{esc_xml(txt)}" '
        f'transform="translate({cx:.0f} {cy:.0f}) rotate({ang_deg:.0f})">'
        f'{_interior_card(txt, color, trazo)}'
        f'</g>')


def punto_borde(x, y, w, h, x2, y2):
    """Punto del borde de la caja (x,y,w,h) hacia (x2,y2)."""
    cx, cy = x + w / 2, y + h / 2
    import math
    dx, dy = x2 - cx, y2 - cy
    if dx == 0 and dy == 0:
        return cx, cy
    escala = min((w / 2) / abs(dx) if dx else 10 ** 9,
                 (h / 2) / abs(dy) if dy else 10 ** 9)
    return cx + dx * min(escala, 1) * 0.9, cy + dy * min(escala, 1) * 0.9


def separar_puertos(geoms):
    """Reparte los extremos de las flechas a lo largo del borde de cada caja.

    Cuando varias flechas salen de la misma caja todas comparten el mismo
    punto del borde y sus etiquetas/símbolos se pisan. Para cada tabla origen
    (y destino) con más de una flecha, se desplaza cada extremo a lo largo de
    la tangente del borde, en carriles ordenados por ángulo, para que los
    conectores queden visualmente separados.

    geoms: lista de dicts {o, d, sx, sy, tx, ty, cx1, cy1, cx2, cy2}.
    """
    from collections import defaultdict
    import math

    def aplicar(grupo, es_origen):
        n = len(grupo)
        if n < 2:
            return
        vx = sum(g["ux"] for g in grupo) / n
        vy = sum(g["uy"] for g in grupo) / n
        vmod = math.hypot(vx, vy) or 1
        vx /= vmod
        vy /= vmod
        tdx, tdy = -vy, vx  # tangente del borde
        if es_origen:
            grupo.sort(key=lambda g: math.atan2(g["cy2"] - g["cy1"],
                                                g["cx2"] - g["cx1"]))
        else:
            grupo.sort(key=lambda g: math.atan2(g["cy1"] - g["cy2"],
                                                g["cx1"] - g["cx2"]))
        for j, g in enumerate(grupo):
            carril = j - (n - 1) / 2
            if es_origen:
                g["sx"] += tdx * carril * 20
                g["sy"] += tdy * carril * 20
            else:
                g["tx"] += tdx * carril * 20
                g["ty"] += tdy * carril * 20

    por_origen = defaultdict(list)
    por_destino = defaultdict(list)
    for g in geoms:
        por_origen[g["o"]].append(g)
        por_destino[g["d"]].append(g)
    for grupo in por_origen.values():
        aplicar(grupo, True)
    for grupo in por_destino.values():
        aplicar(grupo, False)
    # redirigir cada flecha con los nuevos extremos
    for g in geoms:
        dx, dy = g["tx"] - g["sx"], g["ty"] - g["sy"]
        lar = math.hypot(dx, dy) or 1
        g["lar"] = lar
        g["ux"] = dx / lar
        g["uy"] = dy / lar


def construir_conectores(pos, col_de_grupo, ancho_total, alto_total):
    """Geometría de los conectores + notas + símbolos de cardinalidad.

    Devuelve (geoms, lineas, seg_idx, flechas, capa_sup, glifos, notas).
    Los conectores que en línea recta atravesarían una caja ajena se enrutan
    con codos por los corredores libres entre columnas (carriles propios), y
    todas las líneas terminan en el símbolo de cardinalidad (sin punta de
    flecha). Los símbolos y las notas van ENCIMA de las cajas.
    """
    import math
    from collections import defaultdict
    boxes = [pos[t] for t in TABLAS]
    CORREDORES = {"c01": (290, 430, 360), "c12": (680, 820, 750),
                  "c23": (1070, 1210, 1140)}
    TOPY = 45

    def col_de(t):
        for g_, ts in GRUPOS:
            if t in ts:
                return col_de_grupo[g_]
        return 0

    # 1) geometría básica de cada conector (puntos de borde)
    geoms = []
    for i, (o, co_, d, cd_, nota, res, cs, cdest) in enumerate(RELACIONES):
        color = "#e05c00" if res else "#8a97a6"
        x1, y1, w1, h1 = pos[o]
        x2, y2, w2, h2 = pos[d]
        g = {"i": i, "o": o, "d": d, "color": color,
             "nota": nota, "cs": cs, "cdest": cdest,
             "cx1": x1 + w1 / 2, "cy1": y1 + h1 / 2,
             "cx2": x2 + w2 / 2, "cy2": y2 + h2 / 2}
        g["sx"], g["sy"] = punto_borde(x1, y1, w1, h1, g["cx2"], g["cy2"])
        g["tx"], g["ty"] = punto_borde(x2, y2, w2, h2, g["cx1"], g["cy1"])
        dx, dy = g["tx"] - g["sx"], g["ty"] - g["sy"]
        lar = math.hypot(dx, dy) or 1
        g["lar"] = lar
        g["ux"], g["uy"] = dx / lar, dy / lar
        geoms.append(g)
    separar_puertos(geoms)

    # 2) ¿recta o codos? (si la recta atraviesa una caja ajena)
    for g in geoms:
        g["codos"] = any(
            seg_atraviesa_rect(g["sx"], g["sy"], g["tx"], g["ty"],
                               pos[t][0], pos[t][1], pos[t][2], pos[t][3])
            for t in TABLAS if t not in (g["o"], g["d"]))

    # 3) los enrutados salen por el lado derecho de la caja fuente y entran
    #    por el lado que mira al corredor; se reparten los puertos a lo largo
    #    de ese lado vertical para no apilarse
    rout = [g for g in geoms if g["codos"]]
    gpo = defaultdict(list)
    for g in rout:
        gpo[(g["o"], "R", "o")].append(g)
        lado_d = "R" if col_de(g["o"]) == col_de(g["d"]) else "L"
        gpo[(g["d"], lado_d, "d")].append(g)
    for (t, lado, rol), gr in gpo.items():
        bx, by, bw, bh = pos[t]
        if len(gr) == 1:
            continue
        gr.sort(key=lambda gg: gg["cy2"] if rol == "o" else gg["cy1"])
        span = bh - 56
        for k, gg in enumerate(gr):
            yy = by + 28 + span * k / max(1, len(gr) - 1)
            if rol == "o":
                gg["sy"] = yy
            else:
                gg["ty"] = yy

    def lado_dest(g):
        return "R" if col_de(g["o"]) == col_de(g["d"]) else "L"

    def cara_x(t, lado):
        bx, by, bw, bh = pos[t]
        return bx + bw if lado == "R" else bx

    # 4) tramos verticales por corredor y asignación de carriles
    def tramos(g):
        co, cd = col_de(g["o"]), col_de(g["d"])
        if co == cd:
            c = "c%d%d" % (co, co + 1)
            return [(c, (g["sy"], g["ty"]))]
        if cd == co + 1:
            c = "c%d%d" % (co, co + 1)
            return [(c, (g["sy"], g["ty"]))]
        return [("c01", (g["sy"], TOPY)), ("c12", (TOPY, g["ty"]))]

    lanes = {}
    for c in ("c01", "c12", "c23"):
        rs = [g for g in rout if any(cc == c for cc, _ in tramos(g))]
        if not rs:
            continue
        rs.sort(key=lambda g: next((y0 + y1) / 2
                                   for cc, (y0, y1) in tramos(g) if cc == c))
        n = len(rs)
        paso = min(16.0, 96.0 / max(1, n - 1))
        for k, g in enumerate(rs):
            lanes[(c, g["i"])] = CORREDORES[c][2] + (k - (n - 1) / 2) * paso

    # 5) polígono de cada conector (con codos o recto)
    def poligono(g):
        if not g["codos"]:
            return [(g["sx"], g["sy"]), (g["tx"], g["ty"])]
        pt0 = (cara_x(g["o"], "R"), g["sy"])
        ptn = (cara_x(g["d"], lado_dest(g)), g["ty"])
        ts = tramos(g)
        if len(ts) == 1:
            c, (y0, y1) = ts[0]
            lx = lanes[(c, g["i"])]
            return [pt0, (lx, y0), (lx, y1), ptn]
        (c0, (y0, _)), (c1, (_, y1)) = ts
        lx0 = lanes[(c0, g["i"])]
        lx1 = lanes[(c1, g["i"])]
        return [pt0, (lx0, y0), (lx0, TOPY), (lx1, TOPY), (lx1, y1), ptn]

    for g in geoms:
        pts = poligono(g)
        g["pts"] = [tuple(round(v, 4) for v in p) for p in pts]
        g["lar"] = sum(math.hypot(pts[a + 1][0] - pts[a][0],
                                  pts[a + 1][1] - pts[a][1])
                       for a in range(len(pts) - 1))

    # 6) lista plana de tramos (para colisiones) con sus índices por relación
    lineas = []
    seg_idx = {}
    for g in geoms:
        pts = g["pts"]
        idxs = []
        for a in range(len(pts) - 1):
            idxs.append(len(lineas))
            lineas.append((pts[a][0], pts[a][1], pts[a + 1][0], pts[a + 1][1]))
        seg_idx[g["i"]] = idxs

    # 7) líneas sin punta de flecha (terminan en el símbolo de cardinalidad)
    flechas = []
    for g in geoms:
        pts = g["pts"]
        sw = 2.5 if g["color"] == "#e05c00" else 1.5
        for a in range(len(pts) - 1):
            flechas.append(
                f'<line x1="{pts[a][0]:.0f}" y1="{pts[a][1]:.0f}" '
                f'x2="{pts[a + 1][0]:.0f}" y2="{pts[a + 1][1]:.0f}" '
                f'stroke="{g["color"]}" stroke-width="{sw}" '
                f'stroke-linecap="round"/>')

    # 8) símbolos de cardinalidad anclados al eje, junto al borde de cada caja
    glifos = []
    asignados = []
    for g in geoms:
        pts = g["pts"]
        dx0 = pts[1][0] - pts[0][0]
        dy0 = pts[1][1] - pts[0][1]
        l0 = math.hypot(dx0, dy0) or 1
        u0x, u0y = dx0 / l0, dy0 / l0
        aw, ah = tam_card(g["cs"])
        ang_src = math.degrees(math.atan2(-u0y, -u0x))
        csx, csy = pos_card(pts[0][0], pts[0][1], u0x, u0y, 10,
                            boxes, lineas, asignados, ancho_total, alto_total,
                            set(seg_idx[g["i"]]), (aw, ah), pos[g["o"]])
        asignados.append((csx - aw / 2, csy - ah / 2, aw, ah))
        n = len(pts) - 1
        dxn = pts[n][0] - pts[n - 1][0]
        dyn = pts[n][1] - pts[n - 1][1]
        ln = math.hypot(dxn, dyn) or 1
        uNx, uNy = dxn / ln, dyn / ln
        aw, ah = tam_card(g["cdest"])
        ang_dst = math.degrees(math.atan2(uNy, uNx))
        ctx, cty = pos_card(pts[n][0], pts[n][1], -uNx, -uNy, 10,
                            boxes, lineas, asignados, ancho_total, alto_total,
                            set(seg_idx[g["i"]]), (aw, ah), pos[g["d"]])
        asignados.append((ctx - aw / 2, cty - ah / 2, aw, ah))
        glifos.append((g["i"], csx, csy, g["cs"], ang_src,
                       ctx, cty, g["cdest"], ang_dst, g["color"]))

    # 9) notas centrales: sobre el tramo más largo, en una ventana libre
    #    (sin tapar cajas, símbolos, otras notas ni conectores ajenos)
    notas_fijas = []
    notas = []

    def nota_libre(px, py, txt, seg_ok):
        w = 4.6 * len(txt)
        b = (px - w / 2 - 2, py - 9, w + 4, 13)
        bx0, by0, bw, bh = b
        for (x, y, aw, ah) in boxes:
            if not (bx0 + bw <= x - 4 or bx0 >= x + aw + 4 or
                    by0 + bh <= y - 4 or by0 >= y + ah + 4):
                return False
        for (ax, ay, aw, ah) in asignados:
            if not (bx0 + bw <= ax or bx0 >= ax + aw or
                    by0 + bh <= ay or by0 >= ay + ah):
                return False
        for (nx, ny, nw, nh) in notas_fijas:
            if not (bx0 + bw <= nx or bx0 >= nx + nw or
                    by0 + bh <= ny or by0 >= ny + nh):
                return False
        return True

    capa_sup = []
    for g in geoms:
        i = g["i"]
        pts = g["pts"]
        seg_ok = set(seg_idx[i])
        if g["nota"] and g["lar"] >= 140:
            mejor = max(range(len(pts) - 1), key=lambda a:
                        (pts[a + 1][0] - pts[a][0]) ** 2 +
                        (pts[a + 1][1] - pts[a][1]) ** 2)
            (q0x, q0y), (q1x, q1y) = pts[mejor], pts[mejor + 1]
            for f in (0.5, 0.45, 0.55, 0.4, 0.6, 0.35, 0.65, 0.3, 0.7):
                px = q0x + (q1x - q0x) * f
                py = q0y + (q1y - q0y) * f
                if nota_libre(px, py, g["nota"], seg_ok):
                    w = 4.6 * len(g["nota"])
                    notas_fijas.append((px - w / 2 - 2, py - 9, w + 4, 13))
                    notas.append((px, py, g["nota"]))
                    capa_sup.append(
                        f'<text x="{px:.0f}" y="{py - 4:.0f}" text-anchor="middle" '
                        f'font-family="Arial" font-size="9.5" fill="{g["color"]}" '
                        f'paint-order="stroke" stroke="#ffffff" stroke-width="3">'
                        f'{esc_xml(g["nota"])}</text>')
                    break
        _, csx, csy, cs, ang_src, ctx, cty, cdest, ang_dst, color = glifos[i]
        capa_sup.append(card_svg(csx, csy, cs, color, ang_src))
        capa_sup.append(card_svg(ctx, cty, cdest, color, ang_dst))

    return geoms, lineas, seg_idx, flechas, capa_sup, glifos, notas


def generar_html(esquema, indices):
    pos, y_grupo, ancho_total, alto_total = layout(esquema)
    # colores por grupo
    colores = {
        "BASE": ("#4a5568", "#eef1f5"),
        "NÚCLEO SÍSMICO": ("#2c5282", "#e8f0fc"),
        "CADENA DEL ORIGEN PREFERIDO": ("#c05621", "#fdf0e2"),
        "INVENTARIO DE ESTACIONES": ("#276749", "#e8f6ee"),
    }
    col_de_grupo = {"BASE": 0, "NÚCLEO SÍSMICO": 1,
                    "CADENA DEL ORIGEN PREFERIDO": 2, "INVENTARIO DE ESTACIONES": 3}
    grupo_de_tabla = {}
    for g, ts in GRUPOS:
        for t in ts:
            grupo_de_tabla[t] = g

    # líneas (conectores) y capa superior (notas + símbolos de cardinalidad).
    # Los símbolos y las notas van ENCIMA de las cajas para que nunca se
    # oculten. Las flechas que en línea recta atravesarían una caja ajena se
    # enrutan con codos por los corredores libres entre columnas, y cada
    # conector termina en el símbolo de cardinalidad (sin punta de flecha).
    geoms, lineas, seg_idx, flechas, capa_sup, glifos, notas = \
        construir_conectores(pos, col_de_grupo, ancho_total, alto_total)

    resaltadas = set()
    for o, co, d, cd, n, r, _cs, _cd in RELACIONES:
        if r:
            resaltadas.add(o)
            resaltadas.add(d)

    cajas = []
    for t in TABLAS:
        x, y, w, h = pos[t]
        ct, cf = colores[grupo_de_tabla[t]]
        res = t in resaltadas
        a = ANEXO[t]
        tip = (f'{a["resumen"]} — Contiene: {a["contenido"]} '
               f'— Para qué se usa: {a["uso"]}')
        cajas.append(caja_svg(t, x, y, w, h, ct, cf, res, esc_xml(tip)))

    # marcas de grupos
    grupos_svg = []
    for g, yg in y_grupo.items():
        col = col_de_grupo[g]
        xg = col * (320 + 90) + 320 + -20
        x0 = min(pos[t][0] for t, _ in yg) - 12
        y0 = min(y for t, y in yg) - 22
        ymax = max(y + pos[t][3] for t, y in yg) + 12
        ct, cf = colores[g]
        grupos_svg.append(
            f'<rect x="{x0}" y="{y0}" width="{ANCHO_CAJA + 24}" '
            f'height="{ymax - y0}" rx="14" fill="{cf}" fill-opacity="0.55" '
            f'stroke="{ct}" stroke-width="1.5" stroke-dasharray="6,4"/>')
        grupos_svg.append(
            f'<text x="{x0 + ANCHO_CAJA / 2 + 12}" y="{y0 - 8}" text-anchor="middle" '
            f'font-family="Arial" font-size="12" font-weight="bold" fill="{ct}">{esc_xml(g)}</text>')

    defs = ""
    svg = (
        f'<svg id="esquemaSvg" width="{ancho_total}" height="{alto_total}" '
        f'viewBox="0 0 {ancho_total} {alto_total}" '
        f'xmlns="http://www.w3.org/2000/svg" style="background:#fbfcfe">'
        f'<defs>{defs}</defs>'
        + "\n".join(grupos_svg)
        + "\n".join(flechas)
        + "\n".join(cajas)
        + "\n".join(capa_sup)
        + "</svg>"
    )

    llaves = llaves_por_tabla(indices)
    anexo_html = []
    anexo_html.append("<h2>Anexo — Descripción de cada tabla</h2>")
    for g, ts in GRUPOS:
        anexo_html.append(f"<h3>{esc_xml(g)}</h3>")
        for t in ts:
            a = ANEXO[t]
            anexo_html.append(f"<h4>{esc_xml(t)}</h4>")
            anexo_html.append(
                f'<p><b>Contiene.</b> {esc_xml(a["contenido"])}</p>')
            anexo_html.append(
                f'<p><b>Para qué se usa.</b> {esc_xml(a["uso"])}</p>')
            anexo_html.append("<p><b>Atributos:</b></p>")
            anexo_html.append(
                '<table class="atributos" border="1" cellspacing="0" cellpadding="4">')
            anexo_html.append("<thead><tr><th>Nombre</th><th>Tipo de dato</th></tr></thead>")
            anexo_html.append("<tbody>")
            for c, tipo in esquema[t]:
                marca = llaves.get(t, {}).get(c)
                if marca:
                    anexo_html.append(
                        f'<tr><td><b>{esc_xml(c)}</b> '
                        f'<span class="marca">({marca})</span></td>'
                        f'<td>{esc_xml(tipo)}</td></tr>')
                else:
                    anexo_html.append(
                        f'<tr><td>{esc_xml(c)}</td><td>{esc_xml(tipo)}</td></tr>')
            anexo_html.append("</tbody>")
            anexo_html.append("</table>")
    anexo_html = "\n".join(anexo_html)

    def mini_glifo(txt):
        # mini-SVG horizontal (+x a la derecha) con el fondo transparente
        return (
            f'<svg width="26" height="24" viewBox="-2 -12 26 24" '
            f'xmlns="http://www.w3.org/2000/svg">{_interior_card(txt, "#1f2937", 2.4)}</svg>')

    items = [
        (mini_glifo("1"), "una (1)"),
        (mini_glifo("N"), "varias (N)"),
        (mini_glifo("0..1"), "cero o una (0..1)"),
        (mini_glifo("0..N"), "cero o varias (0..N)"),
    ]
    leyenda_card = "".join(
        f'<span class="cardl">{svg}{txt}</span>' for svg, txt in items)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Esquema BD SeisComp6 · NewPT</title>
<style>
 body {{ margin:0; font-family:Arial,Helvetica,sans-serif; }}
 #barra {{ position:sticky; top:0; z-index:10; background:#1f2937; color:#fff;
           padding:8px 16px; display:flex; align-items:center; gap:12px; }}
 #barra b {{ font-size:15px; }}
 #barra button {{ background:#374151; color:#fff; border:1px solid #6b7280;
                  border-radius:6px; padding:4px 10px; cursor:pointer; font-size:13px; }}
 #barra button:hover {{ background:#4b5563; }}
 #lienzo {{ overflow:hidden; position:relative; width:100%; height:880px;
            background:#fbfcfe; cursor:grab; }}
 #lienzo:active {{ cursor:grabbing; }}
 #leyenda {{ padding:10px 16px; background:#f3f4f6; border-top:1px solid #d1d5db; }}
 #leyenda span {{ display:inline-block; margin-right:18px; font-size:12px; }}
 #leyenda-card {{ padding:8px 16px; background:#eef1f4; border-bottom:1px solid #d1d5db;
                  font-size:12px; color:#1f2937; }}
 #leyenda-card .cardl {{ display:inline-flex; align-items:center; margin:4px 18px 0 0; }}
 #leyenda-card .cardl svg {{ margin-right:6px; vertical-align:middle; }}
 .chip {{ display:inline-block; width:12px; height:12px; border-radius:3px;
         margin-right:4px; vertical-align:middle; }}
 #anexo {{ padding:20px 16px 40px; max-width:1050px; }}
 #anexo h2 {{ font-size:20px; border-bottom:2px solid #1f2937; padding-bottom:6px; }}
 #anexo h3 {{ font-size:15px; color:#1f2937; margin:22px 0 4px; }}
 #anexo h4 {{ font-size:13px; margin:12px 0 2px; color:#374151; }}
 #anexo p {{ margin:2px 0 4px; font-size:13px; color:#1f2937; }}
 #anexo ul {{ margin:2px 0 8px 22px; }}
 #anexo li {{ font-size:12.5px; margin:1px 0; color:#1f2937; }}
 #anexo table.atributos {{ border-collapse:collapse; margin:4px 0 14px; }}
 #anexo table.atributos th,
 #anexo table.atributos td {{ border:1px solid #9aa4b1; padding:3px 8px;
         font-size:12.5px; text-align:left; vertical-align:top; }}
 #anexo table.atributos th {{ background:#1f2937; color:#fff; font-weight:bold; }}
 #anexo table.atributos td {{ font-family:Consolas,monospace; font-size:12px; }}
 #anexo table.atributos .marca {{ font-family:Arial; color:#6b7280; }}
 #anexo code {{ font-family:Consolas,monospace; font-size:12px; background:#eef1f4;
                padding:0 3px; border-radius:3px; }}
</style>
</head>
<body>
<div id="barra">
  <b>Esquema BD SeisComp6</b>
  <span style="color:#cbd5e1">rueda del ratón = zoom · arrastrar = mover · tocar "Restablecer" para volver</span>
  <span style="flex:1"></span>
  <button onclick="zoomBy(1.3)">+</button>
  <button onclick="zoomBy(0.77)">−</button>
  <button onclick="encajar()">Encajar</button>
  <button onclick="resetZoom()">Restablecer</button>
</div>
<div id="lienzo">
  <div id="interior">{svg}</div>
</div>
<div id="leyenda">
  <b>Leyenda:</b>
  <span><span class="chip" style="background:#c05621"></span>Cadena de la SOLUCIÓN PREFERIDA (evento → origen preferido → llegadas → picks → estación)</span>
  <span><span class="chip" style="background:#2c5282"></span>Núcleo sísmico</span>
  <span><span class="chip" style="background:#276749"></span>Inventario de estaciones</span>
  <span><span class="chip" style="background:#4a5568"></span>Base</span>
  <span style="color:#e05c00"><b>Líneas naranjas:</b> cadena preferida · <b>grises:</b> resto de relaciones</span>
  <span>Las líneas indican la columna que materializa el enlace.</span>
  <span>Pasa el cursor sobre una caja para ver su descripción.</span>
</div>
<div id="leyenda-card">
  <b>Cardinalidad</b> — cada conector termina en un símbolo encajado en el extremo, junto a cada tabla; indica cuántas filas de ESA tabla participan en la relación:
  {leyenda_card}
</div>
<section id="anexo">
{anexo_html}
</section>
<script>
let escala = 1, tx = 0, ty = 0;
const lienzo = document.getElementById('lienzo');
const interior = document.getElementById('interior');
const svg = document.getElementById('esquemaSvg');
function aplicar() {{
  interior.style.transform = `translate(${{tx}}px,${{ty}}px) scale(${{escala}})`;
  interior.style.transformOrigin = '0 0';
}}
function zoomBy(f, cX, cY) {{
  const r = lienzo.getBoundingClientRect();
  const px = cX !== undefined ? cX - r.left : r.width / 2;
  const py = cY !== undefined ? cY - r.top : r.height / 2;
  const ne = Math.min(6, Math.max(0.2, escala * f));
  const k = ne / escala;
  tx = px - (px - tx) * k;
  ty = py - (py - ty) * k;
  escala = ne; aplicar();
}}
function resetZoom() {{ escala = 1; tx = 0; ty = 0; aplicar(); }}
function encajar() {{
  const r = lienzo.getBoundingClientRect();
  const sw = parseFloat(svg.getAttribute('width'));
  const sh = parseFloat(svg.getAttribute('height'));
  const s = Math.min(r.width / sw, r.height / sh) * 0.96;
  escala = s;
  tx = (r.width - sw * s) / 2;
  ty = (r.height - sh * s) / 2;
  aplicar();
}}
lienzo.addEventListener('wheel', (e) => {{
  e.preventDefault();
  zoomBy(e.deltaY < 0 ? 1.12 : 0.9, e.clientX, e.clientY);
}}, {{ passive:false }});
let arrastrando = false, ix = 0, iy = 0;
lienzo.addEventListener('mousedown', (e) => {{
  arrastrando = true; ix = e.clientX - tx; iy = e.clientY - ty;
  lienzo.style.cursor = 'grabbing';
}});
window.addEventListener('mousemove', (e) => {{
  if (arrastrando) {{ tx = e.clientX - ix; ty = e.clientY - iy; aplicar(); }}
}});
window.addEventListener('mouseup', () => {{
  arrastrando = false; lienzo.style.cursor = 'grab';
}});
aplicar();
encajar();
</script>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def generar_md(esquema, indices):
    L = []
    L.append("# Esquema de la base de datos SeisComp6")
    L.append("")
    L.append(f"_Documento de referencia. Generado el {date.today().strftime('%d/%m/%Y')}._")
    L.append("")
    L.append("## Regla rectora")
    L.append("")
    L.append("Toda la documentación parte de la **solución preferida**: la que apunta "
             "`event.m_preferredoriginid`. Es la solución que un analista procesa (y la que "
             "NewPT usa y valida). Un evento puede tener varios orígenes (ver "
             "`originreference`), pero este documento describe la cadena preferida.")
    L.append("")
    L.append("## Cadena de la solución preferida (resumen)")
    L.append("")
    L.append("```")
    L.append("event")
    L.append(" └─ m_preferredoriginid ──────► ORIGEN PREFERIDO (origin)")
    L.append("      ├─ (sus) arrival [_parent_oid] ─► pick usado (m_pickid)")
    L.append("      │     └─ pick.m_waveformid_stationcode/networkcode ─► QUÉ ESTACIÓN (station/network)")
    L.append("      ├─ (sus) amplitude [_parent_oid] ─► stationmagnitude (m_originid = este origin)")
    L.append("      └─ (sus) dataused / reading")
    L.append("event")
    L.append(" ├─ m_preferredmagnitudeid ──► magnitude (magnitud preferida)")
    L.append(" └─ eventdescription (m_type='region name') ─► nombre de la región")
    L.append("```")
    L.append("")
    L.append("## Leyenda de tipos")
    L.append("")
    L.append("- Todas las tablas de objetos tienen `_oid` (identidad, referencia a `object._oid`) "
             "y `_parent_oid` (pertenencia al padre).")
    L.append("- Los enlaces entre objetos se hacen por **coincidencia de `_oid`** o por "
             "**`m_publicid`/`m_*id`** (texto) — no siempre hay llave foránea declarada.")
    L.append("")
    for grupo, ts in GRUPOS:
        L.append(f"## {grupo}")
        L.append("")
        for t in ts:
            L.append(f"### {t}")
            L.append("")
            txt = ANEXO[t]["resumen"]
            if txt:
                L.append(f"{txt}")
                L.append("")
            cols = esquema[t]
            L.append("| Columna | Tipo |")
            L.append("| --- | --- |")
            for c, tipo in cols:
                L.append(f"| `{c}` | {tipo} |")
            L.append("")
            idx = indices.get(t, [])
            if idx:
                L.append("**Índices:**")
                L.append("")
                for name, definicion in idx:
                    corta = definicion.replace("CREATE INDEX ", "").replace("CREATE UNIQUE INDEX ", "ÚNICO ")
                    L.append(f"- `{name}` → `{corta}`")
                L.append("")
            # columnas que materializan la cadena preferida
            enlaces = [f"`{c}`" for c, tipo in cols
                       if c in ("m_preferredoriginid", "m_preferredmagnitudeid",
                                "m_pickid", "m_originid", "m_amplitudeid",
                                "m_waveformid_stationcode", "m_waveformid_networkcode")]
            if enlaces:
                L.append(f"_Enlaza la cadena preferida:_ " + ", ".join(enlaces))
                L.append("")
    L.append("## Relaciones clave (matriz)")
    L.append("")
    L.append("| De | Columna | Hacia | Nota | Cardinalidad |")
    L.append("| --- | --- | --- | --- | --- |")
    for o, co, d, cd, nota, res, cs, cdest in RELACIONES:
        marca = " ★" if res else ""
        L.append(f"| `{o}` | `{co}` | `{d}` | {nota}{marca} | {cs} : {cdest} |")
    L.append("")
    L.append("> ★ = relación de la **solución preferida**. En el diagrama, cada extremo del "
             "conector lleva un **símbolo** que indica cuántas filas de la tabla que toca "
             "participan en la relación: `1` = una, `N` = varias, `0..1` = cero o una "
             "(opcional), `0..N` = cero o varias. En esta tabla la cardinalidad se lee en el "
             "sentido De → Hacia (primera etiqueta = tabla De, segunda = Hacia).")
    L.append("")
    L.append("### Símbolos de cardinalidad")
    L.append("")
    L.append("| Símbolo | Significado |")
    L.append("| --- | --- |")
    L.append("| `1` | una fila de esa tabla participa en la relación |")
    L.append("| `N` | varias filas de esa tabla participan en la relación |")
    L.append("| `0..1` | cero o una (opcional) — como máximo una fila |")
    L.append("| `0..N` | cero o varias (opcional) |")
    L.append("")
    L.append("## Anexo — Descripción de cada tabla")
    L.append("")
    L.append("> **Contiene.** qué datos viven en la tabla. **Para qué se usa.** su rol dentro del "
             "esquema (especialmente en la cadena de la solución preferida). "
             "**Atributos.** columnas en orden, con las llaves en negrita "
             "(llave = PRIMARY KEY, única = UNIQUE).")
    L.append("")
    llaves = llaves_por_tabla(indices)
    for g, ts in GRUPOS:
        L.append(f"### {g}")
        L.append("")
        for t in ts:
            a = ANEXO[t]
            L.append(f"#### {t}")
            L.append("")
            L.append(f"- **Contiene.** {a['contenido']}")
            L.append(f"- **Para qué se usa.** {a['uso']}")
            L.append("")
            L.append("**Atributos:**")
            L.append("")
            L.append("| Nombre | Tipo de dato |")
            L.append("| --- | --- |")
            for c, tipo in esquema[t]:
                marca = llaves.get(t, {}).get(c)
                if marca:
                    L.append(f"| **`{c}`** ({marca}) | {tipo} |")
                else:
                    L.append(f"| `{c}` | {tipo} |")
            L.append("")
    return "\n".join(L)


def main():
    conn = conectar()
    esquema, indices = extraer_esquema(conn)
    conn.close()

    html = generar_html(esquema, indices)
    md = generar_md(esquema, indices)

    ruta_html = os.path.join(DOCS, "ESQUEMA_BD_SeisComp6.html")
    ruta_md = os.path.join(DOCS, "ESQUEMA_BD_SeisComp6.md")
    ruta_static = os.path.join(DOCS, "ESQUEMA_BD_SeisComp6.static.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)
    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write(md)
    # versión estática (mismo HTML; libreoffice lo convierte a ODT)
    with open(ruta_static, "w", encoding="utf-8") as f:
        f.write(html)

    print("Generado:", ruta_html)
    print("Generado:", ruta_md)
    print("Generado:", ruta_static)

    # ODT con LibreOffice (headless)
    try:
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "odt",
             "--outdir", DOCS, ruta_static],
            check=True, capture_output=True, timeout=120)
        odt = os.path.join(DOCS, "ESQUEMA_BD_SeisComp6.static.odt")
        destino = os.path.join(DOCS, "ESQUEMA_BD_SeisComp6.odt")
        if os.path.exists(odt):
            os.replace(odt, destino)
            print("Generado:", destino)
    except Exception as e:
        print("[Aviso] No se pudo generar el ODT con libreoffice:", e)


if __name__ == "__main__":
    main()