#!/usr/bin/env python3
"""
newpt_servidor.py - Daemon residente de NewPT.

Mantiene en RAM de forma permanente los módulos pesados (matplotlib, cartopy,
numpy, PIL, adjustText) y los datos que el graficador usa (relieve_chile.tif,
grillas/topo_chile.npy, grillas/slab2_global.npy). Así, cada nuevo evento se
dibuja sin re-importar módulos ni re-leer datos desde disco, eliminando la
lentitud de arranque (típicamente 20-30 s en la primera ejecución tras un
periodo sin uso).

newpt.sh se comunica con este daemon a través de un socket UNIX:
  nuevas líneas de evento -> el daemon reutiliza LA MISMA ventana 2D para
  dibujar cada evento (cierra la figura del evento anterior y dibuja el nuevo).

Uso (lo lanza newpt.sh en background):
  newpt_servidor
"""
import os
import sys
import socket
import threading
import queue
import time


def ruta_datos():
    env = os.environ.get("NEWPT_DATA_DIR")
    if env:
        return env
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DATOS = ruta_datos()
SOCK = os.path.join(DATOS, ".newpt.sock")
PID = os.path.join(DATOS, ".newpt.pid")
COLA = queue.Queue()


def _precalentar_datos():
    """Lee los datos pesados para dejarlos en el page cache / RAM del proceso."""
    leidos = []
    rel = os.path.join(DATOS, "relieve_chile.tif")
    topo = os.path.join(DATOS, "grillas", "topo_chile.npy")
    slab = os.path.join(DATOS, "grillas", "slab2_global.npy")
    for arch in (rel, topo, slab):
        if os.path.exists(arch):
            try:
                with open(arch, "rb") as fh:
                    while fh.read(8 * 1024 * 1024):
                        pass
                leidos.append(os.path.basename(arch))
            except OSError:
                pass
    return leidos


def hilo_socket():
    """Acepta conexiones del socket y encola las líneas de evento recibidas."""
    try:
        if os.path.exists(SOCK):
            os.remove(SOCK)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(SOCK)
        server.listen(5)
        os.chmod(SOCK, 0o600)
        while True:
            conn, _ = server.accept()
            try:
                datos = conn.recv(65536).decode("utf-8", errors="replace")
            finally:
                conn.close()
            linea = (datos or "").strip()
            if linea:
                COLA.put(linea)
    except Exception as e:
        print(f"[Servidor] Error en el hilo del socket: {e}", flush=True)


def main():
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import numpy as np  # noqa: F401  (precarga)
    import PIL  # noqa: F401
    import capturar  # reutiliza parsear_linea_evento / plotear_evento

    # Ancla los módulos y los datos pesados en RAM / page cache de este proceso.
    leidos = _precalentar_datos()
    print(f"[Servidor] Datos precargados: {', '.join(leidos) if leidos else 'ninguno'}", flush=True)

    try:
        with open(PID, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass

    threading.Thread(target=hilo_socket, daemon=True).start()
    print(f"[Servidor] Daemon residente listo (PID {os.getpid()}). Socket: {SOCK}", flush=True)

    # Figura de control invisible que mantiene vivo un timer sobre el bucle de
    # Tk del hilo principal. No se cierra con los eventos (atributo marcador).
    ctrl = plt.figure()
    ctrl._newpt_control = True
    try:
        ctrl.canvas.manager.window.withdraw()
    except Exception:
        pass

    estado = {"procesando": False}

    def poll():
        # Corre en el hilo principal (timer de Tk). Procesa un evento a la vez.
        if estado["procesando"]:
            return
        try:
            linea = COLA.get_nowait()
        except queue.Empty:
            return
        estado["procesando"] = True
        try:
            ev = capturar.parsear_linea_evento(linea)
            if ev is None:
                print("[Servidor] Línea de evento no válida (ignorada).", flush=True)
                return
            print(f"[Servidor] Dibujando evento {ev['event_id']}...", flush=True)
            capturar.plotear_evento(
                ev["fecha"], ev["lat"], ev["lon"], ev["prof"],
                ev["mag"], ev["event_id"], ev["texto_magnitud"],
                bloquear=False,
            )
            print(f"[Servidor] Evento {ev['event_id']} mostrado.", flush=True)
        except Exception as e:
            print(f"[Servidor] Fallo al dibujar: {e}", flush=True)
        finally:
            estado["procesando"] = False

    timer = ctrl.canvas.new_timer(interval=50)
    timer.add_callback(poll)
    timer.start()

    try:
        plt.show()
    finally:
        timer.stop()
        for sock_path in (SOCK,):
            try:
                if os.path.exists(sock_path):
                    os.remove(sock_path)
            except OSError:
                pass
        try:
            if os.path.exists(PID):
                os.remove(PID)
        except OSError:
            pass
        print("[Servidor] Daemon detenido. Socket y PID limpiados.", flush=True)


if __name__ == "__main__":
    main()