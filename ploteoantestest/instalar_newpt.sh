#!/bin/bash
# =============================================================================
# instalar_newpt.sh - Instalador genérico de NewPT
# -----------------------------------------------------------------------------
# Corre como USUARIO NORMAL (sin permisos de super usuario). Compila los scripts
# a binarios con PyInstaller dentro de un venv y deja una instalación autocontenida
# en ~/newpt (o en la carpeta indicada como primer argumento).
#
# USO:
#   ./instalar_newpt.sh [DIR_INSTALACION]
#   ./instalar_newpt.sh --solo-verificar        # solo comprueba prerequisitos
#   ./instalar_newpt.sh --ayuda
#   PYTHON_INTERPRETER=/usr/bin/python3 ./instalar_newpt.sh   # forzar intérprete
#
# REQUIERE que junto a este script existan:
#   fuentes/   -> capturar.py, consulta_evento.py, consuta_evento_sc7.py
#   datos/     -> grillas/, NE2_LR_LC_SR_W_DR.tif, base_2023_2026.dat, localidades.csv
#   newpt.sh.tpl
# (Ese contenido lo genera crear_instalador.sh en la máquina de desarrollo.)
# =============================================================================

set -euo pipefail

SOLO_VERIFICAR=0
DIR_INSTALACION="${HOME}/newpt"

for arg in "$@"; do
    case "$arg" in
        --solo-verificar) SOLO_VERIFICAR=1 ;;
        --ayuda|-h)
            echo "USO: $0 [DIR_INSTALACION] [--solo-verificar] [--ayuda]"
            exit 0
            ;;
        *) DIR_INSTALACION="$arg" ;;
    esac
done

ESCENARIO_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
FUENTES_DIR="$ESCENARIO_DIR/fuentes"
DATOS_DIR_SRC="$ESCENARIO_DIR/datos"
TPL="$ESCENARIO_DIR/newpt.sh.tpl"

echo "============================================================"
echo "  INSTALADOR NEWPT"
echo "============================================================"
echo "Carpeta de instalación : $DIR_INSTALACION"

# -----------------------------------------------------------------------------
# 1. VERIFICACIÓN DE PREREQUISITOS
# -----------------------------------------------------------------------------
# Cada prerequisito se muestra SIEMPRE por pantalla con su estado:
#   [OK]              -> está instalado, se puede continuar
#   [DEBE INSTALARSE] -> falta; el encargado de TI debe instalarlo.
# Si hay al menos uno en estado [DEBE INSTALARSE] la instalación se DETIENE
# (no se continúa bajo ningún concepto) y se informa al usuario por terminal.

echo ""
echo "==> Verificando prerequisitos..."
echo "    (programas del sistema: responsabilidad del encargado de TI)"
echo ""

FALTA=0
PREREQS_FALTANTES=()

ok()       { printf '    [OK]              %s\n' "$1"; }
instalar() { printf '    [DEBE INSTALARSE] %s\n' "$1"; PREREQS_FALTANTES+=("$1"); FALTA=1; }

comprobar() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        ok "$desc"
    else
        instalar "$desc"
    fi
}

# --- Selección del intérprete de Python con librería compartida ---
# PyInstaller necesita libpython*.so para generar binarios. La tiene el Python
# del sistema (apt). Si "python3" es un Python compilado a mano sin
# --enable-shared (o de pyenv/conda/etc.), se busca automáticamente otro
# intérprete del sistema que sí sirva. Se puede forzar con:
#   PYTHON_INTERPRETER=/usr/bin/python3 ./instalar_newpt.sh ...
tiene_libpython() {
    local interp="$1" bin ver libdir ruta
    bin="$(command -v "$interp" 2>/dev/null)" || return 1
    bin="$(readlink -f "$bin")"
    ver="$("$bin" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)" || return 1
    libdir="$("$bin" -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR") or "")' 2>/dev/null)"
    if [ -n "$libdir" ] && ls "$libdir"/libpython${ver}*.so* >/dev/null 2>&1; then
        return 0
    fi
    ruta="$("$bin" -c 'import sys; print(sys.executable)' 2>/dev/null)"
    [ -n "$ruta" ] && ls "$(dirname "$ruta")"/../lib/libpython${ver}*.so* >/dev/null 2>&1
}

