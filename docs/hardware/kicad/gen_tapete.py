"""Generador del esquematico del Tapete Interactivo (docs/hardware/kicad/tapete.kicad_sch).

Fuente de verdad de conectividad: docs/hardware/cableado.md §1/§4 + Config.h.
Construccion CUMULATIVA por etapas (ERC+PDF incremental, TDD del esquematico):
    esp32  -> ESP32 + rieles de potencia (+5V/+3V3/GND + PWR_FLAG) + no_connect
    fsr    -> + banco de 6 FSR (divisor 3V3-FSR-nodo-10k-GND, nodo->ADC)
    uln    -> + ULN2803A + 6 grupos LED (110 Ohm, 5V->anodo, catodo->OUTk, INk<-GPIO)
    dfplayer (=all) -> + DFPlayer + parlante 4ohm + desacoples

Uso:  .venv/bin/python gen_tapete.py --stage {esp32|fsr|uln|dfplayer|all} [--project]
"""
import sys
sys.path.insert(0, "/home/alexis/code/tapete_interactivo/docs/hardware/kicad")
import kisch as K

HERE = "/home/alexis/code/tapete_interactivo/docs/hardware/kicad"
STAGES = ["esp32", "fsr", "uln", "dfplayer"]

# --- Simbolos custom (tipados) ----------------------------------------------
# ESP32 DevKit 30-pin. Izquierda = header superior (Fila A); derecha = header
# inferior (Fila J). Numeros 1-30 = posicion fisica (col 25->39). Ver cableado.md.
ESP32_L = [  # (num, nombre, tipo)
    ("1", "VIN", "power_in"), ("2", "GND", "power_in"),
    ("3", "IO13", "bidirectional"), ("4", "IO12", "bidirectional"),
    ("5", "IO14", "bidirectional"), ("6", "IO27", "bidirectional"),
    ("7", "IO26", "bidirectional"), ("8", "IO25", "bidirectional"),
    ("9", "IO33", "input"), ("10", "IO32", "input"),
    ("11", "IO35", "input"), ("12", "IO34", "input"),
    ("13", "IO39_VN", "input"), ("14", "IO36_VP", "input"),
    ("15", "EN", "input"),
]
ESP32_R = [
    ("16", "3V3", "power_in"), ("17", "GND", "power_in"),
    ("18", "IO15", "bidirectional"), ("19", "IO2", "bidirectional"),
    ("20", "IO4", "bidirectional"), ("21", "IO16_RX2", "bidirectional"),
    ("22", "IO17_TX2", "bidirectional"), ("23", "IO5", "bidirectional"),
    ("24", "IO18", "bidirectional"), ("25", "IO19", "bidirectional"),
    ("26", "IO21", "bidirectional"), ("27", "IO3_RX0", "bidirectional"),
    ("28", "IO1_TX0", "bidirectional"), ("29", "IO22", "bidirectional"),
    ("30", "IO23", "bidirectional"),
]
# DFPlayer Mini (custom tipado). Izquierda = alimentacion/UART; derecha = audio/SD.
DF_L = [
    ("1", "VCC", "power_in"), ("7", "GND", "power_in"),
    ("2", "RX", "input"), ("3", "TX", "output"),
]
DF_R = [
    ("6", "SPK1", "passive"), ("8", "SPK2", "passive"),
]

ESP32_DEF = K.make_rect_symbol("ESP32-DevKit-30", ESP32_L, ESP32_R, body_w=25.4)
DF_DEF = K.make_rect_symbol("DFPlayer-Mini", DF_L, DF_R, body_w=20.32)

# GPIO (num de pin ESP32) por senal, para no repetir numeros magicos.
FSR_PIN = {1: "14", 2: "13", 3: "12", 4: "11", 5: "10", 6: "9"}   # FSRk -> pin ESP32
LED_PIN = {1: "20", 2: "23", 3: "24", 4: "25", 5: "26", 6: "30"}  # LEDk -> pin ESP32
# ULN2803A: INk = pin k ; OUTk (OUT1=18..OUT6=13)
ULN_OUT = {1: "18", 2: "17", 3: "16", 4: "15", 5: "14", 6: "13"}


# --- Geometria del plano (hoja A3 = 420 x 297 mm; margen util ~15 mm) --------
# Bloques funcionales, de izquierda a derecha: sensado | computo | actuacion.
# Todo debe caber dentro del marco: la version anterior sacaba la 6a columna de
# LEDs fuera de la hoja y dejaba el cajetin vacio.
X_FSR, Y_FSR = 30.0, 55.0        # banco de 6 canales de sensado
PASO_FSR = 24.0
X_ESP, Y_ESP = 200.0, 110.0      # microcontrolador (centro del plano)
X_ULN, Y_ULN = 285.0, 105.0      # driver de LEDs
X_LED, Y_LED = 340.0, 60.0       # 6 grupos de LED, en 2 filas x 3 columnas
PASO_LED_X, PASO_LED_Y = 25.0, 55.0
X_DF, Y_DF = 205.0, 215.0        # audio
X_PWR, Y_PWR = 30.0, 200.0       # rieles y desacoplo


