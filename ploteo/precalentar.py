#!/usr/bin/env python3
"""
precalentar.py - Precarga en la caché de página del sistema los módulos de
Python y los archivos de datos pesados que usa NewPT.

Cada ejecución de NewPT lanza procesos nuevos. Si pasa un tiempo sin usarlo,
Linux expulsa del page cache los .so de los módulos (matplotlib/cartopy/scipy)
y los datos (TIF recortado, grillas .npy). Al volver, la primera llamada
relee todo desde disco y se nota lenta.

Este script "calienta" ese caché ANTES de que corra capturar.py, para que la
generación de mapas encuentre módulos y datos ya en RAM.

Dos frentes, porque Linux comparte la caché de página por archivo (inodo):
  * DATOS: se leen por la misma ruta que usa capturar.py (relieve_chile.tif,
    topo_chile.npy, slab2_global.npy) -> mismo inodo -> caché compartida.
  * MÓDULOS: se tocan los mismos .so que capturar.py importará. En un binario
    PyInstaller --onedir, precalentar y capturar NO comparten _internal
    (cada uno copia los suyos), así que importar aquí matplotlib/cartopy
    desde el propio binario no acelera a capturar. Por eso se leen
    directamente los archivos .so de bin/newpt_capturar/_internal/ (los que
    capturar realmente va a mapear). En desarrollo (sin PyInstaller) se leen
    los .so de los paquetes instalados del sistema, que capturar igual usa.

Se lanza en background desde newpt.sh. Es silencioso a nivel gráfico; solo
imprime por terminal algunas líneas [Precaliente].
"""
import importlib
import os
import sys
import time

import mediciones as med


def ruta_datos():
    env = os.environ.get("NEWPT_DATA_DIR")
    if env:
        return env
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _leer_bloques(arch):
    """Lee un archivo por bloques empujándolo al page cache del sistema."""
    with open(arch, "rb") as fh:
        while fh.read(8 * 1024 * 1024):
            pass


def calentar_datos(dir_datos):
    """Calienta en caché los archivos de datos pesados que lee capturar.py."""
    rel = os.path.join(dir_datos, "relieve_chile.tif")
    topo = os.path.join(dir_datos, "grillas", "topo_chile.npy")
    slab = os.path.join(dir_datos, "grillas", "slab2_global.npy")
    leidos = []
    for arch in (rel, topo, slab):
        if os.path.exists(arch):
            try:
                _leer_bloques(arch)
                leidos.append(os.path.basename(arch))
            except OSError:
                pass
    return leidos


def _internal_capturar():
    """Devuelve el directorio _internal del binario newpt_capturar, si existe.

    En un binario PyInstaller --onedir el ejecutable vive en
    bin/newpt_capturar/newpt_capturar y sus módulos en
    bin/newpt_capturar/_internal. precalentar vive junto a él, en
    bin/newpt_precalentar/, por lo que se resuelve la ruta relativa.
    """
    if not getattr(sys, "frozen", False):
        return None
    base = os.path.dirname(os.path.abspath(sys.executable))
    candidatos = (
        os.path.join(base, "..", "newpt_capturar", "_internal"),
        os.path.join(base, "newpt_capturar", "_internal"),
    )
    for c in candidatos:
        c = os.path.normpath(c)
        if os.path.isdir(c):
            return c
    return None


def _dirs_paquetes():
    """Directorios de los paquetes con extensiones .so usados por capturar.py."""
    dirs = set()
    for nombre in ("numpy", "matplotlib", "PIL", "cartopy", "pyproj"):
        try:
            mod = importlib.import_module(nombre)
            dirs.add(os.path.dirname(os.path.abspath(mod.__file__)))
        except Exception:
            pass
    return list(dirs)


def _recolectar_so(dirs):
    """Lista recursiva de bibliotecas .so / libpython*.so bajo los directorios."""
    so = []
    vistos = set()
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if (f.endswith((".so", ".pyd", ".dylib"))
                        or f.startswith("libpython")):
                    p = os.path.join(root, f)
                    rp = os.path.realpath(p)
                    if rp in vistos:
                        continue
                    vistos.add(rp)
                    so.append(rp)
    return so


def calentar_modulos():
    """Calienta los .so que capturar.py importará (mismos archivos/inodos)."""
    dirs = []
    fuente = "paquetes"
    internal = _internal_capturar()
    if internal:
        dirs = [internal]
        fuente = "binario capturar"
    else:
        dirs = _dirs_paquetes()
    so = _recolectar_so(dirs)
    leidos = 0
    for arch in so:
        try:
            _leer_bloques(arch)
            leidos += 1
        except OSError:
            pass
    return fuente, leidos, so


def main():
    med.arranque("precalentar")
    t0 = time.time()
    #print("[Precaliente] Inicializando módulos...", flush=True)
    print("[Precarga] Inicializando módulos...", flush=True)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot

    import cartopy.crs
    import cartopy.feature

    try:
        import adjustText
    except Exception:
        pass

    import numpy as np
    np.__version__
    med.hito("precalentar", "imports_fin")

    dir_datos = ruta_datos()
    leidos_datos = calentar_datos(dir_datos)
    med.hito("precalentar", "datos_fin")

    fuente, n_so, lista_so = calentar_modulos()
    med.hito("precalentar", "so_fin")

    # Carga de modulos pesados en cache
    """
    if leidos_datos:
        print(f"[Precaliente] Datos en caché: {', '.join(leidos_datos)}", flush=True)
    if lista_so:
        print(f"[Precaliente] Módulos en caché ({fuente}): {n_so} .so", flush=True)
    print(f"[Precaliente] Listo ({med.ms_desde_arranque():.0f} ms). Caché tibio.", flush=True)
    """

if __name__ == "__main__":
    main()
