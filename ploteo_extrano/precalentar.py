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

Se lanza en background desde newpt.sh. Es silencioso a nivel gráfico; solo
imprime por terminal algunas líneas [Precaliente].
"""
import os
import sys
import time


def ruta_datos():
    env = os.environ.get("NEWPT_DATA_DIR")
    if env:
        return env
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def calentar_y_datos(dir_datos):
    leidos = []
    rel = os.path.join(dir_datos, "relieve_chile.tif")
    topo = os.path.join(dir_datos, "grillas", "topo_chile.npy")
    slab = os.path.join(dir_datos, "grillas", "slab2_global.npy")
    for arch in (rel, topo, slab):
        if os.path.exists(arch):
            try:
                with open(arch, "rb") as fh:
                    while fh.read(8 * 1024 * 1024):
                        pass
                leidos.append(os.path.basename(arch))
            except OSError:
                pass
    return leidos


def main():
    t0 = time.time()
    print("[Precaliente] Inicializando módulos...", flush=True)

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

    dir_datos = ruta_datos()
    leidos = calentar_y_datos(dir_datos)
    t1 = time.time()

    if leidos:
        print(f"[Precaliente] Datos en caché: {', '.join(leidos)}", flush=True)
    print(f"[Precaliente] Listo ({t1 - t0:.0f} ms). Caché tibio.", flush=True)


if __name__ == "__main__":
    main()
