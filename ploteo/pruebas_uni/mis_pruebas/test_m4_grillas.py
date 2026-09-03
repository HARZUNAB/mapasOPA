# Misión M4 — Tests de contar_lineas y procesar_xyz (preprocesa_grillas.py)
# ==========================================================================
# Estas dos funciones trabajan en conjunto para preprocesar grillas
# topográficas y de profundidad de slab (archivos .xyz grandes):
#
# contar_lineas(path):
#   Cuenta líneas de un archivo de forma rápida (modo binario).
#   Se usa para reservar el array de numpy con el tamaño exacto.
#
# procesar_xyz(path, sep, cols, converter, filtro, nombre):
#   Lee un archivo .xyz línea por línea, aplica un filtro, convierte
#   los valores a números, y devuelve un array de numpy ordenado por latitud.
#   Se usa para convertir archivos de texto grandes en arrays binarios (.npy).
#
# Para los tests creamos archivos .xyz temporales con contenido controlado.
# ==========================================================================

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import preprocesa_grillas


def crear_archivo_xyz(lineas, directorio=None):
    """
    Crea un archivo .xyz temporal con las líneas proporcionadas.
    Retorna la ruta del archivo creado.

    Cada línea debe ser una cadena con valores separados por el separador
    indicado (por defecto espacio).
    """
    if directorio is None:
        directorio = tempfile.mkdtemp(prefix="m4_test_")
    ruta = os.path.join(directorio, "grilla_test.xyz")
    with open(ruta, "w") as f:
        for linea in lineas:
            f.write(linea.strip() + "\n")
    return ruta


class TestM4ContarLineas(unittest.TestCase):
    """Tests de contar_lineas(): cuenta líneas de un archivo."""

    # =====================================================================
    # TEST 1: Archivo con 3 líneas → retorna 3
    # =====================================================================
    # Verificamos que la función cuenta correctamente un archivo con
    # algunas líneas de datos.
    def test_1_tres_lineas(self):
        """3 líneas → 3."""
        ruta = crear_archivo_xyz([
            "-71.6 -35.4 100",
            "-71.7 -35.5 200",
            "-71.8 -35.6 300",
        ])
        n = preprocesa_grillas.contar_lineas(ruta)
        self.assertEqual(n, 3, "3 líneas deben contar 3")

    # =====================================================================
    # TEST 2: Archivo vacío → retorna 0
    # =====================================================================
    # Un archivo sin contenido debe retornar 0 líneas.
    def test_2_archivo_vacio(self):
        """Archivo vacío → 0."""
        ruta = crear_archivo_xyz([])
        n = preprocesa_grillas.contar_lineas(ruta)
        self.assertEqual(n, 0, "Archivo vacío debe retornar 0")

    # =====================================================================
    # TEST 3: Archivo inexistente → lanza FileNotFoundError o OSError
    # =====================================================================
    # Si el archivo no existe, la función debe lanzar una excepción
    # en vez de fallar silenciosamente.
    def test_3_archivo_inexistente(self):
        """Archivo inexistente: lanza excepción."""
        ruta_falsa = "/tmp/no_existe_este_archivo_123456789.xyz"
        with self.assertRaises((FileNotFoundError, OSError)):
            preprocesa_grillas.contar_lineas(ruta_falsa)


