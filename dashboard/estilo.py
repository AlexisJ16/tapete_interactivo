"""Hoja de estilo (QSS) de la pantalla del doctor.

Estetica clinica: fondo claro y sereno, primario teal (salud/terapia), zona de
juego oscura para resaltar los LEDs blancos del tapete, y color con SIGNIFICADO
(verde=acierto/subir, ambar=bajar, rojo=error, gris=mantener). Tipografia con
jerarquia: cifras grandes, rotulos pequenos. Qt QSS no soporta sombras ni
text-transform; el relieve se logra con superficie blanca + borde sobre el fondo.
"""

FUENTE = '"Noto Sans", "DejaVu Sans", sans-serif'

QSS = f"""
* {{
    font-family: {FUENTE};
    color: #1F2933;
}}
QMainWindow, QTabWidget::pane, QWidget {{
    background: #F4F6F9;
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
    color: #0F766E;
    border-bottom: 2px solid #0F766E;
}}

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
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid #0F766E; }}
QComboBox::drop-down {{ border: none; width: 20px; }}

QPushButton {{
    background: #FFFFFF;
    border: 1px solid #D5DCE5;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #1F2933;
}}
QPushButton:hover {{ background: #EDF1F5; }}
QPushButton#start {{ background: #0F766E; color: #FFFFFF; border: none; }}
QPushButton#start:hover {{ background: #0B5A54; }}
QPushButton#stop {{ color: #B42318; border: 1px solid #EFC7C2; }}
QPushButton#stop:hover {{ background: #FDF1EF; }}

/* --- Panel de juego: fondo oscuro, los LEDs blancos resaltan --- */
QWidget#panelJuego {{ background: #1B2430; border-radius: 16px; }}
QLabel#estadoJuego, QLabel#rondaJuego {{
    color: #C7D0DB; font-size: 14px; font-weight: 600; padding: 2px 6px;
}}

/* --- Tarjetas de metricas --- */
QWidget#panelMetricas {{ background: transparent; }}
QFrame#tarjeta {{
    background: #FFFFFF;
    border: 1px solid #E3E8EF;
    border-radius: 14px;
    padding: 8px;
}}
QLabel#valor {{ font-size: 34px; font-weight: 800; color: #1F2933; }}
QLabel#rotulo {{ font-size: 11px; font-weight: 700; color: #8A94A6; }}
QFrame#tarjeta[clase="aciertos"] QLabel#valor {{ color: #15803D; }}
QFrame#tarjeta[clase="errores"] QLabel#valor {{ color: #DC2626; }}
QFrame#tarjeta[clase="tasa"] QLabel#valor {{ color: #0F766E; }}

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
    background: #D2DAE3; color: #8A94A6;
}}
/* El boton sigue la direccion: verde subir, ambar bajar (coherente con la tarjeta). */
QPushButton#aplicar[dir="up"]:enabled {{ background: #15803D; color: #FFFFFF; }}
QPushButton#aplicar[dir="up"]:enabled:hover {{ background: #11692F; }}
QPushButton#aplicar[dir="down"]:enabled {{ background: #B45309; color: #FFFFFF; }}
QPushButton#aplicar[dir="down"]:enabled:hover {{ background: #94430A; }}

/* --- Franja inferior --- */
QLabel#export {{ color: #8A94A6; font-size: 12px; }}
"""
