#!/usr/bin/env python3
import os
import time
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GR = os.path.join(BASE_DIR, "grillas")

ARCH_TOPO = os.path.join(GR, "topochile30.xyz")
ARCH_SLAB = os.path.join(GR, "sam_slab2_dep_02.23.18.xyz")
BIN_TOPO = os.path.join(GR, "topo_chile.npy")
BIN_SLAB = os.path.join(GR, "slab2_global.npy")

def contar_lineas(path):
    n = 0
    with open(path, 'rb') as f:
        for _ in f:
            n += 1
    return n

def procesar_xyz(path, sep, cols, converter, filtro, nombre):
    print(f"[PREPROC] {nombre}: contando líneas de {os.path.basename(path)} ...")
    t0 = time.time()
    total = contar_lineas(path)
    arr = np.empty((total, cols), dtype=np.float32)
    k = 0
    with open(path, 'r') as f:
        for linea in f:
            if linea.startswith('#') or not linea.strip():
                continue
            partes = linea.strip().split(sep)
            if len(partes) >= cols:
                vals = converter(partes)
                if filtro is not None and not filtro(vals):
                    continue
                arr[k] = vals[:cols]
                k += 1
    arr = arr[:k]
    print(f"[PREPROC] {nombre}: {k:,} filas válidas leídas en {time.time()-t0:.1f}s")
    t0 = time.time()
    arr = arr[np.argsort(arr[:, 1], kind='stable')]
    print(f"[PREPROC] {nombre}: ordenado por latitud en {time.time()-t0:.1f}s")
    return arr

def main():
    ok = 0
    if os.path.exists(ARCH_TOPO):
        t0 = time.time()
        def conv_topo(p):
            return (float(p[0]), float(p[1]), float(p[2]))
        arr = procesar_xyz(ARCH_TOPO, None, 3, conv_topo, None, "topografía global")
        np.save(BIN_TOPO, arr)
        print(f"[PREPROC] Topografía global guardada: {BIN_TOPO} "
              f"({arr.nbytes/1e6:.0f} MB) en {time.time()-t0:.1f}s")
        print(f"[PREPROC]   cobertura lat: {arr[:,1].min():.2f} a {arr[:,1].max():.2f} | "
              f"lon: {arr[:,0].min():.2f} a {arr[:,0].max():.2f}")
        ok += 1
    else:
        print(f"[PREPROC] Aviso: no existe {ARCH_TOPO}, se omite topografía binaria.")

    if os.path.exists(ARCH_SLAB):
        t0 = time.time()
        def conv_slab(p):
            lon0 = float(p[0])
            lon1 = lon0 - 360 if lon0 > 180 else lon0
            return (lon1, float(p[1]), abs(float(p[2])))
        def filtro_slab(v):
            return not (np.isnan(v[0]) or np.isnan(v[1]) or np.isnan(v[2]))
        arr = procesar_xyz(ARCH_SLAB, ',', 3, conv_slab, filtro_slab, "slab global")
        np.save(BIN_SLAB, arr)
        print(f"[PREPROC] Slab global guardado: {BIN_SLAB} "
              f"({arr.nbytes/1e6:.0f} MB) en {time.time()-t0:.1f}s")
        print(f"[PREPROC]   cobertura lat: {arr[:,1].min():.2f} a {arr[:,1].max():.2f} | "
              f"lon: {arr[:,0].min():.2f} a {arr[:,0].max():.2f}")
        ok += 1
    else:
        print(f"[PREPROC] Aviso: no existe {ARCH_SLAB}, se omite slab binario.")

    if ok == 0:
        print("[PREPROC] ERROR: no se encontró ninguna grilla global de origen.")
    else:
        print(f"[PREPROC] Preprocesado completado ({ok}/2 grillas).")

if __name__ == "__main__":
    main()