class TestM4ProcesarXyz(unittest.TestCase):
    """Tests de procesar_xyz(): lee archivos .xyz y los convierte en arrays."""

    # =====================================================================
    # TEST 1: Archivo con 3 puntos → array ordenado por latitud
    # =====================================================================
    # La función debe leer las líneas, convertirlas a números, y ordenar
    # el resultado por latitud (columna 1, índice 1).
    def test_1_tres_puntos_ordenados_por_lat(self):
        """3 puntos: resultado ordenado por latitud ascendente."""
        # Definimos un convertidor simple: extrae lon, lat, prof
        def converter(p):
            return (float(p[0]), float(p[1]), float(p[2]))

        ruta = crear_archivo_xyz([
            "-71.6 -35.6 300",   # lat -35.6 (debe quedar primero)
            "-71.8 -35.4 100",   # lat -35.4 (debe quedar segundo)
            "-71.7 -35.5 200",   # lat -35.5 (debe quedar tercero)
        ])

        arr = preprocesa_grillas.procesar_xyz(
            ruta, sep=None, cols=3, converter=converter,
            filtro=None, nombre="test"
        )

        # Debe tener 3 filas y 3 columnas
        self.assertEqual(arr.shape, (3, 3),
                         "Array debe ser (3, 3)")

        # Verificamos orden por latitud (columna 1)
        lats = arr[:, 1]
        self.assertAlmostEqual(lats[0], -35.6, places=1, msg="Primera lat debe ser -35.6")
        self.assertAlmostEqual(lats[1], -35.5, places=1, msg="Segunda lat debe ser -35.5")
        self.assertAlmostEqual(lats[2], -35.4, places=1, msg="Tercera lat debe ser -35.4")

    # =====================================================================
    # TEST 2: Filtro descarta filas → solo quedan las que pasan
    # =====================================================================
    # El parámetro filtro es una función que recibe los valores convertidos
    # y retorna True si la fila debe conservarse, False si se descarta.
    def test_2_filtro_descarta_filas(self):
        """Filtro: solo conserva puntos con prof > 150."""
        def converter(p):
            return (float(p[0]), float(p[1]), float(p[2]))

        def filtro(vals):
            return vals[2] > 150  # solo profundidad > 150

        ruta = crear_archivo_xyz([
            "-71.6 -35.6 100",   # descartada (100 < 150)
            "-71.7 -35.5 200",   # conservada (200 > 150)
            "-71.8 -35.4 300",   # conservada (300 > 150)
        ])

        arr = preprocesa_grillas.procesar_xyz(
            ruta, sep=None, cols=3, converter=converter,
            filtro=filtro, nombre="test"
        )

        # Solo 2 filas deben quedar
        self.assertEqual(arr.shape[0], 2,
                         "Filtro debió descartar 1 fila")

    # =====================================================================
    # TEST 3: Filtro None → conserva todas las filas
    # =====================================================================
    # Cuando filtro es None, no se descarta nada.
    def test_3_filtro_none_conserva_todo(self):
        """Filtro None: todas las filas se conservan."""
        def converter(p):
            return (float(p[0]), float(p[1]), float(p[2]))

        ruta = crear_archivo_xyz([
            "-71.6 -35.6 100",
            "-71.7 -35.5 200",
            "-71.8 -35.4 300",
        ])

        arr = preprocesa_grillas.procesar_xyz(
            ruta, sep=None, cols=3, converter=converter,
            filtro=None, nombre="test"
        )

        self.assertEqual(arr.shape[0], 3,
                         "Sin filtro, todas las filas deben quedar")

    # =====================================================================
    # TEST 4: Líneas con comentarios (#) → se ignoran
    # =====================================================================
    # El código tiene un chequeo explícito: if linea.startswith('#').
    # Las líneas que empiezan con # se saltan.
    def test_4_lineas_comentario_se_ignoran(self):
        """Línea con '#': se ignora, no cuenta como dato."""
        def converter(p):
            return (float(p[0]), float(p[1]), float(p[2]))

        ruta = crear_archivo_xyz([
            "# Comentario de la grilla",
            "-71.6 -35.6 100",
            "# Otra línea de comentario",
            "-71.7 -35.5 200",
        ])

        arr = preprocesa_grillas.procesar_xyz(
            ruta, sep=None, cols=3, converter=converter,
            filtro=None, nombre="test"
        )

        # Solo 2 filas (las líneas # se ignoraron)
        self.assertEqual(arr.shape[0], 2,
                         "Líneas con # no deben contar")

    # =====================================================================
    # TEST 5: Líneas vacías → se ignoran
    # =====================================================================
    # El código tiene: if not linea.strip(): continue
    # Las líneas vacías o con solo espacios se saltan.
    def test_5_lineas_vacias_se_ignoran(self):
        """Línea vacía: se ignora."""
        def converter(p):
            return (float(p[0]), float(p[1]), float(p[2]))

        ruta = crear_archivo_xyz([
            "-71.6 -35.6 100",
            "",                    # línea vacía
            "   ",                 # solo espacios
            "-71.7 -35.5 200",
        ])

        arr = preprocesa_grillas.procesar_xyz(
            ruta, sep=None, cols=3, converter=converter,
            filtro=None, nombre="test"
        )

        self.assertEqual(arr.shape[0], 2,
                         "Líneas vacías no deben contar")

    # =====================================================================
    # TEST 6: Archivo con 1 solo dato → array con 1 fila
    # =====================================================================
    # Un archivo con un solo punto válido debe generar un array con 1 fila.
    def test_6_un_solo_dato(self):
        """1 dato: array con 1 fila."""
        def converter(p):
            return (float(p[0]), float(p[1]), float(p[2]))

        ruta = crear_archivo_xyz([
            "-71.6 -35.6 100",
        ])

        arr = preprocesa_grillas.procesar_xyz(
            ruta, sep=None, cols=3, converter=converter,
            filtro=None, nombre="test"
        )

        self.assertEqual(arr.shape, (1, 3),
                         "1 dato debe dar array (1, 3)")

    # =====================================================================
    # TEST 7: Separador por defecto (None = whitespace) → funciona
    # =====================================================================
    # Cuando sep=None, np.loadtxt y split() usan cualquier whitespace.
    # Verificamos que funciona con espacios y tabs.
    def test_7_separador_whitespace(self):
        """Separador whitespace: espacios y tabs funcionan."""
        def converter(p):
            return (float(p[0]), float(p[1]), float(p[2]))

        ruta = crear_archivo_xyz([
            "-71.6\t-35.6\t100",   # tab como separador
            "-71.7 -35.5 200",     # espacio como separador
        ])

        arr = preprocesa_grillas.procesar_xyz(
            ruta, sep=None, cols=3, converter=converter,
            filtro=None, nombre="test"
        )

        self.assertEqual(arr.shape[0], 2,
                         "Sep=None debe manejar tabs y espacios")


if __name__ == "__main__":
    unittest.main()
