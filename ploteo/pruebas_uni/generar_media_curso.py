#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el material multimedia del curso de tests unitarios:
  - Capturas estilo terminal y paneles de código (PNG en /tmp/opencode/curso_build)
  - Diagramas (PNG)
  - Videos MP4 cortos (pruebas_uni/CURSO_MEDIA/)

Requiere: Pillow, matplotlib (python del sistema) y ffmpeg en /usr/bin.
Ejecutar: python3 pruebas_uni/generar_media_curso.py
"""
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

DIR = os.path.dirname(os.path.abspath(__file__))
BUILD = "/tmp/opencode/curso_build"
MEDIA = os.path.join(DIR, "CURSO_MEDIA")

W, H = 1120, 640            # lienzo fijo para todos los frames (ffmpeg lo exige)
PAD_X, PAD_Y = 24, 56       # margen interior bajo la barra de título

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONTS_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def fuente(size, bold=False):
    for p in (FONTS_BOLD if bold else FONTS):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------- colores ---
BG = "#0d1117"          # fondo terminal/editor
BAR = "#161b22"         # barra de título
FG = "#d8dee9"          # texto normal
GREEN = "#7ee787"       # PASSED / ok
RED = "#ff7b72"         # FAILED / ERROR
BLUE = "#79c0ff"        # prompt / strings
PURPLE = "#d2a8ff"      # keywords python
GRAY = "#8b949e"        # separadores / comentarios
ORANGE = "#ffa657"      # [NewPT] / títulos internos


def _color_linea(txt):
    t = txt.strip()
    low = txt.lower()
    if "passed" in low and "failed" not in low:
        return GREEN
    if "failed" in low or "error" in low or "detenida" in low:
        return RED
    if t.startswith("$"):
        return FG
    if t.startswith("#") or t.startswith("("):
        return GRAY
    return FG


KEYWORDS = ("def ", "import ", "from ", "return", "assert", "with ",
            "for ", "if ", "else", "None", "True", "False", "lambda")


def _draw_code_line(d, x, y, txt, fnt, fnt_bold):
    # comentario a fin de línea en gris
    code_part, com = txt, ""
    if "#" in txt and not txt.lstrip().startswith('"""'):
        idx = txt.index("#")
        code_part, com = txt[:idx], txt[idx:]
    # segmentos entre comillas en azul
    segs, buf, in_str, q = [], "", False, ""
    for ch in code_part:
        if in_str:
            buf += ch
            if ch == q:
                segs.append((buf, BLUE)); buf, in_str = "", False
        else:
            if ch in "\"'":
                if buf:
                    segs.append((buf, None))
                buf, in_str, q = ch, True, ch
            else:
                buf += ch
    if buf:
        segs.append((buf, None))
    cx = x
    for s, c in segs:
        col = c or FG
        if c is None and any(k in s for k in KEYWORDS):
            d.text((cx, y), s, font=fnt_bold, fill=PURPLE)
        else:
            d.text((cx, y), s, font=fnt, fill=col)
        cx += d.textlength(s, font=fnt)
    if com:
        d.text((cx, y), com, font=fnt, fill=GRAY)


