"""Hoja de estilo (QSS) de la pantalla del doctor.

Estetica clinica: fondo claro y sereno, primario teal (salud/terapia), zona de
juego oscura para resaltar los LEDs blancos del tapete, y color con SIGNIFICADO
(verde=acierto/subir, ambar=bajar, rojo=error, gris=mantener). Tipografia con
jerarquia: cifras grandes, rotulos pequenos. Qt QSS no soporta sombras ni
text-transform; el relieve se logra con superficie blanca + borde sobre el fondo.

La paleta vive una sola vez aqui (constantes de abajo) y la consumen tanto el QSS
como las graficas matplotlib del "Historico" (via GRAFICO), para que ambas
pestanas lean como un solo producto y no como dos aplicaciones distintas.
"""

FUENTE = '"Noto Sans", "DejaVu Sans", sans-serif'

# --- Paleta clinica (fuente unica de color) ---
TEAL = "#0F766E"       # primario (salud/terapia)
TEAL_OSC = "#0B5A54"
VERDE = "#15803D"      # acierto / subir nivel
ROJO = "#DC2626"       # error
ROJO_OSC = "#B42318"
AMBAR = "#B45309"      # bajar nivel
AZUL_PIZ = "#475569"   # dato neutro (tiempo de reaccion)
TINTA = "#1F2933"
GRIS = "#8A94A6"
FONDO = "#F4F6F9"

# Colores para las series de matplotlib del historico (mismos que el QSS).
GRAFICO = {
    "aciertos": VERDE,
    "errores": ROJO,
    "rt": AZUL_PIZ,
    "tasa": TEAL,
    "nivel": AMBAR,
    "grid": "#CBD5E1",
    "tinta": "#384250",
    "fondo": FONDO,
}

