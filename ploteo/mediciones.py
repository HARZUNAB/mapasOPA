#!/usr/bin/env python3
"""
mediciones.py - Cronometrado por fase para localizar la demora de NewPT.

NewPT tarda un tiempo anómalo (del orden de ~40 s) cuando ha pasado un
tiempo considerable desde la última ejecución, y desaparece en ejecuciones
continuas. Para ubicar dónde caen exactamente esos segundos, los scripts
del flujo (precalentar.py, consulta_evento.py, capturar.py) registran aquí
un hito por cada fase importante.

El registro se escribe en un archivo TSV persistente (newpt_metricas.tsv,
en el directorio de datos) para poder comparar una ejecución LENTA contra
una RÁPIDA. Además se imprime un resumen breve por consola con prefijo [M].

Uso desde otros scripts:
    import mediciones as m
    m.arranque("consulta")
    # ... trabajo ...
    m.hito("consulta", "conexion_fin", extra="ok")
    m.hito("consulta", "fin")
"""
import os
import sys
import time


def _ruta_datos():
    """Resuelve el directorio de datos (misma regla que precalentar/capturar)."""
    env = os.environ.get("NEWPT_DATA_DIR")
    if env:
        return env
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


_ARCHIVO = os.path.join(_ruta_datos(), "newpt_metricas.tsv")

# Referencia del proceso: monotonic (intervalos fiables) + epoch (hora real).
_t0 = None
_epoch0 = None
_script = None


def _escritor(lista):
    """Escribe la línea en el TSV sin romper por errores de E/S."""
    linea = "\t".join(str(x) for x in lista)
    try:
        with open(_ARCHIVO, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except OSError:
        pass


def arranque(script):
    """Fija el inicio del proceso y escribe el encabezado/referencia."""
    global _t0, _epoch0, _script
    _script = script
    _t0 = time.monotonic()
    _epoch0 = time.time()
    if not os.path.exists(_ARCHIVO) or os.path.getsize(_ARCHIVO) == 0:
        _escritor(["epoch_inicio", "ms_desde_arranque", "script", "fase", "extra"])
    hito(script, "arranque")


def hito(script=None, fase="", extra=""):
    """Registra los ms transcurridos desde arranque() para una fase."""
    if _t0 is None:
        return
    script = script or _script
    ms = (time.monotonic() - _t0) * 1000.0
    _escritor([f"{_epoch0:.0f}", f"{ms:.0f}", script, fase, extra])
    #print(f"[M] {script} · {fase}: {ms:.0f} ms {extra}".rstrip(), flush=True)


def ms_desde_arranque():
    """Devuelve los ms transcurridos desde arranque(), o 0 si no se llamó."""
    if _t0 is None:
        return 0.0
    return (time.monotonic() - _t0) * 1000.0


if __name__ == "__main__":
    print(f"mediciones.py -> registro: {_ARCHIVO}")