def _canvas(titulo):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34], fill=BAR)
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        d.ellipse([16 + i * 22, 12, 28 + i * 22, 24], fill=c)
    f = fuente(14, True)
    tw = d.textlength(titulo, font=f)
    d.text(((W - tw) // 2, 9), titulo, font=f, fill=GRAY)
    return img, d


def render_terminal(lineas, out=None, titulo="terminal"):
    img, d = _canvas(titulo)
    fnt = fuente(17)
    fnt_b = fuente(17, True)
    y = PAD_Y
    for ln in lineas:
        if ln.startswith("$ "):
            d.text((PAD_X, y), "❯", font=fnt_b, fill=GREEN)
            cmd_x = PAD_X + 22
            d.text((cmd_x, y), ln[2:], font=fnt_b, fill="#e6edf3")
        else:
            d.text((PAD_X + 4, y), ln, font=fnt, fill=_color_linea(ln))
        y += 27
    if out:
        img.save(out)
    return img


def render_codigo(lineas, out=None, titulo="test_ejemplo.py"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34], fill=BAR)
    f14 = fuente(14, True)
    d.text((16, 9), "─ " + titulo, font=f14, fill=ORANGE)
    fnt = fuente(17)
    fnt_b = fuente(17, True)
    y = PAD_Y
    for i, ln in enumerate(lineas, 1):
        d.text((PAD_X, y), f"{i:>2}", font=fnt, fill="#3d4d5c")
        _draw_code_line(d, PAD_X + 44, y, ln, fnt, fnt_b)
        y += 27
    if out:
        img.save(out)
    return img


def apilar(imagenes, out):
    """Varias imágenes una debajo de otra dentro del lienzo fijo."""
    base = Image.new("RGB", (W, H * len(imagenes)), BG)
    y = 0
    for im in imagenes:
        base.paste(im, (0, y))
        y += H
    base.save(out)


def escalar_a_lienzo(png):
    im = Image.open(png).convert("RGB")
    if im.size != (W, H):
        fondo = Image.new("RGB", (W, H), BG)
        fondo.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
        fondo.save(png)


def video(nombre, frames_dir, fps=1.4):
    out = os.path.join(MEDIA, nombre + ".mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-framerate", str(fps), "-i", os.path.join(frames_dir, "f%03d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", out],
        check=True)
    print("  video:", out)


def frames(nombre, imagenes):
    fd = os.path.join(BUILD, nombre)
    os.makedirs(fd, exist_ok=True)
    for i, im in enumerate(imagenes, 1):
        im.save(os.path.join(fd, f"f{i:03d}.png"))
    video(nombre, fd)


# ------------------------------------------------------------- diagramas ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "DejaVu Sans"


def _nueva_fig(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=110)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis("off")
    fig.patch.set_facecolor("#0d1117")
    return fig, ax


def _caja(ax, x, y, w, h, texto, fc, ec, fs=13, tc="#0d1117"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.15", fc=fc, ec=ec, lw=1.6))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center",
            fontsize=fs, color=tc, weight="bold")


def _flecha(ax, x1, y1, x2, y2, color="#d8dee9"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                 arrowstyle="-|>", mutation_scale=18, color=color, lw=1.8))


