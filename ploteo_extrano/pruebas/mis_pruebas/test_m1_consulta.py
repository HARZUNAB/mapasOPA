# Misión M1 — Tests de consultar_por_fecha_creacion (consulta_evento.py)
# ==========================================================================
# Esta función conecta a una base de datos PostgreSQL (SeisComP), busca un
# evento por su ID de origen, y escribe el resultado en evento_data.txt
# para que capturar.py lo use al momento de graficar.
#
# En estos tests NO usamos una BD real. En su lugar, "mock-eamos" (simulamos)
# psycopg2.connect para que devuelva respuestas controladas. Así podemos
# probar la lógica de la función sin depender de red ni de datos externos.
#
# Patrón: mock.patch("psycopg2.connect") reemplaza la función real por una
# versión falsa que devuelve un objeto MagicMock con un cursor que devuelve
# las filas que nosotros definamos.
# ==========================================================================

import io
import os
import sys
import tempfile
import datetime
import unittest
from contextlib import redirect_stdout
from unittest import mock

# --- IMPORTS DEL PROYECTO ---
# sys.path.insert permite que Python encuentre consulta_evento.py
# (estamos 3 niveles más abajo: mis_pruebas/ → pruebas/ → ploteo/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import consulta_evento


# --- FILA SIMULADA ---
# Representa lo que la BD devolvería al consultar un origen válido.
# Los nombres de las claves coinciden con los alias del SQL (AS id_evento, etc.)
FILA_ORIGEN = {
    "id_evento": "csn_sc62026nkkbb",
    "ot_utc": datetime.datetime(2026, 8, 21, 14, 32, 5),
    "magnitud": 4.6,
    "tipo_magnitud": "Ml",
    "fases": 128,
    "rms": 0.45,
    "azgap": 212,
    "latitud": -35.42,
    "longitud": -71.62,
    "profundidad_km": 95.3,
    "agencia": "CSN",
    "operador": "operador1",
    "region": "Region del Maule",
    "estatus": "confirmed",
}


# --- FUNCIONES AUXILIARES PARA EL MOCK ---
# Un mock "finge" ser un objeto real. Aquí creamos un cursor y una conexión
# falsos que devuelven las filas que nosotros configuremos.

def crear_cursor_fake(filas):
    """
    Crea un cursor falso. Cada vez que se llama a fetchone(), devuelve la
    siguiente fila de la lista. Cuando se acaban las filas, devuelve None.
    Esto simula el comportamiento real de un cursor de psycopg2.
    """
    it = iter(filas)
    fake = mock.MagicMock()
    fake.fetchone.side_effect = lambda: next(it, None)
    return fake


def ejecutar_con_mock(id_origen, filas_cursor):
    """
    Ejecuta consultar_por_fecha_creacion() con psycopg2 simulado.

    Retorna:
        str: lo que la función imprimió por pantalla (stdout)
    """
    cursor = crear_cursor_fake(filas_cursor)
    conexion = mock.MagicMock()
    conexion.cursor.return_value = cursor

    with mock.patch("psycopg2.connect", return_value=conexion):
        salida = io.StringIO()
        with redirect_stdout(salida):
            consulta_evento.consultar_por_fecha_creacion(id_origen)
    return salida.getvalue()


# --- CLASE DE TESTS ---
# Cada método que empieza con "test_" es un caso de prueba independiente.
# setUp() y tearDown() se ejecutan antes y después de CADA test.

