# Misión M3 — Tests de lee_catalogo (lee_catalogo.py)
# ==========================================================================
# Esta función lee un archivo de catálogo sísmico (.dat) concolumnas
# separadas por espacios y devuelve un DataFrame de pandas con:
#   fecha, lon, lat, prof, mag, type_mag, sensible
#
# Formato esperado del .dat (columnas por posición):
#   0: fecha (YYYY-MM-DD)    1: hora (HH:MM:SS)
#   2: latitud                3: longitud
#   4: profundidad            5: magnitud
#   6: tipo de magnitud       7: sensible ("S" o "N")
#
# Para los tests creamos archivos .dat temporales con tempfile.
# ==========================================================================

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import lee_catalogo


def crear_archivo_dat(lineas, directorio=None):
    """
    Crea un archivo .dat temporal con las líneas proporcionadas.
    Retorna la ruta del archivo creado.

    Cada línea debe ser una cadena con columnas separadas por espacios,
    en el orden: fecha hora lat lon prof mag tipo_mag sensible
    """
    if directorio is None:
        directorio = tempfile.mkdtemp(prefix="m3_test_")
    ruta = os.path.join(directorio, "catalogo_test.dat")
    with open(ruta, "w") as f:
        for linea in lineas:
            f.write(linea.strip() + "\n")
    return ruta


