#!/bin/bash
# =============================================================================
# crear_instalador.sh - Empaqueta NewPT para instalarlo en cualquier máquina.
# Se ejecuta en la MÁQUINA DE DESARROLLO (donde están los scripts y los datos).
#
# Genera: newpt_instalador.tar.gz  (con instalar_newpt.sh, fuentes/, datos/,
#         newpt.sh.tpl, LISTA_PARA_TI.txt e INSTRUCCIONES_INSTALACION.docx)
#
# USO:
#   ./crear_instalador.sh [DIR_SALIDA]      # default: directorio actual
# =============================================================================

set -euo pipefail

DIR_ORIGEN="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
DIR_SALIDA="${1:-$DIR_ORIGEN}"

echo "==> Empaquetando instalador NewPT desde $DIR_ORIGEN"

EMP="$(mktemp -d)"
trap 'rm -rf "$EMP"' EXIT
BASE="$EMP/newpt_instalador"

mkdir -p "$BASE/fuentes" "$BASE/datos"

# --- Fuentes (solo los necesarios para ejecutar/compilar) ---
cp "$DIR_ORIGEN/capturar.py"          "$BASE/fuentes/"
cp "$DIR_ORIGEN/consulta_evento.py"   "$BASE/fuentes/"
cp "$DIR_ORIGEN/precalentar.py"       "$BASE/fuentes/"
# Módulos auxiliares que los tests de la marcha blanca importan (PYTHONPATH=fuentes)
cp "$DIR_ORIGEN/lee_catalogo.py"      "$BASE/fuentes/"
cp "$DIR_ORIGEN/preprocesa_grillas.py" "$BASE/fuentes/"

# --- Pruebas unitarias (marcha blanca del instalador) ---
# Solo los tests: el informe y el curso de pruebas son material interno
# de QA/capacitación, no viajan en el paquete.
if [ -d "$DIR_ORIGEN/pruebas" ]; then
    cp -r "$DIR_ORIGEN/pruebas" "$BASE/fuentes/pruebas"
    rm -f "$BASE/fuentes/pruebas/INFORME_TESTS_MARCHA_BLANCA.docx" \
          "$BASE/fuentes/pruebas/generar_informe_tests.py" \
          "$BASE/fuentes/pruebas/generar_informe_mis_tests.py" \
          "$BASE/fuentes/pruebas/generar_informe_tests_ia.py" \
          "$BASE/fuentes/pruebas/CURSO_TESTS_UNITARIOS.docx" \
          "$BASE/fuentes/pruebas/generar_curso.py" \
          "$BASE/fuentes/pruebas/generar_media_curso.py"
    rm -rf "$BASE/fuentes/pruebas/CURSO_MEDIA" \
           "$BASE"/fuentes/pruebas/__pycache__
fi

# --- Herramientas de instalación ---
cp "$DIR_ORIGEN/instalar_newpt.sh"    "$BASE/"
cp "$DIR_ORIGEN/newpt.sh.tpl"         "$BASE/"
cp "$DIR_ORIGEN/documentos/LISTA_PARA_TI.txt"    "$BASE/"
cp "$DIR_ORIGEN/documentos/INSTRUCCIONES_INSTALACION.docx" "$BASE/"

# --- Datos ---
cp -r "$DIR_ORIGEN/grillas"           "$BASE/datos/"
cp "$DIR_ORIGEN/NE2_LR_LC_SR_W_DR.tif"  "$BASE/datos/"
cp "$DIR_ORIGEN/relieve_chile.tif"      "$BASE/datos/"
cp "$DIR_ORIGEN/base_2023_2026.dat"   "$BASE/datos/"
cp "$DIR_ORIGEN/localidades.csv"      "$BASE/datos/"

# --- Permisos ---
chmod +x "$BASE/instalar_newpt.sh"

# --- Limpieza de cachés antes de empaquetar ---
find "$EMP" -type d -name "__pycache__" -prune -exec rm -rf {} +

# --- Tarball ---
TARBALL="$DIR_SALIDA/newpt_instalador.tar.gz"
mkdir -p "$DIR_SALIDA"
tar -czf "$TARBALL" -C "$EMP" newpt_instalador

echo "==> Listo: $TARBALL"
echo ""
echo "Para instalarlo en una máquina nueva:"
echo "  1) (TI)  sudo apt install -y python3 python3-venv python3-tk xterm"
echo "  2) Copiar $TARBALL a la máquina"
echo "  3) tar -xzf newpt_instalador.tar.gz"
echo "  4) cd newpt_instalador && ./instalar_newpt.sh"