class TestM1Consulta(unittest.TestCase):

    def setUp(self):
        """
        Prepara un entorno limpio para cada test:
        1. Crea una carpeta temporal (para que la función escriba ahí).
        2. Apunta la variable de entorno NEWPT_DATA_DIR a esa carpeta.
        Esto evita que los tests toquen archivos reales del sistema.
        """
        self.tmp = tempfile.mkdtemp(prefix="m1_test_")
        os.environ["NEWPT_DATA_DIR"] = self.tmp

    def tearDown(self):
        """
        Limpia después de cada test: elimina la variable de entorno
        para que no contamine otros tests.
        """
        os.environ.pop("NEWPT_DATA_DIR", None)

    def ruta_evento(self):
        """Atajo: devuelve la ruta completa de evento_data.txt en la carpeta temporal."""
        return os.path.join(self.tmp, "evento_data.txt")

    # =====================================================================
    # TEST 1: Origen preferido válido → se escribe archivo con 19 campos
    # =====================================================================
    # Este es el "camino feliz": el ID corresponde a un origen que ES el
    # preferido de su evento (tiene id_evento asociado). La función debe
    # escribir evento_data.txt con exactamente 19 campos separados por ";".
    def test_1_origen_preferido_escribe_archivo(self):
        """Origen preferido: se genera evento_data.txt con 19 campos."""
        # Ejecutamos la función con una fila válida (id_evento no es None)
        salida = ejecutar_con_mock("csn_sc62026nkkbb", [FILA_ORIGEN])

        # Verificamos que el archivo fue creado
        ruta = self.ruta_evento()
        self.assertTrue(os.path.exists(ruta),
                        "evento_data.txt debió crearse para un origen preferido")

        # Leemos la línea generada y contamos los campos
        with open(ruta, encoding="utf-8") as f:
            linea = f.readline().rstrip("\n")
        campos = linea.split(";")

        # Debe tener exactamente 19 campos
        self.assertEqual(len(campos), 19,
                         f"Se esperaban 19 campos, se encontraron {len(campos)}")

        # Verificamos algunos campos clave
        self.assertEqual(campos[0], "2026-08-21 14:32:05")  # fecha formateada
        self.assertEqual(campos[3], "4.6")                   # magnitud
        self.assertEqual(campos[4], "Ml")                    # tipo de magnitud
        self.assertEqual(campos[8], "35.42 S")               # latitud con hemisferio
        self.assertEqual(campos[9], "71.62 W")               # longitud con hemisferio
        self.assertEqual(campos[10], "95 km")                # profundidad sin decimales
        self.assertEqual(campos[-1], "csn_sc62026nkkbb")     # event_id al final

    # =====================================================================
    # TEST 2: Origen NO preferido → aviso impreso, NO se escribe archivo
    # =====================================================================
    # Cuando el origen existe pero NO es el preferido del evento (id_evento
    # es None porque el LEFT JOIN no encontró evento asociado), la función
    # imprime un aviso y NO escribe ningún archivo.
    def test_2_origen_no_preferido_avisa_y_no_escribe(self):
        """Origen no preferido: imprime aviso y no genera archivo."""
        # Creamos una fila donde id_evento es None (= origen no preferido)
        fila_no_preferida = dict(FILA_ORIGEN, id_evento=None)

        salida = ejecutar_con_mock("origen_no_preferido", [fila_no_preferida])

        # El aviso debe aparecer en la salida por pantalla
        self.assertIn("NO es la solución preferida", salida,
                      "Debió imprimirse el aviso de origen no preferido")

        # No se debió crear el archivo
        self.assertFalse(os.path.exists(self.ruta_evento()),
                         "No debió crearse evento_data.txt para origen no preferido")

    # =====================================================================
    # TEST 3: ID inexistente → no se escribe archivo
    # =====================================================================
    # Si el ID no existe como origen ni como evento, fetchone() devuelve
    # None en ambas consultas. La función imprime un mensaje y sale sin
    # escribir nada.
    def test_3_id_inexistente_no_escribe_archivo(self):
        """ID inexistente: no se crea evento_data.txt."""
        # Cursor que devuelve None = "no encontré nada en la BD"
        salida = ejecutar_con_mock("ID_INEXISTENTE", [None])

        self.assertFalse(os.path.exists(self.ruta_evento()),
                         "No debió crearse evento_data.txt para ID inexistente")
        self.assertIn("No se encontró", salida,
                      "Debió imprimirse el mensaje de ID no encontrado")

    # =====================================================================
    # TEST 4: Limpieza preventiva → archivo viejo se borra antes de consultar
    # =====================================================================
    # Si ya existía un evento_data.txt de una consulta anterior (residuo),
    # la función lo borra antes de conectar a la BD. Esto evita "ploteos
    # fantasmas" donde se grafica un evento que ya no es el seleccionado.
    def test_4_limpieza_preventiva_borra_archivo_viejo(self):
        """Archivo viejo se borra preventivamente antes de la consulta."""
        # Creamos un archivo viejo con contenido basura
        ruta = self.ruta_evento()
        with open(ruta, "w") as f:
            f.write("residuo de un evento anterior que ya no sirve")

        # Verificamos que el archivo viejo existe antes de ejecutar
        self.assertTrue(os.path.exists(ruta),
                        "Precondición: el archivo viejo debe existir")

        # Ejecutamos con un ID inexistente (para que no genere uno nuevo)
        ejecutar_con_mock("OTRO_ID", [None])

        # El archivo viejo debió ser eliminado
        self.assertFalse(os.path.exists(ruta),
                         "El archivo viejo debió ser borrado por la limpieza preventiva")

    # =====================================================================
    # TEST 5: Magnitud None → campo magnitud queda vacío, tipo queda "M"
    # =====================================================================
    # Cuando un evento no tiene magnitud calculada (es None), la función
    # asigna un string vacío al campo magnitud y "M" al tipo. Esto lo
    # interpreta capturar.py como "M s/d" (Sin Datos) en el título del gráfico.
    def test_5_magnitud_none_campo_vacio(self):
        """Magnitud None: campo vacío y tipo 'M' por defecto."""
        # Fila con magnitud y tipo_magnitud en None
        fila_sin_mag = dict(FILA_ORIGEN, magnitud=None, tipo_magnitud=None)
        ejecutar_con_mock("csn_test_mag", [fila_sin_mag])

        with open(self.ruta_evento(), encoding="utf-8") as f:
            campos = f.readline().split(";")

        # Campo magnitud (posición 3) debe estar vacío
        self.assertEqual(campos[3], "",
                         "La magnitud None debe escribirse como campo vacío")
        # Campo tipo magnitud (posición 4) debe ser "M" por defecto
        self.assertEqual(campos[4], "M",
                         "El tipo de magnitud None debe ser 'M' por defecto")

    # =====================================================================
    # TEST 6: Fallback por evento → ID con formato "Event/..." usa segunda SQL
    # =====================================================================
    # Si el ID no se encuentra como origen, la función intenta buscarlo
    # como evento (segunda consulta SQL). Esto permite pasar el publicID
    # de un evento directamente, no solo el de un origen.
    def test_6_fallback_por_evento(self):
        """ID de evento (no de origen): usa la segunda consulta SQL."""
        # El mock hace dos llamadas a fetchone(): primera returns None
        # (= no encontrado como origen), segunda devuelve la fila (= encontrado como evento)
        cursor = crear_cursor_fake([None, FILA_ORIGEN])
        conexion = mock.MagicMock()
        conexion.cursor.return_value = cursor

        with mock.patch("psycopg2.connect", return_value=conexion):
            salida = io.StringIO()
            with redirect_stdout(salida):
                consulta_evento.consultar_por_fecha_creacion("Event/2026abc")

        # Se escribió el archivo (encontró el evento por fallback)
        self.assertTrue(os.path.exists(self.ruta_evento()),
                        "El fallback por evento debió generar el archivo")

    # =====================================================================
    # TEST 7: eventdescription ausente → campo region queda vacío
    # =====================================================================
    # El campo "region" viene de eventdescription.m_text. Si no hay
    # descripción (None), la función asigna "Unknown Region" por defecto.
    def test_7_region_ausente_da_unknown_region(self):
        """Sin eventdescription: region queda como 'Unknown Region'."""
        # Fila con region None (= eventdescription no tiene registro)
        fila_sin_region = dict(FILA_ORIGEN, region=None)
        ejecutar_con_mock("csn_test_region", [fila_sin_region])

        with open(self.ruta_evento(), encoding="utf-8") as f:
            campos = f.readline().split(";")

        # El campo region (posición 17) debe ser "Unknown Region"
        self.assertEqual(campos[17], "Unknown Region",
                         "Sin eventdescription, region debe ser 'Unknown Region'")

    # =====================================================================
    # TEST 8: Profundidad 0.0 → se escribe "0 km" (sin decimales)
    # =====================================================================
    # La función trunca la profundidad a entero con int(). Un valor de 0.0
    # debe escribirse como "0 km", no como "0.0 km" ni como "km".
    def test_8_profundidad_cero(self):
        """Profundidad 0.0 km: se escribe '0 km'."""
        fila_prof_cero = dict(FILA_ORIGEN, profundidad_km=0.0)
        ejecutar_con_mock("csn_test_prof0", [fila_prof_cero])

        with open(self.ruta_evento(), encoding="utf-8") as f:
            campos = f.readline().split(";")

        # Profundidad (posición 10) debe ser "0 km"
        self.assertEqual(campos[10], "0 km",
                         "Profundidad 0.0 debe escribirse como '0 km'")


if __name__ == "__main__":
    unittest.main()