def diag_AAA(out):
    fig, ax = _nueva_fig(10, 3.6)
    ax.text(5, 9.3, "El ciclo AAA de un test", ha="center", fontsize=15,
            color="#e6edf3", weight="bold")
    _caja(ax, 0.4, 3.4, 2.7, 2.6, "PREPARAR\n(Arrange)\n\ndatos de entrada\ny escenario", "#79c0ff", "#79c0ff", 11)
    _caja(ax, 3.7, 3.4, 2.7, 2.6, "ACTUAR\n(Act)\n\nejecutar la función\nbajo prueba", "#7ee787", "#7ee787", 11)
    _caja(ax, 7.0, 3.4, 2.7, 2.6, "VERIFICAR\n(Assert)\n\n¿el resultado es\nel esperado?", "#ffa657", "#ffa657", 11)
    _flecha(ax, 3.15, 4.7, 3.65, 4.7)
    _flecha(ax, 6.45, 4.7, 6.95, 4.7)
    fig.savefig(out, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def diag_mock(out):
    fig, ax = _nueva_fig(10, 3.8)
    ax.text(5, 9.3, "Simular (mock) una dependencia lenta o ajena a ti",
            ha="center", fontsize=15, color="#e6edf3", weight="bold")
    _caja(ax, 0.3, 4.2, 2.0, 2.2, "TEST", "#7ee787", "#7ee787")
    _caja(ax, 3.1, 4.2, 2.4, 2.2, "consulta_\nevento()", "#d8dee9", "#d8dee9", 12)
    _caja(ax, 6.6, 6.3, 3.0, 1.7, "PostgreSQL real\n✗ nunca en unit tests", "#3d1d20", "#ff7b72", 11, tc="#ff7b72")
    _caja(ax, 6.6, 2.6, 3.0, 1.7, "BD fingida (mock)\n✓ rápida y controlada", "#1d2d20", "#7ee787", 11, tc="#7ee787")
    _flecha(ax, 2.35, 5.3, 3.05, 5.3)
    _flecha(ax, 5.55, 5.75, 6.55, 6.9, "#ff7b72")
    ax.text(5.6, 6.55, "se REEMPLAZA por", fontsize=10, color="#ff7b72")
    _flecha(ax, 5.55, 4.9, 6.55, 3.7, "#7ee787")
    ax.text(5.6, 3.85, "durante el test", fontsize=10, color="#7ee787")
    fig.savefig(out, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def diag_flujo(out):
    fig, ax = _nueva_fig(10, 4.4)
    ax.text(5, 9.4, "La marcha blanca dentro de instalar_newpt.sh",
            ha="center", fontsize=15, color="#e6edf3", weight="bold")
    _caja(ax, 0.2, 5.6, 2.3, 2.0, "./instalar_newpt.sh\n(--probar o paso 4b)", "#79c0ff", "#79c0ff", 10)
    _caja(ax, 3.0, 5.6, 2.3, 2.0, "venv temporal +\npip versiones fijas", "#d8dee9", "#d8dee9", 10)
    _caja(ax, 5.8, 5.6, 2.1, 2.0, "pytest\nfuentes/pruebas", "#7ee787", "#7ee787", 11)
    _caja(ax, 8.3, 5.6, 1.6, 2.0, "¿todo\nPASSED?", "#ffa657", "#ffa657", 11)
    _caja(ax, 6.4, 1.2, 2.4, 1.8, "compila los\nbinarios ✓", "#1d2d20", "#7ee787", 11, tc="#7ee787")
    _caja(ax, 1.6, 1.2, 3.0, 1.8, "INSTALACIÓN DETENIDA\n✗ exit 1", "#3d1d20", "#ff7b72", 11, tc="#ff7b72")
    _flecha(ax, 2.55, 6.6, 2.95, 6.6)
    _flecha(ax, 5.35, 6.6, 5.75, 6.6)
    _flecha(ax, 7.95, 6.6, 8.25, 6.6)
    _flecha(ax, 9.1, 5.5, 8.8, 3.05, "#7ee787")
    ax.text(9.25, 4.3, "sí", fontsize=12, color="#7ee787", weight="bold")
    _flecha(ax, 8.45, 5.45, 3.15, 3.1, "#ff7b72")
    ax.text(5.0, 4.55, "no: muestra el test que falló", fontsize=10.5,
            color="#ff7b72")
    fig.savefig(out, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def diag_anatomia(out):
    fig, ax = _nueva_fig(10, 4.2)
    ax.text(5, 9.4, "Anatomía de un test pytest", ha="center", fontsize=15,
            color="#e6edf3", weight="bold")
    codigo = (
        "def test_medio_avance():            ← nombre: empieza con test_\n"
        '    """50% de avance dibuja 10 bloques."""   ← docstring (qué protege)\n'
        "    salida = capturar()             ← PREPARAR / ACTUAR\n"
        "    assert salida == esperado       ← VERIFICAR (el corazón)")
    ax.text(0.3, 6.6, codigo, fontsize=12.5, family="monospace", color="#e6edf3",
            va="top", linespacing=1.9)
    notas = [
        (7.9, "pytest solo ejecuta\nfunciones test_*", "#79c0ff"),
        (6.05, "documentación viva:\nexplica el propósito", "#8b949e"),
        (4.2, "llama al código REAL\ndel proyecto", "#7ee787"),
        (2.35, "si es False → FAIL\ncon explicación clara", "#ff7b72"),
    ]
    for y, t, c in notas:
        ax.annotate(t, xy=(8.6, y + 1.15), xytext=(9.0, y - 0.4),
                    fontsize=9.5, color=c, ha="left", va="top",
                    arrowprops=dict(arrowstyle="->", color=c, lw=1.4))
    ax.set_xlim(0, 13)
    fig.savefig(out, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


# ------------------------------------------------------------------ main ----
def main():
    if shutil.which("ffmpeg") is None:
        sys.exit("[ERROR] ffmpeg no está en /usr/bin")
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(MEDIA, exist_ok=True)

    # ---------- diagramas ----------
    diag_AAA(os.path.join(BUILD, "g_AAA.png"))
    diag_mock(os.path.join(BUILD, "g_mock.png"))
    diag_flujo(os.path.join(BUILD, "g_flujo.png"))
    diag_anatomia(os.path.join(BUILD, "g_anatomia.png"))
    for g in ("g_AAA", "g_mock", "g_flujo", "g_anatomia"):
        escalar_a_lienzo(os.path.join(BUILD, g + ".png"))
    print("diagramas OK")

    PASADOS = [
        "test_capturar.py::TestDistancias::test_a1_distancia_mismo_punto_es_cero PASSED [  4%]",
        "test_capturar.py::TestDistancias::test_a2_distancia_santiago_valparaiso PASSED [  8%]",
        "test_capturar.py::TestParsear::test_a9_linea_valida_completa PASSED [ 12%]",
        "test_consulta.py::TestFormato::test_b1_formato_19_campos PASSED [ 36%]",
    ]

    # ---------- V1: correr la suite ----------
    v1 = []
    v1.append(render_terminal(["$ cd ploteo", ""], "/tmp/x.png"))
    v1.append(render_terminal(
        ["$ python3 -m pytest fuentes/pruebas -v", "",
         "===================== test session starts =====================",
         "platform linux -- Python 3.12.3, pytest-9.1.1",
         "collected 25 items", ""], "/tmp/x.png"))
    v1.append(render_terminal(PASADOS, "/tmp/x.png"))
    v1.append(render_terminal(
        ["test_consulta.py::TestComportamiento::test_b5 PASSED [ 68%]",
         "test_datos.py::TestPerfiles::test_c1_pares_consistentes PASSED [ 80%]",
         "test_datos.py::TestRelieveYGrillas::test_c5_tif_presente PASSED [ 96%]"],
        "/tmp/x.png"))
    v1.append(render_terminal(
        ["==================== 25 passed in 0.81s ===================="],
        "/tmp/x.png"))
    v1.append(render_terminal(
        ["$ echo $?", "0", "", "# cero = la marcha blanca quedó SUPERADA"],
        "/tmp/x.png"))
    frames("v1", v1)

    # ---------- V2: primer test paso a paso ----------
    cod_vacio = render_codigo(["# (archivo vacío: aquí nacerá tu primer test)"],
                              "/tmp/x.png", "pruebas_uni/IA_pruebas/test_avance.py")
    cod_1 = render_codigo(["import capturar"], "/tmp/x.png", "pruebas_uni/IA_pruebas/test_avance.py")
    cod_2 = render_codigo(
        ["import capturar", "",
         "def test_medio_avance():"],
        "/tmp/x.png", "pruebas_uni/IA_pruebas/test_avance.py")
    cod_3 = render_codigo(
        ["import capturar", "",
         "def test_medio_avance():",
         '    """Con paso=50 y total=100 se dibuja 50%."""',
         "    capturar.mostrar_avance(50, 100, 'cargando')",
         "    fuera = captura_salida()",
         "    assert '50%' in fuera",
         "    assert '█' * 10 in fuera"],
        "/tmp/x.png", "pruebas_uni/IA_pruebas/test_avance.py")
    v2 = [cod_vacio, cod_1, cod_2, cod_3,
          render_terminal(["$ python3 -m pytest pruebas_uni/IA_pruebas/test_avance.py -v", ""],
                          "/tmp/x.png"),
          render_terminal(["collected 1 item", "",
                           "test_avance.py::test_medio_avance PASSED [100%]"],
                          "/tmp/x.png"),
          render_terminal(["==================== 1 passed ====================", "",
                           "# ¡Tu primer test está vivo!"], "/tmp/x.png")]
    frames("v2", v2)

    # ---------- V3: leer un traceback ----------
    fallo = render_codigo(
        ["import capturar", "",
         "def test_porcentaje_correcto():",
         "    capturar.mostrar_avance(25, 100, 'x')",
         "    fuera = captura_salida()",
         "    assert '25%' in fuera     # 25 de 100 → ¿25%?",
         "    assert '50%' in fuera     # ¡UPS! esto no puede pasar"],
        "/tmp/x.png", "pruebas_uni/IA_pruebas/test_fallo.py")
    v3 = [fallo,
          render_terminal(["$ python3 -m pytest pruebas_uni/IA_pruebas/test_fallo.py -v", "",
                           "test_fallo.py::test_porcentaje_correcto FAILED [100%]"],
                          "/tmp/x.png"),
          render_terminal(
              ["=================================== FAILURES ===================================",
               "________________________________ test_porcentaje _______________________________",
               ">       assert '50%' in fuera",
               "E       AssertionError: assert '50%' in '[NewPT] |█████-----| 25% - x'",
               "E        +  donde '50%' no aparece en el avance real (25%)",
               "=========================== short summary ============================",
               "FAILED pruebas_uni/IA_pruebas/test_fallo.py::test_porcentaje_correcto - AssertionError"],
              "/tmp/x.png"),
          render_terminal(
              ["# Lectura: pytest te dice QUÉ assert falló y QUÉ valor real había.",
               "# El test estaba mal escrito (exigía 50% con datos de 25%). Se corrige:",
               "$ nano pruebas_uni/IA_pruebas/test_fallo.py"],
              "/tmp/x.png"),
          render_codigo(
              ["import capturar", "",
               "def test_porcentaje_correcto():",
               "    capturar.mostrar_avance(25, 100, 'x')",
               "    fuera = captura_salida()",
               "    assert '25%' in fuera     # corregido"],
              "/tmp/x.png", "pruebas_uni/IA_pruebas/test_fallo.py"),
          render_terminal(["$ python3 -m pytest pruebas_uni/IA_pruebas/test_fallo.py -v", "",
                           "test_fallo.py::test_porcentaje_correcto PASSED [100%]",
                           "1 passed"], "/tmp/x.png")]
    frames("v3", v3)

    # ---------- V4: black ----------
    feo = render_codigo(
        ["import capturar", "",
         "def calculo_raro( a,b ):",
         "   resultado=a+b*2",
         "  return    resultado"],
        "/tmp/x.png", "antes de black")
    bello = render_codigo(
        ["import capturar", "",
         "",
         "def calculo_raro(a, b):",
         "    resultado = a + b * 2",
         "    return resultado"],
        "/tmp/x.png", "después de black")
    v4 = [feo,
          render_terminal(["$ black pruebas_uni/IA_pruebas/", "",
                           "reformatted pruebas_uni/IA_pruebas/test_demo.py",
                           "All done! ✨  1 file reformatted."],
                          "/tmp/x.png"),
          bello,
          render_terminal(["$ black --check fuentes/pruebas/",
                           "would reformat fuentes/pruebas/test_demo.py",
                           "1 file would be reformatted."],
                          "/tmp/x.png")]
    frames("v4", v4)

    # ---------- V5: mock ----------
    gm = Image.open(os.path.join(BUILD, "g_mock.png")).convert("RGB")
    v5 = [gm.copy(),
          render_codigo(
              ["import consulta_evento", "",
               "def test_bd_simulada(monkeypatch):",
               "    cursor_falso = FakeCursor([FILA_ORIGEN])",
               "    def connect_falso(*a, **k):",
               "        return FakeConexion(cursor_falso)",
               "    monkeypatch.setattr(",
               "        'psycopg2.connect', connect_falso)",
               "    consulta_evento.consultar_por_fecha_creacion('csn_sc62026')"],
              "/tmp/x.png", "sin tocar la red ni PostgreSQL"),
          render_codigo(
              ["    with open(ruta_tmp()) as f:",
               "        linea = f.readline().split(';')",
               "    assert len(linea) == 19      # el contrato se cumple igual",
               "    assert linea[8] == '35.42 S'"],
              "/tmp/x.png", "…y verificamos el resultado como siempre"),
          render_terminal(["$ python3 -m pytest pruebas_uni -v", "",
                           "25 passed in 0.81s"], "/tmp/x.png")]
    frames("v5", v5)

    # ---------- capturas estáticas para el docx ----------
    apilar([v1[2], v1[4]], os.path.join(BUILD, "s_suite.png"))
    apilar([v3[1], v3[2]], os.path.join(BUILD, "s_fail.png"))
    apilar([v4[0], v4[2]], os.path.join(BUILD, "s_black.png"))

    ut = render_codigo(
        ["class TestRumbo(unittest.TestCase):",
         "    def test_norte(self):",
         "        self.assertEqual(obtener_rumbo(0, 0, 0, 10), 'N')"],
        "/tmp/x.png", "estilo unittest (tus suites actuales)")
    pq = render_codigo(
        ["def test_norte():",
         "    assert obtener_rumbo(0, 0, 0, 10) == 'N'"],
        "/tmp/x.png", "estilo pytest (los tuyos)")
    lado = Image.new("RGB", (W * 2, H), BG)
    lado.paste(ut, (0, 0)); lado.paste(pq, (W, 0))
    lado.save(os.path.join(BUILD, "s_estilos.png"))

    render_codigo(
        ["def test_profundidad_invalida_da_default():",
         "    linea = parsear_linea_evento(LINEA_CON_PROF_CORRUPTA)",
         "    assert linea['prof'] == 10        # valor por defecto",
         "",
         "def test_id_inexistente_no_escribe():",
         "    consultar(None)",
         "    assert not os.path.exists(ruta_tmp())",
         "",
         "with pytest.raises(ValueError):",
         "    parsear_linea_evento('basura sin campos')"],
        "/tmp/x.png", "aserciones frecuentes").save(
            os.path.join(BUILD, "s_asserts.png"))

    render_codigo(
        ["class BaseConsulta(unittest.TestCase):          # TU suite B real",
         "    def setUp(self):                            # antes de CADA test",
         "        self.tmp = tempfile.mkdtemp(prefix='newpt_test_')",
         "        os.environ['NEWPT_DATA_DIR'] = self.tmp",
         "",
         "    def tearDown(self):                         # después de CADA test",
         "        restaurar_entorno()",
         "",
         "# equivalente pytest: fixture reutilizable",
         "@pytest.fixture",
         "def tmp_datos(tmp_path, monkeypatch):",
         "    monkeypatch.setenv('NEWPT_DATA_DIR', str(tmp_path))",
         "    return tmp_path"],
        "/tmp/x.png", "fixtures: preparar y limpiar el escenario").save(
            os.path.join(BUILD, "s_fixtures.png"))

    render_codigo(
        ["def test_mostrar_avance(capsys):                # capsys = stdout capturado",
         "    capturar.mostrar_avance(50, 100, 'leyendo grillas')",
         "    fuera = capsys.readouterr().out",
         "    assert '50%' in fuera and '█' * 10 in fuera"],
        "/tmp/x.png", "L1 · mostrar_avance() — pista principal").save(
            os.path.join(BUILD, "s_l1.png"))

    render_codigo(
        ["def test_contar_lineas(tmp_path):",
         "    f = tmp_path / 'mini.xyz'",
         "    f.write_text('lon lat\\n1 2\\n3 4\\n')",
         "    assert preprocesa_grillas.contar_lineas(str(f)) == 3",
         "",
         "def test_contar_lineas_archivo_inexistente(tmp_path):",
         "    with pytest.raises(OSError):",
         "        preprocesa_grillas.contar_lineas(str(tmp_path / 'no.txt'))"],
        "/tmp/x.png", "L2 · contar_lineas() — pista principal").save(
            os.path.join(BUILD, "s_l2.png"))

    print("capturas OK")
    print("Listo. Assets en:", BUILD, "y videos en:", MEDIA)


if __name__ == "__main__":
    main()