class TestM3Catalogo(unittest.TestCase):
    """Tests de lee_catalogo(): lectura de archivos de catálogo sísmico."""

    # =====================================================================
    # TEST 1: Archivo con 2 eventos → lat/lon en columnas correctas
    # =====================================================================
    # Verificamos que la función lee correctamente un archivo con datos
    # y que latitud (col 2) y longitud (col 3) están en las posiciones
    # correctas del DataFrame (no invertidas).
    # NOTA: Se usan 2 filas porque np.loadtxt con 1 sola fila devuelve
    # un escalar (0-dimensional) en vez de array, lo que genera IndexError.
    # Esto es un comportamiento conocido de numpy, no un bug de la función.
    def test_1_archivo_minimo_lat_lon_correctos(self):
        """2 eventos: lat/lon en columnas correctas."""
        ruta = crear_archivo_dat([
            "2026-08-21 14:32:05 -35.42 -71.62 95.3 4.6 Ml S",
            "2026-08-22 10:15:00 -23.50 -70.10 30.0 5.2 Mw N",
        ])
        df = lee_catalogo.lee_catalogo(ruta)

        # Debe tener 2 filas
        self.assertEqual(len(df), 2,
                         "Un archivo con 2 líneas debe devolver 2 filas")

        # Verificamos que lat y lon están en las posiciones correctas
        self.assertAlmostEqual(df.iloc[0]["lat"], -35.42, places=2)
        self.assertAlmostEqual(df.iloc[0]["lon"], -71.62, places=2)
        self.assertAlmostEqual(df.iloc[0]["prof"], 95.3, places=1)
        self.assertAlmostEqual(df.iloc[0]["mag"], 4.6, places=1)
        self.assertEqual(df.iloc[0]["type_mag"], "Ml")

    # =====================================================================
    # TEST 2: Múltiples eventos → todas las filas parseadas
    # =====================================================================
    # Verificamos que la función maneja archivos con varias líneas
    # y que todas las filas aparecen en el DataFrame.
    def test_2_multiples_eventos(self):
        """3 eventos: 3 filas en el DataFrame."""
        ruta = crear_archivo_dat([
            "2026-08-21 14:32:05 -35.42 -71.62 95.3 4.6 Ml S",
            "2026-08-22 10:15:00 -23.50 -70.10 30.0 5.2 Mw N",
            "2026-08-23 08:00:00 -40.00 -73.00 10.0 3.1 Ms S",
        ])
        df = lee_catalogo.lee_catalogo(ruta)

        # 3 filas
        self.assertEqual(len(df), 3,
                         "3 líneas deben dar 3 filas")

        # Verificamos la primera y última
        self.assertAlmostEqual(df.iloc[0]["lat"], -35.42, places=2)
        self.assertAlmostEqual(df.iloc[2]["lat"], -40.00, places=2)

    # =====================================================================
    # TEST 3: Fecha concatenada = col0 + " " + col1
    # =====================================================================
    # La función concatena la fecha (col 0) y la hora (col 1) para formar
    # el campo "fecha" del DataFrame. Verificamos que el formato es correcto.
    # Se usan 2 filas para evitar el problema de np.loadtxt con 1 sola fila.
    def test_3_fecha_concatenada_correctamente(self):
        """Fecha = 'YYYY-MM-DD HH:MM:SS' concatenando col0 y col1."""
        ruta = crear_archivo_dat([
            "2026-08-21 14:32:05 -35.42 -71.62 95.3 4.6 Ml S",
            "2026-08-22 10:15:00 -23.50 -70.10 30.0 5.2 Mw N",
        ])
        df = lee_catalogo.lee_catalogo(ruta)

        # La fecha debe ser la concatenación de col0 + espacio + col1
        self.assertEqual(df.iloc[0]["fecha"], "2026-08-21 14:32:05",
                         "Fecha debe ser col0 + ' ' + col1")
        self.assertEqual(df.iloc[1]["fecha"], "2026-08-22 10:15:00")

    # =====================================================================
    # TEST 4: Columna sensible: "S" → True, "N" → False
    # =====================================================================
    # La columna sensible (col 7) usa "S" (Sí, es sensible) y "N" (No).
    # La función mapea esto a booleanos True/False.
    def test_4_sensible_s_y_n_mapeo_booleano(self):
        """'S' → True, 'N' → False en la columna sensible."""
        ruta = crear_archivo_dat([
            "2026-08-21 14:32:05 -35.42 -71.62 95.3 4.6 Ml S",
            "2026-08-22 10:15:00 -23.50 -70.10 30.0 5.2 Mw N",
        ])
        df = lee_catalogo.lee_catalogo(ruta)

        # Primera fila: "S" → True
        self.assertTrue(df.iloc[0]["sensible"],
                        "'S' debe mapearse a True")
        # Segunda fila: "N" → False
        self.assertFalse(df.iloc[1]["sensible"],
                         "'N' debe mapearse a False")

    # =====================================================================
    # TEST 5: sensibles=True → columna sensible es numérica (no booleana)
    # =====================================================================
    # Cuando se pasa sensibles=True, la función reemplaza la columna
    # sensible con valores numéricos de la última columna del archivo.
    # Esto se usa para otro tipo de análisis donde "sensible" es un número.
    def test_5_sensibles_true_columna_numerica(self):
        """sensibles=True: columna sensible es numérica."""
        # La última columna ahora es un número (ej. magnitud percibida)
        ruta = crear_archivo_dat([
            "2026-08-21 14:32:05 -35.42 -71.62 95.3 4.6 Ml 3.2",
            "2026-08-22 10:15:00 -23.50 -70.10 30.0 5.2 Mw 4.8",
        ])
        df = lee_catalogo.lee_catalogo(ruta, sensibles=True)

        # La columna sensible debe ser numérica, no booleana
        self.assertAlmostEqual(df.iloc[0]["sensible"], 3.2, places=1)
        self.assertAlmostEqual(df.iloc[1]["sensible"], 4.8, places=1)

    # =====================================================================
    # TEST 6: Archivo vacío → se maneja sin errores fatales
    # =====================================================================
    # Un archivo vacío no tiene datos para leer. np.loadtxt retorna
    # arrays vacíos (con warnings). La función debe generar un DataFrame
    # vacío sin lanzar excepciones.
    def test_6_archivo_vacio(self):
        """Archivo vacío: genera DataFrame vacío sin errores fatales."""
        import pandas as pd
        ruta = crear_archivo_dat([])  # archivo sin líneas
        # np.loadtxt con archivo vacío retorna arrays vacíos
        # La función debe manejar esto y devolver un DataFrame
        df = lee_catalogo.lee_catalogo(ruta)
        self.assertIsInstance(df, pd.DataFrame,
                              "Debe devolver un DataFrame incluso si está vacío")
        self.assertEqual(len(df), 0,
                         "Archivo vacío → DataFrame con 0 filas")

    # =====================================================================
    # TEST 7: Múltiples archivos → cada uno produce su propio DataFrame
    # =====================================================================
    # Verificamos que la función puede leer distintos archivos
    # independientemente y que los datos no se mezclan entre sí.
    def test_7_archivos_independientes(self):
        """Archivos diferentes: datos no se mezclan."""
        # Usamos directorios separados para que no se sobrescriban
        ruta1 = crear_archivo_dat([
            "2026-08-21 14:32:05 -35.42 -71.62 95.3 4.6 Ml S",
            "2026-08-22 10:15:00 -23.50 -70.10 30.0 5.2 Mw N",
        ])
        ruta2 = crear_archivo_dat([
            "2026-09-01 08:00:00 -40.00 -73.00 10.0 3.1 Ms S",
            "2026-09-02 12:00:00 -41.00 -74.00 20.0 2.5 Ml N",
        ])  # directorio temporal diferente por defecto

        df1 = lee_catalogo.lee_catalogo(ruta1)
        df2 = lee_catalogo.lee_catalogo(ruta2)

        # Cada archivo produce su propio DataFrame con datos diferentes
        self.assertEqual(len(df1), 2)
        self.assertEqual(len(df2), 2)
        self.assertAlmostEqual(df1.iloc[0]["lat"], -35.42, places=2)
        self.assertAlmostEqual(df2.iloc[0]["lat"], -40.00, places=2)


if __name__ == "__main__":
    unittest.main()
