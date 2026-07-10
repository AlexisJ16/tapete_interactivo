"""Genera una traza REAL del protocolo de comunicacion PC <-> cerebro del tapete.

Evidencia para la seccion 4.4 (protocolo de comunicacion) y "comandos funcionando".

Demo 1: comunicacion por TCP sobre un puerto real. Un cliente (el rol del dashboard)
se conecta al servidor del tapete y hace ping -> hello. Es EXACTAMENTE el transporte
que usa el ESP32 (servidor TCP en el puerto 3333); pasar del simulador al hardware es
solo cambiar la IP.

Demos 2-4: dialogo completo de una partida en cada uno de los tres modos (Velocidad,
Memoria, Equilibrio), byte a byte. Cada escenario se lee de shared/golden_vectors.json
y se reproduce contra el MISMO GameCore que corre en el ESP32 (cargado como .so). Esos
mismos escenarios los verifica la suite de pruebas en cada corrida, asi que la traza es
reproducible exactamente.

    python docs/evidencia/ejecucion/gen_traza_protocolo.py
"""
import json
import os
import socket
import sys
import time

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "simulator"))

from core_bridge import CoreBridge      # noqa: E402
from servidor import ServidorTapete     # noqa: E402

GOLDEN = os.path.join(RAIZ, "shared", "golden_vectors.json")
NOMBRE_MODO = {1: "Memoria", 2: "Velocidad", 3: "Equilibrio"}
LINEAS = []


def out(s=""):
    LINEAS.append(s)


def demo_tcp():
    out("=" * 72)
    out(" DEMO 1 - Comunicacion por TCP (puerto real), identica a la del ESP32")
    out("=" * 72)
    out(" El servidor expone el mismo protocolo de lineas JSON que el ESP32 real")
    out(" (que escucha en el puerto 3333). El dashboard se conecta como cliente.")
    out("")
    srv = ServidorTapete(host="127.0.0.1", puerto=0)   # puerto efimero
    srv.iniciar()
    try:
        cli = socket.create_connection(("127.0.0.1", srv.puerto), timeout=3)
        cli.settimeout(3)
        out(f" [cliente conectado a 127.0.0.1:{srv.puerto}]")
        out("")
        linea = '{"cmd":"ping"}'
        cli.sendall((linea + "\n").encode("utf-8"))
        out(f" PC      -> cerebro : {linea}")
        buf = b""
        while b"\n" not in buf:
            buf += cli.recv(1024)
        respuesta = buf.split(b"\n", 1)[0].decode("utf-8")
        out(f" cerebro -> PC      : {respuesta}")
        cli.close()
    finally:
        srv.detener()
    out("")


def reproducir_traza(escenario):
    """Reproduce el timeline del escenario mostrando el dialogo PC<->cerebro."""
    core = CoreBridge()

    def drenar():
        for ev in core.drenar_eventos():
            out(f" cerebro -> PC      : {ev}")

    cfg = escenario.get("config", {})
    if "seed" in cfg:
        linea = json.dumps({"cmd": "set_seed", "seed": cfg["seed"]}, separators=(",", ":"))
        core.comando(linea)
        out(f" PC      -> cerebro : {linea}")
        drenar()

    t_prev = None
    for paso in escenario.get("timeline", []):
        t = paso.get("t", 0)
        core.set_millis(t)
        core.actualizar()
        drenar()
        if t != t_prev:
            t_prev = t
        if "cmd" in paso:
            linea = json.dumps(paso["cmd"], separators=(",", ":"))
            core.comando(linea)
            out(f" PC      -> cerebro : {linea}   (t={t} ms)")
            drenar()
        elif "press" in paso:
            core.pisar(int(paso["press"]))
            out(f" [pisada casilla {paso['press']} <- equivale al FSR]   (t={t} ms)")
            drenar()
    core.cerrar()


def demo_modo(escenarios, nombre_escenario, n):
    esc = next(e for e in escenarios if e["name"] == nombre_escenario)
    modo = esc["config"]["mode"]
    out("=" * 72)
    out(f" DEMO {n} - Modo {modo} ({NOMBRE_MODO[modo]}) — dialogo completo del protocolo")
    out(f" Escenario determinista = golden vector '{nombre_escenario}'")
    out("=" * 72)
    out("")
    reproducir_traza(esc)
    out("")


def main():
    with open(GOLDEN, encoding="utf-8") as f:
        escenarios = json.load(f)["scenarios"]

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    out(f"# Traza del protocolo de comunicacion del Tapete Interactivo  ({ts})")
    out("# Generada por docs/evidencia/ejecucion/gen_traza_protocolo.py")
    out("# 'cerebro' = nucleo GameCore corriendo como simulador de software.")
    out("# El protocolo es identico al del ESP32 real (mismo codigo C++).")
    out("# Las mismas lineas viajan por Serial 115200 o TCP 3333.")
    out("")
    demo_tcp()
    demo_modo(escenarios, "velocidad_strict_dos_aciertos", 2)
    demo_modo(escenarios, "memoria_juego_completo", 3)
    demo_modo(escenarios, "equilibrio_juego_completo", 4)
    out(" Leyenda de eventos (ver protocol.md, seccion 3):")
    out("   state = cambio de estado del motor    led   = encendido/apagado de un LED")
    out("   press = pisada detectada              sound = peticion de audio 000X.mp3")
    out("   score = metricas (aciertos/fallos, tiempo de reaccion, ronda)")
    print("\n".join(LINEAS))


if __name__ == "__main__":
    main()