QSS = f"""
* {{
    font-family: {FUENTE};
    color: {TINTA};
}}
QMainWindow, QTabWidget::pane, QWidget {{
    background: {FONDO};
}}
QTabWidget::pane {{ border: none; }}
/* Los QLabel no pintan fondo (heredarian el gris del selector universal). */
QLabel {{ background: transparent; }}
/* Separadores arrastrables pero discretos (sin los puntos por defecto). */
QSplitter::handle {{ background: transparent; }}
QSplitter::handle:horizontal {{ width: 12px; }}
QSplitter::handle:vertical {{ height: 12px; }}
QTabBar::tab {{
    background: transparent;
    color: #6B7280;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {TEAL};
    border-bottom: 2px solid {TEAL};
}}
QTabBar::tab:hover:!selected {{ color: #384250; }}

/* --- Barra de controles --- */
QLabel {{ font-size: 13px; color: #384250; }}
QLineEdit, QComboBox, QSpinBox {{
    background: #FFFFFF;
    border: 1px solid #D5DCE5;
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 13px;
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {TEAL}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}

/* SpinBox de nivel: botones +/- con fondo sutil pegados al campo; la flecha la
   pinta Qt (nativa) -- los triangulos QSS por 'border' no cuajan fiables entre
   estilos y se veian como rectangulos. Tratamiento minimo y limpio. */
QSpinBox {{ padding-right: 22px; }}
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: padding;
    width: 18px; background: #EDF1F5; border-left: 1px solid #D5DCE5;
}}
QSpinBox::up-button {{ subcontrol-position: top right; border-bottom: 1px solid #D5DCE5; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #DDE4EC; }}

QPushButton {{
    background: #FFFFFF;
    border: 1px solid #D5DCE5;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
    color: {TINTA};
}}
QPushButton:hover {{ background: #EDF1F5; }}
/* Foco de teclado visible (accesibilidad): anillo teal sin mover el layout. */
QPushButton:focus {{ border: 1px solid {TEAL}; }}
QPushButton#start {{ background: {TEAL}; color: #FFFFFF; border: 1px solid {TEAL}; }}
QPushButton#start:hover {{ background: {TEAL_OSC}; border-color: {TEAL_OSC}; }}
QPushButton#start:focus {{ border: 1px solid {TEAL_OSC}; }}
QPushButton#stop {{ color: {ROJO_OSC}; border: 1px solid #EFC7C2; }}
QPushButton#stop:hover {{ background: #FDF1EF; }}
QPushButton#stop:focus {{ border: 1px solid {ROJO_OSC}; }}

/* --- Panel de juego: fondo oscuro, los LEDs blancos resaltan --- */
QWidget#panelJuego {{ background: #1B2430; border-radius: 16px; }}
QLabel#rondaJuego {{
    color: #C7D0DB; font-size: 14px; font-weight: 600; padding: 2px 6px;
}}
/* Estado del juego como chip con color semantico (idle/running/paused/finished).
   El texto conserva la palabra de estado en minuscula (lo usan los tests). */
QLabel#estadoJuego {{
    font-size: 13px; font-weight: 700; color: #AEB8C6;
    padding: 3px 12px; border-radius: 11px;
    background: rgba(255, 255, 255, 0.06);
}}
QLabel#estadoJuego[estado="running"]  {{ color: #86EFAC; background: rgba(21, 128, 61, 0.22); }}
QLabel#estadoJuego[estado="paused"]   {{ color: #FBBF77; background: rgba(180, 83, 9, 0.26); }}
QLabel#estadoJuego[estado="finished"] {{ color: #7FE3D8; background: rgba(15, 118, 110, 0.30); }}

/* --- Tarjetas de metricas --- */
QWidget#panelMetricas {{ background: transparent; }}
QFrame#tarjeta {{
    background: #FFFFFF;
    border: 1px solid #E3E8EF;
    border-radius: 14px;
    padding: 8px;
    min-height: 74px;
}}
QLabel#valor {{ font-size: 34px; font-weight: 800; color: {TINTA}; }}
QLabel#rotulo {{ font-size: 11px; font-weight: 700; color: #6B7280; }}
QFrame#tarjeta[clase="aciertos"] QLabel#valor {{ color: {VERDE}; }}
QFrame#tarjeta[clase="errores"] QLabel#valor {{ color: {ROJO}; }}
QFrame#tarjeta[clase="tasa"] QLabel#valor {{ color: {TEAL}; }}
/* La tarjeta de ronda (ancha) es contexto, no una metrica de desempeno: mas sobria. */
QFrame#tarjeta[clase="ronda"] {{ min-height: 58px; background: #FBFCFD; }}
QFrame#tarjeta[clase="ronda"] QLabel#valor {{ font-size: 26px; color: #384250; }}

/* --- Panel de analisis / recomendacion --- */
QWidget#panelAnalisis {{ background: transparent; }}
QLabel#tendencia {{ font-size: 15px; color: #384250; padding: 4px 2px; }}
QLabel#recomendacion {{
    font-size: 15px; font-weight: 600;
    border-radius: 12px; padding: 12px 14px;
    background: #EEF2F6; color: #384250;
}}
QLabel#recomendacion[dir="up"] {{ background: #E6F4EA; color: #14683B; }}
QLabel#recomendacion[dir="down"] {{ background: #FBEFE0; color: #8A4B0A; }}
QPushButton#aplicar {{
    font-size: 14px; font-weight: 700; padding: 11px;
    border: none; border-radius: 10px;
    background: #D2DAE3; color: #6B7280;
}}
/* El boton sigue la direccion: verde subir, ambar bajar (coherente con la tarjeta). */
QPushButton#aplicar[dir="up"]:enabled {{ background: {VERDE}; color: #FFFFFF; }}
QPushButton#aplicar[dir="up"]:enabled:hover {{ background: #11692F; }}
QPushButton#aplicar[dir="down"]:enabled {{ background: {AMBAR}; color: #FFFFFF; }}
QPushButton#aplicar[dir="down"]:enabled:hover {{ background: #94430A; }}

/* --- Franja inferior --- */
QLabel#export {{ color: {GRIS}; font-size: 12px; }}
/* Indicador de conexion como chip (verde=conectado, rojo=degradado). La logica
   solo alterna la propiedad 'estado'; el color sale de aqui (antes iba inline). */
QLabel#estadoConexion {{
    font-size: 12px; font-weight: 700;
    padding: 3px 10px; border-radius: 10px;
}}
QLabel#estadoConexion[estado="ok"] {{ color: {VERDE}; background: #E6F4EA; }}
QLabel#estadoConexion[estado="degradado"] {{ color: {ROJO_OSC}; background: #FDECEA; }}
"""
