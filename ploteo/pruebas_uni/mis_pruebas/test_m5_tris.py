# Misión M5 — Tests de _promediar_tris (capturar.py)
# ==========================================================================
# Esta función agrupa puntos (lon, lat, altitud/profundidad) en celdas
# de un tamaño dado (res, en grados) y devuelve las coordenadas de las
# celdas con su valor promedio. Se usa para generar superficies 3D
# suaves y ligeras en la visualización del contexto sismotectónico.
#
# Parámetros:
#   x: array de longitudes (eje X)
#   y: array de latitudes (eje Y)
#   z: array de altitudes/profundidades (eje Z)
#   res: tamaño de la celda en grados (default: 0.2)
#
# Retorna:
#   (x_celdas, y_celdas, z_promedio): arrays con las coordenadas
#   centro de cada celda y el valor promedio de z en esa celda.
#
# La función usa np.round para agrupar, np.unique para encontrar
# celdas únicas, y np.add.at para sumar valores por celda.
# ==========================================================================

import sys
import os
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from capturar import _promediar_tris


class TestM5PromediarTris(unittest.TestCase):
    """Tests de _promediar_tris(): agrupación y promediado de puntos 3D."""

    # =====================================================================
    # TEST 1: Promedio correcto por celda
    # =====================================================================
    # Con res=1.0, los puntos se agrupan por celdas de 1 grado.
    # Verificamos que el promedio de z es correcto para cada celda.
    def test_1_promedio_correcto_por_celda(self):
        """Puntos en misma celda: promedio de z es correcto."""
        # -71.2 y -71.4 redondean a -71.0 con res=1.0 (misma celda)
        x = np.array([-71.2, -71.4])
        y = np.array([-35.2, -35.4])
        z = np.array([100.0, 200.0])   # promedio = 150.0

        xc, yc, zc = _promediar_tris(x, y, z, res=1.0)

        # Debe haber 1 sola celda
        self.assertEqual(len(xc), 1,
                         "2 puntos en misma celda → 1 celda")
        # Promedio de z: (100 + 200) / 2 = 150.0
        self.assertAlmostEqual(zc[0], 150.0, places=1,
                               msg="Promedio debe ser 150.0")

    # =====================================================================
    # TEST 2: Todos los puntos en la misma celda → 1 celda
    # =====================================================================
    # Si todos los puntos caen en la misma celda (porque res es grande
    # o porque están muy cerca), el resultado es un solo punto.
    def test_2_todos_en_misma_celda(self):
        """Todos los puntos en 1 celda: resultado es 1 punto."""
        x = np.array([-71.1, -71.2, -71.3, -71.4])
        y = np.array([-35.1, -35.2, -35.3, -35.4])
        z = np.array([100.0, 200.0, 300.0, 400.0])

        xc, yc, zc = _promediar_tris(x, y, z, res=1.0)

        # 1 sola celda
        self.assertEqual(len(xc), 1,
                         "Todos los puntos en res=1.0 → 1 celda")
        # Promedio: (100+200+300+400)/4 = 250.0
        self.assertAlmostEqual(zc[0], 250.0, places=1)

    # =====================================================================
    # TEST 3: res muy grande → todo en 1 celda
    # =====================================================================
    # Con res=10.0, puntos que están a varios grados de distancia
    # se agrupan en una sola celda.
    def test_3_res_grande_una_sola_celda(self):
        """res=10.0: puntos cercanos → 1 celda."""
        # -72, -74, -73 con res=10 → todos redondean a -70.0
        x = np.array([-72.0, -74.0, -73.0])
        y = np.array([-32.0, -34.0, -33.0])
        z = np.array([100.0, 200.0, 300.0])

        xc, yc, zc = _promediar_tris(x, y, z, res=10.0)

        self.assertEqual(len(xc), 1,
                         "res=10 agrupa puntos cercanos en 1 celda")

    # =====================================================================
    # TEST 4: res muy pequeño → cada punto = 1 celda (sin promediar)
    # =====================================================================
    # Con res muy pequeño (0.001), cada punto cae en su propia celda.
    # No hay promediado porque no hay dos puntos en la misma celda.
    def test_4_res_pequeno_cada_punto_es_celda(self):
        """res=0.001: cada punto es su propia celda."""
        x = np.array([-71.1, -71.2, -71.3])
        y = np.array([-35.1, -35.2, -35.3])
        z = np.array([100.0, 200.0, 300.0])

        xc, yc, zc = _promediar_tris(x, y, z, res=0.001)

        # 3 celdas (una por punto)
        self.assertEqual(len(xc), 3,
                         "res muy pequeño: cada punto = 1 celda")
        # Los valores de z deben ser los originales (sin promediar)
        # np.unique ordena la salida, así que ordenamos los esperados
        z_ordenado = sorted(zc)
        np.testing.assert_array_almost_equal(z_ordenado, [100.0, 200.0, 300.0],
                                             decimal=1)

    # =====================================================================
    # TEST 5: Profundidades negativas → promedio negativo correcto
    # =====================================================================
    # En sismología, la profundidad del slab se representa como negativa
    # (por debajo del nivel del mar). La función debe manejar negativos
    # correctamente al promediar.
    def test_5_profundidades_negativas(self):
        """Profundidades negativas: promedio negativo correcto."""
        x = np.array([-71.1, -71.2])
        y = np.array([-35.1, -35.2])
        z = np.array([-100.0, -300.0])  # profundidades negativas

        xc, yc, zc = _promediar_tris(x, y, z, res=1.0)

        # Promedio: (-100 + -300) / 2 = -200.0
        self.assertAlmostEqual(zc[0], -200.0, places=1,
                               msg="Promedio de negativos debe ser negativo")

    # =====================================================================
    # TEST 6: Array vacío → salida vacía sin errores
    # =====================================================================
    # Si se pasan arrays vacíos, la función no debe fallar.
    def test_6_array_vacio(self):
        """Arrays vacíos: salida vacía sin errores."""
        x = np.array([])
        y = np.array([])
        z = np.array([])

        xc, yc, zc = _promediar_tris(x, y, z, res=0.2)

        # Las salidas deben ser arrays vacíos
        self.assertEqual(len(xc), 0, "Salida x debe estar vacía")
        self.assertEqual(len(yc), 0, "Salida y debe estar vacía")
        self.assertEqual(len(zc), 0, "Salida z debe estar vacía")

    # =====================================================================
    # TEST 7: Un solo punto → 1 celda con su valor
    # =====================================================================
    # Un punto único genera exactamente 1 celda con el valor original.
    def test_7_un_solo_punto(self):
        """1 punto: 1 celda con su valor."""
        x = np.array([-71.5])
        y = np.array([-35.5])
        z = np.array([150.0])

        xc, yc, zc = _promediar_tris(x, y, z, res=0.2)

        self.assertEqual(len(xc), 1, "1 punto → 1 celda")
        self.assertAlmostEqual(zc[0], 150.0, places=1,
                               msg="Valor debe ser el original")


if __name__ == "__main__":
    unittest.main()
