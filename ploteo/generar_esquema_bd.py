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

# Descripción breve de cada grupo para la leyenda del diagrama.
TEXTOS = {
    "object": "Raíz común de todos los objetos (identidad _oid).",
    "publicobject": "Extiende object: añade m_publicid, el ID público (único).",
    "event": "El sismo agregado. m_preferredoriginid apunta al ORIGEN PREFERIDO.",
    "origin": "Una solución de hipocentro (la preferida es la que analiza el analista).",
    "magnitude": "Magnitud preferida del evento (m_linkea por publicid).",
    "eventdescription": "Descripciones textuales (m_type='region name' = región).",
    "originreference": "Contexto: lista todos los orígenes asociados al evento.",
    "arrival": "Llegada de una fase usada para localizar; enlaza el pick usado.",
    "pick": "Detección de una fase en un canal: dice EN QUÉ ESTACIÓN.",
    "amplitude": "Amplitud medida sobre un pick.",
    "stationmagnitude": "Magnitud calculada por estación.",
    "stationmagnitudecontribution": "Contribución de cada estación a la magnitud.",
    "dataused": "Fases/datos usados en la localización.",
    "reading": "Lecturas asociadas (auxiliar).",
    "network": "Red sismológica (padre del inventario).",
    "station": "Estación: lat/lon/elev, a la que apunta pick.m_waveformid_stationcode.",
    "sensorlocation": "Emplazamiento de la estación.",
    "stream": "Canal (stream) del emplazamiento.",
}

