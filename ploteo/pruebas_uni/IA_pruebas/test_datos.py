# Tests de integridad de los archivos de datos de NewPT.
# Leen desde NEWPT_DATA_DIR (default: la carpeta que contiene a tests/).
import csv
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATOS = os.environ.get("NEWPT_DATA_DIR") or \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRILLAS = os.path.join(DATOS, "grillas")

RE_SLAB = re.compile(r"^slabP(\d+)\.tmp$")
RE_TOPO = re.compile(r"^topoP(\d+)\.tmp$")


def listar_perfiles():
    slabs, topos = {}, {}
    if os.path.isdir(GRILLAS):
        for nombre in os.listdir(GRILLAS):
            m = RE_SLAB.match(nombre)
            if m:
                slabs[int(m.group(1))] = nombre
            m = RE_TOPO.match(nombre)
            if m:
                topos[int(m.group(1))] = nombre
    return slabs, topos


class TestPerfiles(unittest.TestCase):
    def test_c1_hay_pares_consistentes(self):
        slabs, topos = listar_perfiles()
        self.assertGreater(len(slabs), 0, f"No hay slabP###.tmp en {GRILLAS}")
        huerfanos_slab = sorted(set(slabs) - set(topos))
        huerfanos_topo = sorted(set(topos) - set(slabs))
        pares = sorted(set(slabs) & set(topos))
        self.assertGreater(len(pares), 0,
                           "No existe ni un par slabP###/topoP### completo")
        self.assertEqual(huerfanos_slab, [],
                         f"slabP sin su topoP: {[slabs[i] for i in huerfanos_slab]}")
        self.assertEqual(huerfanos_topo, [],
                         f"topoP sin su slabP: {[topos[i] for i in huerfanos_topo]}")

    def test_c2_perfiles_parseables(self):
        slabs, topos = listar_perfiles()
        for nombre in list(slabs.values()) + list(topos.values()):
            with self.subTest(perfil=nombre):
                ruta = os.path.join(GRILLAS, nombre)
                filas_datos = 0
                with open(ruta, "r") as f:
                    for linea in f:
                        if linea.startswith("#") or not linea.strip():
                            continue
                        partes = linea.strip().split()
                        self.assertGreaterEqual(
                            len(partes), 7, f"{nombre}: fila con menos de 7 columnas")
                        float(partes[2])   # longitud
                        float(partes[3])   # latitud
                        if "nan" not in partes[6].lower():
                            float(partes[6])   # profundidad/altura
                        filas_datos += 1
                self.assertGreater(filas_datos, 0, f"{nombre}: sin filas de datos")


class TestCatalogos(unittest.TestCase):
    def test_c3_base_historica_parseable(self):
        ruta = os.path.join(DATOS, "base_2023_2026.dat")
        self.assertTrue(os.path.exists(ruta), f"Falta {ruta}")
        n_filas = 0
        with open(ruta, "r") as f:
            for i, linea in enumerate(f):
                partes = linea.strip().split()
                if not partes:
                    continue
                self.assertGreaterEqual(len(partes), 5)
                for idx in (2, 3, 4):          # lat, lon, prof
                    float(partes[idx])
                n_filas += 1
                if i >= 200:                    # muestra suficiente
                    break
        self.assertGreater(n_filas, 0)

    def test_c4_localidades_con_filas(self):
        ruta = os.path.join(DATOS, "localidades.csv")
        self.assertTrue(os.path.exists(ruta), f"Falta {ruta}")
        with open(ruta, newline="", encoding="utf-8") as f:
            lector = list(csv.reader(f))
        self.assertGreaterEqual(len(lector), 2)   # encabezado + ≥1 localidad


class TestRelieveYGrillasGlobales(unittest.TestCase):
    def test_c5_tif_relieve_presente(self):
        ruta = os.path.join(DATOS, "NE2_LR_LC_SR_W_DR.tif")
        self.assertTrue(os.path.exists(ruta), f"Falta {ruta}")
        self.assertGreater(os.path.getsize(ruta), 0)

    def test_c6_npy_globales_cargan_si_existen(self):
        import numpy as np
        for binario in ("slab2_global.npy", "topo_chile.npy"):
            ruta = os.path.join(GRILLAS, binario)
            if not os.path.exists(ruta):
                continue   # son opcionales
            with self.subTest(binario=binario):
                arr = np.load(ruta, mmap_mode="r")
                self.assertEqual(arr.ndim, 2)
                self.assertEqual(arr.shape[1], 3)


if __name__ == "__main__":
    unittest.main()
