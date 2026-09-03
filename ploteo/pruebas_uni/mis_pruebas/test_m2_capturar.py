# Misión M2 — Tests de parsear_linea_evento (capturar.py)
# ==========================================================================
# Esta función toma la línea de texto de evento_data.txt (generada por
# consultar_por_fecha_creacion) y la convierte en un diccionario con los
# campos que plotear_evento() necesita para graficar.
#
# La línea tiene 19 campos separados por ";" y esta función:
# 1. Valida que la línea tenga "csn_" (marca de identificación del CSN)
# 2. Extrae lat/lon convirtiendo hemisferios (S/W → negativo)
# 3. Convierte magnitud y profundidad de string a float
# 4. Maneja errores (profundidad corrupta, magnitud vacía, etc.)
#
# No necesita mock de BD porque es una función pura: solo transforma texto.
# ==========================================================================

import io
import sys
import os
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import capturar


# --- LÍNEA DE EJEMPLO VÁLIDA ---
# Replica exactamente lo que consultar_por_fecha_creacion escribe en evento_data.txt.
# Los campos vacíos (posiciones 1, 2, 13, 14) se dejan con ";" vacíos.
LINEA_VALIDA = (
    "2026-08-21 14:32:05;;;"           # 0: fecha
    "4.6;"                              # 1: magnitud (vacío en este caso)
    "Ml;"                               # 2: tipo magnitud (vacío en este caso)
    "128;"                              # 3: fases
    "0.45;"                             # 4: rms
    "212;"                              # 5: azgap
    "35.42 S;"                          # 6: latitud con hemisferio
    "71.62 W;"                          # 7: longitud con hemisferio
    "95.3 km;"                          # 8: profundidad con unidad
    "from location;"                    # 9: cadena fija
    "confirmed;;"                       # 10: estatus
    "2;"                                # 11: fijo
    "CSN;"                              # 12: agencia
    "operador1;"                        # 13: operador
    "Region del Maule;"                 # 14: region
    "csn_sc62026nkkbb"                  # 15: event_id (DEBE contener "csn_")
)