def power_rails(d: K.Design) -> None:
    """Simbolos de potencia + PWR_FLAG por riel (una fuente ERC por net)."""
    d.add(K.Comp("#PWR01", "power", "+5V", "+5V", X_PWR, Y_PWR))
    d.add(K.Comp("#FLG01", "power", "PWR_FLAG", "PWR_FLAG", X_PWR + 15, Y_PWR))
    d.connect("+5V", ("#PWR01", "1"), ("#FLG01", "1"))
    d.add(K.Comp("#PWR02", "power", "+3V3", "+3V3", X_PWR + 40, Y_PWR))
    d.add(K.Comp("#FLG02", "power", "PWR_FLAG", "PWR_FLAG", X_PWR + 55, Y_PWR))
    d.connect("+3V3", ("#PWR02", "1"), ("#FLG02", "1"))
    d.add(K.Comp("#PWR03", "power", "GND", "GND", X_PWR, Y_PWR + 30))
    d.add(K.Comp("#FLG03", "power", "PWR_FLAG", "PWR_FLAG", X_PWR + 15, Y_PWR + 30))
    d.connect("GND", ("#PWR03", "1"), ("#FLG03", "1"))


def sub_esp32(d: K.Design) -> None:
    d.add(K.Comp("U1", "tapete", "ESP32-DevKit-30", "ESP32-DevKit-30", X_ESP, Y_ESP))
    d.connect("+5V", ("U1", "1"))
    d.connect("+3V3", ("U1", "16"))
    d.connect("GND", ("U1", "2"), ("U1", "17"))
    # Pines del header sin uso -> no_connect (evita "pin no conectado").
    d.no_connect("U1", "3", "4", "5", "6", "7", "8", "15", "18", "19", "27", "28", "29")
    power_rails(d)
    d.notes.append((X_FSR, 30,
        "BLOQUE 1 - SENSADO (3V3): 6 canales  3V3 -[FSR]- nodo -[10k]- GND ; nodo -> ADC1"))
    d.notes.append((X_LED - 10, 30,
        "BLOQUE 3 - ACTUACION (5V): 5V -[110R]- anodo LED ; catodo -> OUTk del ULN2803A"))
    d.notes.append((X_PWR, Y_PWR + 45,
        "Alimentacion: USB del PC -> VIN(5V) del ESP32. Los rieles 3V3 y 5V NUNCA se puentean.\\n"
        "Conectividad definida por etiquetas de net (label): mismo nombre = mismo nodo."))


def sub_fsr(d: K.Design) -> None:
    """6 canales: 3V3 -[FSR]- nodo -[10k]- GND ; nodo -> ADC (input)."""
    for k in range(1, 7):
        x = X_FSR + (k - 1) * PASO_FSR
        rv, r = f"RV{k}", f"R{k}"
        d.add(K.Comp(rv, "Device", "R_Variable", f"FSR{k}", x, Y_FSR, footprint=""))
        d.add(K.Comp(r, "Device", "R", "10k", x, Y_FSR + 40))
        node = f"FSR{k}_ADC"
        d.connect("+3V3", (rv, "1"))
        d.connect(node, (rv, "2"), (r, "1"), ("U1", FSR_PIN[k]))
        d.connect("GND", (r, "2"))


def sub_uln(d: K.Design) -> None:
    """ULN2803A + 6 grupos LED. 5V-[110R]-anodo ; catodo-OUTk ; INk<-GPIO."""
    d.add(K.Comp("U2", "Transistor_Array", "ULN2803A", "ULN2803A", X_ULN, Y_ULN))
    d.connect("GND", ("U2", "9"))          # pin 9 = GND
    d.connect("+5V", ("U2", "10"))         # pin 10 = COM -> 5V
    d.no_connect("U2", "7", "8", "11", "12")  # IN7/IN8, OUT7/OUT8 sin uso
    for k in range(1, 7):
        # 2 filas x 3 columnas: refleja la disposicion fisica de las casillas.
        col, fila = (k - 1) % 3, (k - 1) // 3
        x = X_LED + col * PASO_LED_X
        y = Y_LED + fila * PASO_LED_Y
        rser, led = f"R{6 + k}", f"D{k}"   # R7..R12 = serie 110 Ohm ; D1..D6 = LED
        d.add(K.Comp(rser, "Device", "R", "110", x, y))
        d.add(K.Comp(led, "Device", "LED", "LED", x, y + 25))
        d.connect("+5V", (rser, "1"))
        d.connect(f"LED{k}_A", (rser, "2"), (led, "2"))    # anodo (pin 2 = A)
        d.connect(f"LED{k}_K", (led, "1"), ("U2", ULN_OUT[k]))  # catodo (pin 1 = K) -> OUTk
        d.connect(f"GPIO_LED{k}", ("U1", LED_PIN[k]), ("U2", str(k)))  # GPIO -> INk