elegir_python() {
    local c
    if command -v "$PYTHON" >/dev/null 2>&1 && tiene_libpython "$PYTHON"; then
        return 0
    fi
    if [ -n "${PYTHON_INTERPRETER:-}" ]; then
        echo "    [AVISO] '$PYTHON' no tiene libpython*.so. Buscando otro..."
    else
        echo "    [AVISO] 'python3' no tiene libpython*.so (Python sin --enable-shared o similar)."
        echo "            Buscando un intérprete del sistema que sirva..."
    fi
    PYTHON=""
    for c in /usr/bin/python3.12 /usr/bin/python3.11 /usr/bin/python3.10 /usr/bin/python3.9 /usr/bin/python3.8 /usr/bin/python3.13 /usr/bin/python3; do
        if [ -x "$c" ] && tiene_libpython "$c"; then
            PYTHON="$c"
            return 0
        fi
    done
    return 1
}

PYTHON="${PYTHON_INTERPRETER:-python3}"

if elegir_python; then
    ok "Python con libpython compartida: $("$PYTHON" -V 2>&1) ($(command -v "$PYTHON"))"
else
    instalar "Python 3 del sistema con libpython*.so (paquetes python3 / python3-dev)"
    echo ""
    echo "============================================================"
    echo "[ERROR] No se encontró ningún Python con libpython*.so."
    echo ""
    echo "  Causa habitual: Python compilado a mano sin --enable-shared,"
    echo "  o un gestor de versiones (pyenv, conda, etc.)."
    echo ""
    echo "  Soluciones:"
    echo "    - Usar el Python del sistema (apt):"
    echo "          PYTHON_INTERPRETER=/usr/bin/python3 $0 $DIR_INSTALACION"
    echo "    - Instalar python3-dev (provee libpython*.so) y reintentar."
    echo "============================================================"
    exit 1
fi

comprobar "Módulo venv para crear el ambiente virtual (paquete python3-venv)" \
    bash -c "$PYTHON -m venv --help >/dev/null 2>&1"
comprobar "Terminal xterm para la ventana de progreso (paquete xterm)" \
    command -v xterm
comprobar "Tkinter para la ventana gráfica de matplotlib (paquete python3-tk)" \
    bash -c "$PYTHON -c 'import tkinter'"

echo ""
echo "    ------------------------------------------------------------"
if [ "$FALTA" -ne 0 ]; then
    echo "    RESUMEN DE PREREQUISITOS DEL SISTEMA:"
    echo "      Deben ser instalados por el encargado de TI:"
    for f in "${PREREQS_FALTANTES[@]}"; do
        echo "        * $f"
    done
    echo "    ------------------------------------------------------------"
    echo ""
    echo "============================================================"
    echo "  INSTALACIÓN DETENIDA: hay prerequisitos sin instalar."
    echo ""
    echo "  El encargado de TI debe instalar los programas faltantes"
    echo "  del sistema (una sola vez, con sudo):"
    echo ""
    echo "      sudo apt update"
    echo "      sudo apt install -y python3 python3-venv python3-tk xterm"
    echo ""
    echo "  La instalación NO continuará hasta que todos los"
    echo "  prerequisitos estén instalados. Una vez instalados,"
    echo "  vuelva a ejecutar este instalador."
    echo ""
    echo "  Nota: NINGÚN módulo de Python se instala en el sistema;"
    echo "  todo va dentro del venv de esta instalación."
    echo "============================================================"
    exit 1
fi

echo "    RESUMEN DE PREREQUISITOS DEL SISTEMA: todo OK."
echo "    ------------------------------------------------------------"
echo ""
echo "==> Prerequisitos completos: continuando con la instalación..."

if [ "$SOLO_VERIFICAR" -eq 1 ]; then
    echo ""
    echo "Todos los prerequisitos están disponibles. Ejecuta:"
    echo "    $0 $DIR_INSTALACION"
    exit 0
fi