class TestM2ParsearLinea(unittest.TestCase):
    """Tests de parsear_linea_evento(): cómo transforma texto en datos."""

    # =====================================================================
    # TEST 1: Línea válida completa → dict con todos los campos correctos
    # =====================================================================
    # El "camino feliz": una línea bien formateada con todos los campos.
    # Verificamos que cada campo se extrae correctamente.
    def test_1_linea_valida_campos_correctos(self):
        """Línea completa: extrae fecha, coords, mag, prof e id."""
        ev = capturar.parsear_linea_evento(LINEA_VALIDA)

        # No debe ser None (la línea es válida)
        self.assertIsNotNone(ev, "Una línea válida no debe devolver None")

        # Verificamos cada campo extraído
        self.assertEqual(ev["fecha"], "2026-08-21 14:32:05")
        self.assertEqual(ev["lat"], -35.42)       # S → negativo
        self.assertEqual(ev["lon"], -71.62)       # W → negativo
        self.assertEqual(ev["prof"], 95.3)        # se extrae el número
        self.assertEqual(ev["mag"], 4.6)
        self.assertEqual(ev["tipo_mag"], "Ml")
        self.assertEqual(ev["texto_magnitud"], "4.6 Ml")
        self.assertEqual(ev["event_id"], "csn_sc62026nkkbb")

    # =====================================================================
    # TEST 2: Magnitud vacía → "M s/d" (Sin Datos)
    # =====================================================================
    # Cuando el campo de magnitud está vacío en la línea, la función
    # asigna mag=0.0 y texto_magnitud="M s/d (tipo)". Esto lo interpreta
    # capturar.py para mostrar "M s/d" en el título del gráfico.
    def test_2_magnitud_vacia_da_m_sd(self):
        """Magnitud vacía: mag=0.0 y texto='M s/d (Ml)'."""
        # Reemplazamos "4.6" por vacío en el campo de magnitud
        linea = LINEA_VALIDA.replace("4.6;", ";", 1)
        ev = capturar.parsear_linea_evento(linea)

        self.assertIsNotNone(ev)
        self.assertEqual(ev["mag"], 0.0)
        self.assertEqual(ev["texto_magnitud"], "M s/d (Ml)")

    # =====================================================================
    # TEST 3: Profundidad corrupta → usa valor por defecto 10.0 km
    # =====================================================================
    # Si la profundidad no se puede convertir a número (por ejemplo,
    # aparece "Moments" en vez de "95.3 km"), la función asigna 10.0 km
    # por defecto para que el script no se caiga.
    def test_3_profundidad_corrupta_usa_default(self):
        """Profundidad no numérica: usa 10.0 km por defecto."""
        linea = LINEA_VALIDA.replace("95.3 km;", "Moments;", 1)
        salida = io.StringIO()
        with redirect_stdout(salida):
            ev = capturar.parsear_linea_evento(linea)

        self.assertIsNotNone(ev)
        self.assertEqual(ev["prof"], 10.0)
        # Verificamos que imprimió el aviso
        self.assertIn("[Aviso]", salida.getvalue())
        self.assertIn("10 km", salida.getvalue())

    # =====================================================================
    # TEST 4: Línea incompleta (< 12 campos) → None
    # =====================================================================
    # Si la línea tiene menos de 12 campos, no hay suficientes datos
    # para extraer lat/lon/etc. La función devuelve None.
    def test_4_linea_incompleta_devuelve_none(self):
        """Menos de 12 campos: la función rechaza la línea."""
        # Tomamos solo los primeros 11 campos de la línea válida
        corta = ";".join(LINEA_VALIDA.split(";")[:11])
        resultado = capturar.parsear_linea_evento(corta)
        self.assertIsNone(resultado, "Línea con <12 campos debe devolver None")

    # =====================================================================
    # TEST 5: Sin marca "csn_" → None
    # =====================================================================
    # La función requiere que el event_id contenga "csn_" para validar
    # que la línea es del CSN. Si no lo tiene, la descarta.
    def test_5_sin_marca_csn_devuelve_none(self):
        """Sin 'csn_' en el event_id: la función rechaza la línea."""
        # Reemplazamos el ID del CSN por uno genérico sin "csn_"
        linea_ajena = LINEA_VALIDA.replace("csn_sc62026nkkbb", "otro_2026xyz")
        self.assertIsNone(capturar.parsear_linea_evento(linea_ajena))
        # También con string vacío y None
        self.assertIsNone(capturar.parsear_linea_evento(""))
        self.assertIsNone(capturar.parsear_linea_evento(None))

    # =====================================================================
    # TEST 6: Hemisferio Norte → latitud positiva
    # =====================================================================
    # Cuando la latitud tiene "N" en vez de "S", debe quedarse positiva.
    def test_6_hemisferio_norte_lat_positiva(self):
        """Latitud con N: valor positivo."""
        linea = LINEA_VALIDA.replace("35.42 S;", "35.42 N;", 1)
        ev = capturar.parsear_linea_evento(linea)
        self.assertEqual(ev["lat"], 35.42,
                         "Latitud con N debe ser positiva")

    # =====================================================================
    # TEST 7: Hemisferio Este → longitud positiva
    # =====================================================================
    # Cuando la longitud tiene "E" en vez de "W", debe quedarse positiva.
    def test_7_hemisferio_este_lon_positiva(self):
        """Longitud con E: valor positivo."""
        linea = LINEA_VALIDA.replace("71.62 W;", "71.62 E;", 1)
        ev = capturar.parsear_linea_evento(linea)
        self.assertEqual(ev["lon"], 71.62,
                         "Longitud con E debe ser positiva")

    # =====================================================================
    # TEST 8: Longitud con "O" (español) en vez de "W" → negativa
    # =====================================================================
    # La función acepta tanto "W" (inglés) como "O" (español: Oeste).
    # Ambas deben producir longitud negativa.
    def test_8_longitud_o_es_negativa(self):
        """Longitud con 'O' (Oeste): se interpreta como negativa."""
        linea = LINEA_VALIDA.replace("71.62 W;", "71.62 O;", 1)
        ev = capturar.parsear_linea_evento(linea)
        self.assertEqual(ev["lon"], -71.62,
                         "Longitud con 'O' debe ser negativa igual que 'W'")

    # =====================================================================
    # TEST 9: Profundidad 0.0 km → se parsea como 0.0
    # =====================================================================
    # Una profundidad de 0.0 km es válida (sismo en el lecho marino).
    # La función debe extraer el número correctamente.
    def test_9_profundidad_cero_km(self):
        """Profundidad 0.0 km: se parsea como 0.0."""
        linea = LINEA_VALIDA.replace("95.3 km;", "0.0 km;", 1)
        ev = capturar.parsear_linea_evento(linea)
        self.assertIsNotNone(ev)
        self.assertEqual(ev["prof"], 0.0,
                         "Profundidad 0.0 km debe ser 0.0")


if __name__ == "__main__":
    unittest.main()