# Relaciones que se dibujan en el diagrama.
# (tabla_origen, columna_origen, tabla_destino, columna_destino, nota, resaltada)
RELACIONES = [
    ("object", "_oid", "publicobject", "_oid", "publicobject._oid = object._oid", False),
    ("publicobject", "_oid", "origin", "_oid", "origin._oid = publicobject._oid", False),
    ("publicobject", "_oid", "event", "_oid", "event._oid = publicobject._oid", False),
    ("publicobject", "_oid", "magnitude", "_oid", "magnitude._oid = publicobject._oid", False),
    ("publicobject", "_oid", "pick", "_oid", "pick._oid = publicobject._oid", False),
    ("event", "m_preferredoriginid", "origin", "m_publicid", "ORIGEN PREFERIDO", True),
    ("event", "m_preferredmagnitudeid", "magnitude", "m_publicid", "magnitud preferida", True),
    ("event", "_oid", "eventdescription", "_parent_oid", "eventdescription._parent_oid = event._oid", False),
    ("event", "_oid", "originreference", "_parent_oid", "origenes del evento", False),
    ("originreference", "m_originid", "origin", "m_publicid", "un origen alternativo", False),
    ("origin", "_oid", "arrival", "_parent_oid", "llegadas del origen", True),
    ("arrival", "m_pickid", "pick", "m_publicid", "pick usado", True),
    ("pick", "m_waveformid_stationcode", "station", "m_code", "qué estación", True),
    ("origin", "_oid", "amplitude", "_parent_oid", "amplitudes del origen", False),
    ("amplitude", "m_pickid", "pick", "m_publicid", "sobre ese pick", False),
    ("origin", "m_publicid", "stationmagnitude", "m_originid", "magnitud por estación", True),
    ("stationmagnitude", "m_amplitudeid", "amplitude", "m_publicid", "usa esa amplitud", False),
    ("magnitude", "_oid", "stationmagnitudecontribution", "_parent_oid", "contribuciones", False),
    ("stationmagnitudecontribution", "m_stationmagnitudeid", "stationmagnitude", "m_publicid", "de cada estación", False),
    ("origin", "_oid", "dataused", "_parent_oid", "datos usados", False),
    ("pick", "_oid", "reading", "_parent_oid", "lecturas del pick", False),
    ("network", "_oid", "station", "_parent_oid", "st. pertenece a la red", False),
    ("station", "_oid", "sensorlocation", "_parent_oid", "emplazamientos", False),
    ("sensorlocation", "_oid", "stream", "_parent_oid", "canales (streams)", False),
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
            y += altos[t] + 34
    ancho_total = (max_ancho + 90) * 4 + 60
    alto_total = 0
    for g, yg in y_grupo.items():
        for t, y in yg:
            alto_total = max(alto_total, y + altos[t] + 60)
    return pos, y_grupo, ancho_total, alto_total


def esc_xml(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def caja_svg(t, x, y, w, h, color_titulo, color_fondo, resaltada):
    cols = CLAVE[t]
    stroke = "#e05c00" if resaltada else "#5f6b7a"
    ancho_stroke = "2.5" if resaltada else "1.5"
    lines = ["<g>"]
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

    # flechas
    flechas = []
    import math
    marcadores = {}
    for o, co, d, cd, nota, res in RELACIONES:
        color = "#e05c00" if res else "#8a97a6"
        sw = 2.5 if res else 1.5
        x1, y1, w1, h1 = pos[o]
        x2, y2, w2, h2 = pos[d]
        sx, sy = punto_borde(x1, y1, w1, h1, x2 + w2 / 2, y2 + h2 / 2)
        tx, ty = punto_borde(x2, y2, w2, h2, x1 + w1 / 2, y1 + h1 / 2)
        dx, dy = tx - sx, ty - sy
        largo = math.hypot(dx, dy) or 1
        ux, uy = dx / largo, dy / largo
        xf, yf = sx + ux * (largo - 8), sy + uy * (largo - 8)
        mid = f"{color[1:]}"
        marcadores[mid] = color
        flechas.append(
            f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{xf:.0f}" y2="{yf:.0f}" '
            f'stroke="{color}" stroke-width="{sw}" marker-end="url(#arr{mid})"/>')
        mx, my = (sx + tx) / 2, (sy + ty) / 2
        flechas.append(
            f'<text x="{mx:.0f}" y="{my - 3:.0f}" text-anchor="middle" '
            f'font-family="Arial" font-size="8.5" fill="{color}" '
            f'paint-order="stroke" stroke="#ffffff" stroke-width="3">{esc_xml(nota)}</text>')

    defs = "\n".join(
        f'<marker id="arr{k}" viewBox="0 0 10 10" refX="8" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for k, c in marcadores.items())
    if not defs:
        defs = f'<marker id="arr8a97a6" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#8a97a6"/></marker>'

    resaltadas = set()
    for o, co, d, cd, n, r in RELACIONES:
        if r:
            resaltadas.add(o)
            resaltadas.add(d)

    cajas = []
    for t in TABLAS:
        x, y, w, h = pos[t]
        ct, cf = colores[grupo_de_tabla[t]]
        res = t in resaltadas
        cajas.append(caja_svg(t, x, y, w, h, ct, cf, res))

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

    svg = (
        f'<svg id="esquemaSvg" width="{ancho_total}" height="{alto_total}" '
        f'viewBox="0 0 {ancho_total} {alto_total}" '
        f'xmlns="http://www.w3.org/2000/svg" style="background:#fbfcfe">'
        f'<defs>{defs}</defs>'
        + "\n".join(grupos_svg)
        + "\n".join(flechas)
        + "\n".join(cajas)
        + "</svg>"
    )

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
 .chip {{ display:inline-block; width:12px; height:12px; border-radius:3px;
         margin-right:4px; vertical-align:middle; }}
</style>
</head>
<body>
<div id="barra">
  <b>Esquema BD SeisComp6</b>
  <span style="color:#cbd5e1">rueda del ratón = zoom · arrastrar = mover · tocar "Restablecer" para volver</span>
  <span style="flex:1"></span>
  <button onclick="zoomBy(1.3)">+</button>
  <button onclick="zoomBy(0.77)">−</button>
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
  <span style="color:#e05c00"><b>Flechas naranjas:</b> cadena preferida · <b>grises:</b> resto de relaciones</span>
  <span>Las flechas llevan la columna que materializa el enlace.</span>
</div>
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
            txt = TEXTOS.get(t, "")
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
    L.append("| De | Columna | Hacia | Nota |")
    L.append("| --- | --- | --- | --- |")
    for o, co, d, cd, nota, res in RELACIONES:
        marca = " ★" if res else ""
        L.append(f"| `{o}` | `{co}` | `{d}` | {nota}{marca} |")
    L.append("")
    L.append("> ★ = relación de la **solución preferida**.")
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