# -----------------------------------------------------------------------------
# 2. VALIDACIÓN DE LOS COMPONENTES A INSTALAR
# -----------------------------------------------------------------------------
echo ""
echo "==> Validando componentes del instalador..."
[ -d "$FUENTES_DIR" ]       || { echo "[ERROR] No existe $FUENTES_DIR"; exit 1; }
[ -d "$DATOS_DIR_SRC" ]     || { echo "[ERROR] No existe $DATOS_DIR_SRC"; exit 1; }
[ -f "$TPL" ]               || { echo "[ERROR] No existe $TPL"; exit 1; }
[ -f "$FUENTES_DIR/capturar.py" ]        || { echo "[ERROR] Falta fuentes/capturar.py"; exit 1; }
[ -f "$FUENTES_DIR/consulta_evento.py" ] || { echo "[ERROR] Falta fuentes/consulta_evento.py"; exit 1; }
[ -f "$DATOS_DIR_SRC/NE2_LR_LC_SR_W_DR.tif" ] || { echo "[ERROR] Falta datos/NE2_LR_LC_SR_W_DR.tif"; exit 1; }
[ -f "$DATOS_DIR_SRC/base_2023_2026.dat" ]   || { echo "[ERROR] Falta datos/base_2023_2026.dat"; exit 1; }
[ -f "$DATOS_DIR_SRC/localidades.csv" ]      || { echo "[ERROR] Falta datos/localidades.csv"; exit 1; }
[ -d "$DATOS_DIR_SRC/grillas" ]              || { echo "[ERROR] Falta datos/grillas"; exit 1; }
echo "    Componentes OK."

# -----------------------------------------------------------------------------
# 3. CREACIÓN DE LA ESTRUCTURA
# -----------------------------------------------------------------------------
echo ""
echo "==> Creando estructura en $DIR_INSTALACION"
mkdir -p "$DIR_INSTALACION"
DIR_INSTALACION="$(cd "$DIR_INSTALACION" && pwd)"

# Si ya existe una instalación previa de NewPT aquí, se reconstruye limpio.
# No se tocan archivos del usuario fuera de .dev/ y bin/ (los datos se recopian encima).
if [ -e "$DIR_INSTALACION/newpt.sh" ] || [ -e "$DIR_INSTALACION/bin" ] || [ -e "$DIR_INSTALACION/.dev" ]; then
    echo "    Detectada una instalación previa de NewPT en $DIR_INSTALACION."
    echo "    Se reconstruirán .dev/ y bin/ (se conserva todo lo demás)."
    rm -rf "$DIR_INSTALACION/.dev" "$DIR_INSTALACION/bin"
fi

mkdir -p "$DIR_INSTALACION/.dev" "$DIR_INSTALACION/bin"
cp -r "$FUENTES_DIR" "$DIR_INSTALACION/.dev/fuentes"
chmod -R u+rwX "$DIR_INSTALACION/.dev"

# -----------------------------------------------------------------------------
# 4. VENV + MÓDULOS (todo dentro del venv, nada en el Python del sistema)
# -----------------------------------------------------------------------------
echo ""
echo "==> Creando ambiente virtual (venv) y módulos..."
VENV="$DIR_INSTALACION/.dev/venv"
"$PYTHON" -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip

# -----------------------------------------------------------------------------
# Módulos con versión FIJA: se instalan exactamente las mismas versiones
# probadas en desarrollo para evitar problemas de compatibilidad entre módulos.
# En particular, matplotlib >= 3.11 rompe la graticula (gridlines) de cartopy
# al dibujar (GEOSException: Points of LinearRing do not form a closed
# linestring); se usa la 3.10.9, compatible con cartopy 0.25.
# No relajar estas fijaciones sin probar antes el conjunto completo.
# -----------------------------------------------------------------------------
"$VENV/bin/pip" install \
    "numpy==2.4.4" \
    "matplotlib==3.10.9" \
    "cartopy==0.25.0" \
    "pyproj==3.7.2" \
    "Pillow==12.2.0" \
    "psycopg2-binary==2.9.12" \
    "adjustText==1.4.0" \
    "pyinstaller==6.22.2"

# Verificación: cada módulo debe quedar instalado en su versión esperada.
echo ""
echo "==> Versiones instaladas en el venv:"
"$VENV/bin/python" - <<'EOF'
import importlib.metadata as md