def sub_dfplayer(d: K.Design) -> None:
    """DFPlayer + parlante 4ohm + desacoples. RX<-1k<-TX2 ; TX->RX2 ; SPK diferencial."""
    d.add(K.Comp("U3", "tapete", "DFPlayer-Mini", "DFPlayer-Mini", X_DF, Y_DF))
    d.add(K.Comp("R13", "Device", "R", "1k", X_DF - 35, Y_DF - 10))
    d.add(K.Comp("LS1", "Device", "Speaker", "4ohm", X_DF + 50, Y_DF))
    d.add(K.Comp("C1", "Device", "C_Polarized", "1000uF", X_PWR + 75, Y_PWR))
    d.add(K.Comp("C2", "Device", "C_Polarized", "100uF", X_PWR + 95, Y_PWR))
    d.add(K.Comp("C3", "Device", "C", "100nF", X_PWR + 115, Y_PWR))
    d.connect("+5V", ("U3", "1"), ("C1", "1"), ("C2", "1"), ("C3", "1"))
    d.connect("GND", ("U3", "7"), ("C1", "2"), ("C2", "2"), ("C3", "2"))
    # UART: ESP32 TX2(17) -[1k]-> DFPlayer RX ; DFPlayer TX -> ESP32 RX2(16)
    d.connect("DF_UART_TX", ("U1", "22"), ("R13", "1"))
    d.connect("DF_RX", ("R13", "2"), ("U3", "2"))
    d.connect("DF_TX", ("U3", "3"), ("U1", "21"))
    # Parlante diferencial (NO aterrizar)
    d.connect("SPK_P", ("U3", "6"), ("LS1", "1"))
    d.connect("SPK_N", ("U3", "8"), ("LS1", "2"))
    d.notes.append((X_DF - 40, Y_DF + 45,
        "BLOQUE 4 - AUDIO (5V): UART2 del ESP32 -[1k]-> RX del DFPlayer ; TX -> RX2.\\n"
        "Contingencia GPIO16 (cableado.md, Paso 7): GPIO16 no es 5V-tolerante. Si el TX\\n"
        "del DFPlayer mide ~5 V, intercalar divisor 1k+2k en DF_TX. Nominal (3,3 V) = directo."))


SUBS = {"esp32": sub_esp32, "fsr": sub_fsr, "uln": sub_uln, "dfplayer": sub_dfplayer}


TITULO = K.TitleBlock(
    title="Tapete Interactivo Terapeutico - Esquematico del sistema",
    company="Universidad Santiago de Cali - Ingenieria Electronica",
    date="2026-07-09",   # fija: la salida debe ser reproducible byte a byte
    rev="1.0",
    comments=(
        "Fuente de verdad: firmware/lib/GameCore/Config.h (pines) y docs/hardware/cableado.md",
        "Generado por docs/hardware/kicad/gen_tapete.py - no editar el .kicad_sch a mano",
        "Alimentacion unica: USB del PC. Los rieles 3V3 y 5V no se puentean.",
    ),
)


def build(stage: str) -> K.Design:
    d = K.Design(project="tapete", paper="A3", title_block=TITULO)
    d.custom_defs["tapete:ESP32-DevKit-30"] = K.to_lib_id(ESP32_DEF, "tapete", "ESP32-DevKit-30")
    d.custom_defs["tapete:DFPlayer-Mini"] = K.to_lib_id(DF_DEF, "tapete", "DFPlayer-Mini")
    upto = STAGES.index("dfplayer" if stage == "all" else stage)
    for s in STAGES[:upto + 1]:
        SUBS[s](d)
    return d


def write_project() -> None:
    """Escribe .kicad_sym + sym-lib-table + .kicad_pro (limpia lib_symbol_issues)."""
    K.write_symlib(f"{HERE}/tapete.kicad_sym", [ESP32_DEF, DF_DEF])
    with open(f"{HERE}/sym-lib-table", "w") as f:
        f.write('(sym_lib_table\n\t(version 7)\n'
                '\t(lib (name "tapete")(type "KiCad")'
                '(uri "${KIPRJMOD}/tapete.kicad_sym")(options "")(descr "Simbolos del Tapete"))\n)\n')
    with open(f"{HERE}/tapete.kicad_pro", "w") as f:
        f.write('{\n  "meta": {"filename": "tapete.kicad_pro", "version": 1},\n'
                '  "schematic": {},\n  "libraries": {"pinned_symbol_libs": []},\n'
                '  "sheets": [], "boards": []\n}\n')


if __name__ == "__main__":
    stage = "all"
    for a in sys.argv[1:]:
        if a.startswith("--stage="):
            stage = a.split("=", 1)[1]
        elif a == "--stage":
            pass
        elif a in STAGES or a == "all":
            stage = a
    if "--project" in sys.argv:
        write_project()
        print("proyecto escrito (tapete.kicad_sym / sym-lib-table / tapete.kicad_pro)")
    K.write(build(stage), f"{HERE}/tapete.kicad_sch")
    print(f"tapete.kicad_sch escrito (stage={stage})")
