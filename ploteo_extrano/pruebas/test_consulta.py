# Tests de consulta_evento.py con BD SIMULADA.
# No requieren servidor PostgreSQL ni red.
import datetime
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import consulta_evento

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


def cursor_mock(filas):
    """Cursor falso: cada fetchone() consume una entrada de 'filas'."""
    it = iter(filas)
    fake = mock.MagicMock()
    fake.fetchone.side_effect = lambda: next(it, None)
    return fake


class BaseConsulta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="newpt_test_")
        self.viejo_env = os.environ.get("NEWPT_DATA_DIR")
        os.environ["NEWPT_DATA_DIR"] = self.tmp
        # La consulta resuelve la ruta en cada llamada: basta con el entorno.

    def tearDown(self):
        if self.viejo_env is None:
            os.environ.pop("NEWPT_DATA_DIR", None)
        else:
            os.environ["NEWPT_DATA_DIR"] = self.viejo_env

    def ruta_tmp(self):
        return os.path.join(self.tmp, "evento_data.txt")

    def consultar(self, filas_origen, filas_evento=None):
        """Ejecuta consultar_por_fecha_creacion() con psycopg2 simulado."""
        cur = cursor_mock([filas_origen] if filas_evento is None
                          else [filas_origen, filas_evento])
        conn = mock.MagicMock()
        conn.cursor.return_value = cur
        with mock.patch("psycopg2.connect", return_value=conn) as mk:
            salida = io.StringIO()
            with redirect_stdout(salida):
                consulta_evento.consultar_por_fecha_creacion("csn_sc62026nkkbb")
        return salida.getvalue(), mk.called


class TestFormatoSalida(BaseConsulta):
    def test_b1_b2_b3_b4_formato_19_campos(self):
        self.consultar(FILA_ORIGEN)
        with open(self.ruta_tmp(), encoding="utf-8") as f:
            linea = f.readline().rstrip("\n")
        campos = linea.split(";")
        self.assertEqual(len(campos), 19)
        self.assertEqual(campos[0], "2026-08-21 14:32:05")       # B2
        self.assertEqual(campos[3], "4.6")                        # magnitud
        self.assertEqual(campos[4], "Ml")
        self.assertEqual(campos[8], "35.42 S")                    # B3
        self.assertEqual(campos[9], "71.62 W")                    # B3
        self.assertEqual(campos[10], "95 km")   # B4: se trunca a entero
        self.assertEqual(campos[-1], "csn_sc62026nkkbb")

    def test_b7_magnitud_none_queda_vacia(self):
        fila = dict(FILA_ORIGEN, magnitud=None, tipo_magnitud=None)
        self.consultar(fila)
        with open(self.ruta_tmp(), encoding="utf-8") as f:
            campos = f.readline().split(";")
        self.assertEqual(campos[3], "")   # sin valor de magnitud
        self.assertEqual(campos[4], "M")  # tipo por defecto ("M s/d" aguas abajo)


class TestComportamiento(BaseConsulta):
    def test_b5_id_inexistente_no_escribe_archivo(self):
        salida, conecto = self.consultar(None, None)
        self.assertFalse(os.path.exists(self.ruta_tmp()))
        self.assertTrue(conecto)

    def test_b6_limpieza_preventiva_del_tmp(self):
        viejo = self.ruta_tmp()
        with open(viejo, "w") as f:
            f.write("residuo de un evento anterior")
        self.consultar(None, None)
        self.assertFalse(os.path.exists(viejo))

    def test_b8_origen_no_preferido_avisa_y_no_escribe(self):
        fila = dict(FILA_ORIGEN, id_evento=None)
        salida, _ = self.consultar(fila)
        self.assertIn("NO es la solución preferida", salida)
        self.assertFalse(os.path.exists(self.ruta_tmp()))


if __name__ == "__main__":
    unittest.main()