MODULOS = ("numpy", "matplotlib", "cartopy", "pyproj", "Pillow",
           "psycopg2-binary", "adjustText", "pyinstaller")
for m in MODULOS:
    try:
        print(f"    [OK] {m:<16} {md.version(m)}")
    except md.PackageNotFoundError:
        print(f"    [FALTA] {m}: no quedó instalado")
        raise SystemExit(1)
EOF

# -----------------------------------------------------------------------------
# 5. COMPILACIÓN A BINARIOS (PyInstaller)
# -----------------------------------------------------------------------------
echo ""
echo "==> Compilando binarios (puede tardar varios minutos)..."
cd "$DIR_INSTALACION/.dev/fuentes"

"$VENV/bin/pyinstaller" --onedir --noconfirm --clean \
    --name newpt_capturar \
    --collect-data cartopy \
    --collect-data pyproj \
    --hidden-import matplotlib.backends.backend_tkagg \
    --hidden-import tkinter \
    --hidden-import PIL._tkinter_finder \
    capturar.py

"$VENV/bin/pyinstaller" --onedir --noconfirm --clean \
    --name newpt_consulta \
    consulta_evento.py

# -----------------------------------------------------------------------------
# 6. ENSAMBLADO DE LA INSTALACIÓN
# -----------------------------------------------------------------------------
echo ""
echo "==> Ensamblando instalación..."
cp -r "$DIR_INSTALACION/.dev/fuentes/dist/newpt_capturar" "$DIR_INSTALACION/bin/"
cp -r "$DIR_INSTALACION/.dev/fuentes/dist/newpt_consulta" "$DIR_INSTALACION/bin/"

cp -r "$DATOS_DIR_SRC/." "$DIR_INSTALACION/"

cp "$TPL" "$DIR_INSTALACION/newpt.sh"
chmod +x "$DIR_INSTALACION/newpt.sh"

# Archivo de configuración de BD (ajustable por el operador)
cat > "$DIR_INSTALACION/.env" <<EOF
# Configuración de conexión a la base de datos SeisComP
NEWPT_DB_HOST=10.54.217.69
NEWPT_DB_DATABASE=seiscomp
NEWPT_DB_USER=sysop
NEWPT_DB_PASSWORD=sysop
EOF
chmod 600 "$DIR_INSTALACION/.env"

# Ocultar y restringir la carpeta de desarrollo (venv + fuentes)
chmod 700 "$DIR_INSTALACION/.dev"

# -----------------------------------------------------------------------------
# 7. RESUMEN
# -----------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  INSTALACIÓN COMPLETADA"
echo "============================================================"
echo ""
echo "Estructura en $DIR_INSTALACION:"
echo "  newpt.sh                      -> lanzador (lo ejecuta el botón de SeisComP)"
echo "  .env                          -> configuración de la BD (chmod 600)"
echo "  bin/newpt_capturar/           -> binario del graficador"
echo "  bin/newpt_consulta/           -> binario de la consulta"
echo "  grillas/ NE2_....tif base_2023_2026.dat localidades.csv"
echo "  .dev/                         -> venv + fuentes (oculto, chmod 700)"
echo ""
echo "Python usado para compilar: $("$PYTHON" -V) ($(command -v "$PYTHON"))"
echo ""
echo "PRUEBA:"
echo "  cd $DIR_INSTALACION && ./newpt.sh csn_sc62026nkkbb"
echo ""
echo "  (reemplace 'csn_sc62026nkkbb' por el ID del evento a graficar."
echo "   Escríbalo tal cual, sin signos < > ni comillas.)"
echo ""
echo "BOTÓN DE SEISCOMP:"
echo "  Configura el módulo para que ejecute:"
echo "      $DIR_INSTALACION/newpt.sh \$EVENT_ID"
echo ""
echo "  Aquí SÍ se escribe literalmente \$EVENT_ID: SeisComP lo"
echo "  reemplaza automáticamente por el ID del evento al presionarlo."
echo ""
echo "RECORDATORIO (una sola vez, con sudo):"
echo "  sudo apt install -y python3 python3-venv python3-tk xterm"
echo "============================================================"