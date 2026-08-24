# Tests unitarios de NewPT (marcha blanca).
# Ejecución:  MPLBACKEND=Agg python -m unittest discover -s tests -v
import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO

# Asegura backend sin pantalla ANTES de importar matplotlib/capturar,
# y permite ejecutar este archivo directamente desde cualquier ruta.
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import capturar

# Línea de evento_data.txt con el formato real de 19 campos que escribe
# consulta_evento.py (ver test_consulta.py: ambos deben seguir de acuerdo).
LINEA_VALIDA = (
    "2026-08-21 14:32:05;;;"   # fecha (+2 vacíos)
    "4.6;"                     # magnitud
    "Ml;"                      # tipo magnitud
    "128;"                     # fases
    "0.45;"                    # rms
    "212;"                     # azgap
    "35.42 S;"                 # latitud
    "71.62 W;"                 # longitud
    "95.3 km;"                 # profundidad
    "from location;"
    "confirmed;;"
    "2;"
    "CSN;"
    "operador1;"
    "Region del Maule;"
    "csn_sc62026nkkbb"         # event_id (último campo)
)


class TestDistancias(unittest.TestCase):
    """calcular_distancia(): haversine en km."""

    def test_a1_distancia_mismo_punto_es_cero(self):
        self.assertAlmostEqual(
            capturar.calcular_distancia(-70.65, -33.45, -70.65, -33.45), 0.0, places=6)

    def test_a2_distancia_conocida_santiago_valparaiso(self):
        d = capturar.calcular_distancia(-70.65, -33.45, -71.62, -33.05)
        self.assertAlmostEqual(d, 103.0, delta=15.0)

    def test_a3_simetria(self):
        d1 = capturar.calcular_distancia(-70.65, -33.45, -71.62, -33.05)
        d2 = capturar.calcular_distancia(-71.62, -33.05, -70.65, -33.45)
        self.assertAlmostEqual(d1, d2, places=6)


class TestRumbo(unittest.TestCase):
    """obtener_rumbo(): punto cardinal desde el origen."""

    def test_a4_norte(self):
        self.assertEqual(capturar.obtener_rumbo(0, 0, 0, 10), "N")

    def test_a5_sur(self):
        self.assertEqual(capturar.obtener_rumbo(0, 0, 0, -10), "S")

    def test_a6_este(self):
        self.assertEqual(capturar.obtener_rumbo(0, 0, 10, 0), "E")

    def test_a7_oeste(self):
        self.assertEqual(capturar.obtener_rumbo(0, 0, -10, 0), "W")


class TestRutaDatos(unittest.TestCase):
    """ruta_datos(): prioridad de NEWPT_DATA_DIR."""

    def test_a8_respeta_newpt_data_dir(self):
        viejo = os.environ.get("NEWPT_DATA_DIR")
        try:
            os.environ["NEWPT_DATA_DIR"] = "/tmp/newpt_test_datos"
            self.assertEqual(capturar.ruta_datos(), "/tmp/newpt_test_datos")
        finally:
            if viejo is None:
                os.environ.pop("NEWPT_DATA_DIR", None)
            else:
                os.environ["NEWPT_DATA_DIR"] = viejo


class TestParsearLineaEvento(unittest.TestCase):
    """parsear_linea_evento(): contrato con la línea de 19 campos."""

    def test_a9_linea_valida_completa(self):
        ev = capturar.parsear_linea_evento(LINEA_VALIDA)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["fecha"], "2026-08-21 14:32:05")
        self.assertEqual(ev["lat"], -35.42)      # S -> negativa
        self.assertEqual(ev["lon"], -71.62)      # W -> negativa
        self.assertEqual(ev["prof"], 95.3)
        self.assertEqual(ev["mag"], 4.6)
        self.assertEqual(ev["tipo_mag"], "Ml")
        self.assertEqual(ev["texto_magnitud"], "4.6 Ml")
        self.assertEqual(ev["event_id"], "csn_sc62026nkkbb")

    def test_a10_magnitud_vacia_da_m_sd(self):
        linea = LINEA_VALIDA.replace("4.6", "", 1)   # vacía el campo mag
        ev = capturar.parsear_linea_evento(linea)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["mag"], 0.0)
        self.assertEqual(ev["texto_magnitud"], "M s/d (Ml)")

    def test_a11_profundidad_corrupta_usa_default(self):
        linea = LINEA_VALIDA.replace("95.3 km;", "Moments;", 1)
        salida = StringIO()
        with redirect_stdout(salida):
            ev = capturar.parsear_linea_evento(linea)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["prof"], 10.0)
        self.assertIn("[Aviso]", salida.getvalue())
        self.assertIn("Usando valor por defecto de 10 km", salida.getvalue())

    def test_a12_linea_incompleta_se_rechaza(self):
        corta = ";".join(LINEA_VALIDA.split(";")[:11])
        self.assertIsNone(capturar.parsear_linea_evento(corta))

    def test_a13_sin_marca_csn_se_rechaza(self):
        ajena = LINEA_VALIDA.replace("csn_sc62026nkkbb", "otro_2026xyz")
        self.assertIsNone(capturar.parsear_linea_evento(ajena))
        self.assertIsNone(capturar.parsear_linea_evento(""))
        self.assertIsNone(capturar.parsear_linea_evento(None))

    def test_a14_hemisferio_norte_y_este_positivos(self):
        linea = (LINEA_VALIDA
                 .replace("35.42 S;", "35.42 N;", 1)
                 .replace("71.62 W;", "71.62 E;", 1))
        ev = capturar.parsear_linea_evento(linea)
        self.assertEqual(ev["lat"], 35.42)
        self.assertEqual(ev["lon"], 71.62)


if __name__ == "__main__":
    unittest.main()
