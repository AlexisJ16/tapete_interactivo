"""Motor de autoría de esquemáticos KiCad 10 (.kicad_sch) para el Tapete.

Autoría programática desde un modelo declarativo (componentes + nets). Emite un
.kicad_sch valido para kicad-cli 10.0.4 (erc/export). No hay API oficial de Python
para esquematicos, asi que se emite el S-expression directamente, tomando el formato
de los templates reales del sistema (v20250114, gen 9.0; kicad-cli 10 lo migra).

Principios de diseno:
- Todos los simbolos se colocan a rotacion 0, sin espejo. El punto de conexion
  absoluto de un pin es (Sx + px, Sy + py) donde (px,py) es el `at` local del pin.
  Esto elimina la matematica de rotacion/espejo (el usuario reordena en la GUI).
- Conectividad por `label` local en el punto de conexion de cada pin (mismo nombre
  = mismo net en la hoja). No se dibujan wires (patron del template Arduino_Pro_Mini).
- UUIDs DETERMINISTAS (uuid5) para que la salida sea reproducible byte a byte
  (diffs de git limpios), en linea con la filosofia de golden vectors del proyecto.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

# Namespace fijo del proyecto -> uuids reproducibles.
_NS = uuid.UUID("7a9e1b2c-0000-4000-8000-746170657465")  # "...tapete"
# uuid raiz de la hoja (usado en los bloques (instances (path "/<root>"))).
ROOT_UUID = str(uuid.uuid5(_NS, "root-sheet"))

SYMDIR = "/usr/share/kicad/symbols"
GRID = 1.27  # rejilla de conexion de KiCad (50 mil)


def uid(key: str) -> str:
    return str(uuid.uuid5(_NS, key))


def _snap(v: float) -> float:
    """Ajusta a la rejilla de 1.27 mm (evita warnings endpoint_off_grid)."""
    return round(round(v / GRID) * GRID, 4)


def _fmt(v: float) -> str:
    """Coordenada limpia (sin ruido de float ni .0 sobrante)."""
    return f"{round(v, 4):.4f}".rstrip("0").rstrip(".") or "0"


# --- Extraccion de simbolos stock -------------------------------------------

def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _extract_block(text: str, start: int) -> str:
    """Devuelve el S-expression balanceado que empieza en el '(' de la pos start."""
    depth = 0
    i = start
    in_str = False
    while i < len(text):
        c = text[i]
        if c == '"' and text[i - 1] != "\\":
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    raise ValueError("parentesis sin cerrar")


def extract_symbol(lib: str, name: str) -> str:
    """Bloque `(symbol "name" ...)` de <lib>.kicad_sym, con el nombre externo
    reescrito a "lib:name" (formato de lib_symbols embebido)."""
    text = _read(f"{SYMDIR}/{lib}.kicad_sym")
    m = re.search(r'\(symbol\s+"' + re.escape(name) + r'"', text)
    if not m:
        raise ValueError(f"simbolo {lib}:{name} no encontrado")
    block = _extract_block(text, m.start())
    # Reescribe SOLO el nombre externo (primera ocurrencia). Los sub-simbolos
    # (name_0_1 / name_1_1) se dejan intactos.
    return block.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)


_PIN_RE = re.compile(
    r'\(pin\s+\S+\s+\S+\s*\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)'
    r'.*?\(number\s+"([^"]+)"',
    re.DOTALL,
)


def pins_of(symbol_block: str) -> dict[str, tuple[float, float]]:
    """number -> (x, y) local del punto de conexion, para todos los pines."""
    out: dict[str, tuple[float, float]] = {}
    for mx, my, _rot, num in _PIN_RE.findall(symbol_block):
        out[num] = (float(mx), float(my))
    return out


# --- Modelo declarativo ------------------------------------------------------

@dataclass
class Comp:
    ref: str
    lib: str          # p.ej. "Device", "power", "tapete"
    name: str         # p.ej. "R", "+5V", "ESP32-DevKit-30"
    value: str
    x: float
    y: float
    footprint: str = ""
    # override de def de simbolo (para simbolos custom que no vienen de SYMDIR)
    custom_def: str | None = None

    @property
    def lib_id(self) -> str:
        return f"{self.lib}:{self.name}"


@dataclass
class Design:
    project: str = "tapete"
    paper: str = "A3"
    comps: list[Comp] = field(default_factory=list)
    # net -> lista de (ref, pin_number)
    nets: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    # defs de simbolos custom: lib_id -> bloque S-expr (ya con nombre "lib:name")
    custom_defs: dict[str, str] = field(default_factory=dict)
    # textos libres: (x, y, texto)
    notes: list[tuple[float, float, str]] = field(default_factory=list)
    # pines marcados no_connect: (ref, pin_number)
    nc: list[tuple[str, str]] = field(default_factory=list)

    def add(self, c: Comp) -> Comp:
        self.comps.append(c)
        return c

    def connect(self, net: str, *endpoints: tuple[str, str]) -> None:
        self.nets.setdefault(net, []).extend(endpoints)

    def no_connect(self, ref: str, *pins: str) -> None:
        self.nc.extend((ref, p) for p in pins)


# --- Emision de S-expression -------------------------------------------------

def _prop(name: str, val: str, x: float, y: float, hide: bool = False) -> str:
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (
        f'\t\t(property "{name}" "{val}"\n'
        f"\t\t\t(at {_fmt(x)} {_fmt(y)} 0){h}\n"
        f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n"
        f"\t\t)\n"
    )


def _emit_symbol(c: Comp, symdef: str) -> str:
    ps = pins_of(symdef)
    pins_txt = "".join(
        f'\t\t(pin "{n}"\n\t\t\t(uuid "{uid(c.ref + ":pin:" + n)}")\n\t\t)\n'
        for n in ps
    )
    is_power = c.lib == "power"
    ref_prop = _prop("Reference", c.ref, c.x + 2.54, c.y - 1.27, hide=is_power)
    val_prop = _prop("Value", c.value, c.x + 2.54, c.y + 1.27)
    fp_prop = _prop("Footprint", c.footprint, c.x, c.y, hide=True)
    return (
        f"\t(symbol\n"
        f'\t\t(lib_id "{c.lib_id}")\n'
        f"\t\t(at {_fmt(c.x)} {_fmt(c.y)} 0)\n"
        f"\t\t(unit 1)\n"
        f"\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n"
        f'\t\t(uuid "{uid(c.ref)}")\n'
        f"{ref_prop}{val_prop}{fp_prop}{pins_txt}"
        f"\t\t(instances\n"
        f'\t\t\t(project "{{proj}}"\n'
        f'\t\t\t\t(path "/{ROOT_UUID}"\n'
        f'\t\t\t\t\t(reference "{c.ref}")\n\t\t\t\t\t(unit 1)\n'
        f"\t\t\t\t)\n\t\t\t)\n\t\t)\n"
        f"\t)\n"
    )


def _emit_label(net: str, x: float, y: float, key: str) -> str:
    return (
        f'\t(label "{net}"\n'
        f"\t\t(at {_fmt(x)} {_fmt(y)} 0)\n"
        f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n"
        f'\t\t(uuid "{uid("label:" + key)}")\n'
        f"\t)\n"
    )


def _emit_text(x: float, y: float, txt: str, key: str) -> str:
    esc = txt.replace('"', '\\"')
    return (
        f'\t(text "{esc}"\n'
        f"\t\t(at {_fmt(x)} {_fmt(y)} 0)\n"
        f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n"
        f'\t\t(uuid "{uid("text:" + key)}")\n'
        f"\t)\n"
    )


def render(d: Design) -> str:
    # 0) Ajustar todos los origenes a la rejilla de 1.27 (pines -> on-grid).
    for c in d.comps:
        c.x, c.y = _snap(c.x), _snap(c.y)

    # 1) Reunir defs de simbolos usados (stock -> extraidas; custom -> del design).
    used: dict[str, str] = {}
    pin_cache: dict[str, dict[str, tuple[float, float]]] = {}
    for c in d.comps:
        if c.lib_id in used:
            continue
        if c.custom_def is not None:
            block = c.custom_def
        elif c.lib_id in d.custom_defs:
            block = d.custom_defs[c.lib_id]
        else:
            block = extract_symbol(c.lib, c.name)
        used[c.lib_id] = block
        pin_cache[c.lib_id] = pins_of(block)

    # 2) lib_symbols
    lib_syms = "".join(
        "\t\t" + block.replace("\n", "\n\t\t") + "\n" for block in used.values()
    )

    # 3) simbolos colocados
    body = "".join(_emit_symbol(c, used[c.lib_id]) for c in d.comps)

    # 4) labels por net (uno en el punto de conexion de cada pin del net)
    by_ref = {c.ref: c for c in d.comps}
    labels = ""
    for net, endpoints in d.nets.items():
        for ref, pin in endpoints:
            c = by_ref[ref]
            px, py = pin_cache[c.lib_id][pin]
            # Y-flip: el espacio del simbolo es Y-arriba; el esquematico Y-abajo.
            ax, ay = c.x + px, c.y - py
            labels += _emit_label(net, ax, ay, f"{net}:{ref}:{pin}")

    # 5) no_connect en el punto de conexion de cada pin marcado
    ncs = ""
    for ref, pin in d.nc:
        c = by_ref[ref]
        px, py = pin_cache[c.lib_id][pin]
        ax, ay = c.x + px, c.y - py
        ncs += (
            f"\t(no_connect\n\t\t(at {_fmt(ax)} {_fmt(ay)})\n"
            f'\t\t(uuid "{uid("nc:" + ref + ":" + pin)}")\n\t)\n'
        )

    # 6) notas de texto
    notes = "".join(_emit_text(x, y, t, f"{i}") for i, (x, y, t) in enumerate(d.notes))

    doc = (
        "(kicad_sch\n"
        "\t(version 20260306)\n"
        '\t(generator "eeschema")\n'
        '\t(generator_version "10.0")\n'
        f'\t(uuid "{ROOT_UUID}")\n'
        f'\t(paper "{d.paper}")\n'
        f"\t(lib_symbols\n{lib_syms}\t)\n"
        f"{body}{labels}{ncs}{notes}"
        '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n'
        "\t(embedded_fonts no)\n"
        ")\n"
    ).replace("{proj}", d.project)
    return doc


def write(d: Design, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(d))


# --- Constructor de simbolos custom (rectangulo con pines tipados) ----------

def _pin(num: str, name: str, etype: str, x: float, y: float, rot: int) -> str:
    return (
        f"\t\t(pin {etype} line\n"
        f"\t\t\t(at {_fmt(x)} {_fmt(y)} {rot})\n"
        f"\t\t\t(length 2.54)\n"
        f'\t\t\t(name "{name}"\n\t\t\t\t(effects\n\t\t\t\t\t(font\n\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n'
        f'\t\t\t(number "{num}"\n\t\t\t\t(effects\n\t\t\t\t\t(font\n\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n'
        f"\t\t)\n"
    )


def make_rect_symbol(name: str, left: list, right: list, body_w: float = 30.48,
                     ref: str = "U", bare: bool = True) -> str:
    """Simbolo rectangular con pines tipados. left/right = [(num, name, etype)].
    Pines a 2.54 mm; geometria on-grid. Devuelve el bloque (nombre bare por defecto).
    """
    n = max(len(left), len(right))
    top = round((n - 1) * 2.54 / 2, 4)          # y del primer pin (Y-arriba, simbolo)
    half = body_w / 2
    ext = half + 2.54                            # x del punto de conexion
    ry = top + 2.54                              # medio-alto del rectangulo

    pins = ""
    for i, (num, pname, et) in enumerate(left):
        pins += _pin(num, pname, et, -ext, top - i * 2.54, 0)
    for i, (num, pname, et) in enumerate(right):
        pins += _pin(num, pname, et, ext, top - i * 2.54, 180)

    return (
        f'(symbol "{name}"\n'
        f"\t(pin_names\n\t\t(offset 1.016)\n\t)\n"
        f"\t(exclude_from_sim no)\n\t(in_bom yes)\n\t(on_board yes)\n"
        f'\t(property "Reference" "{ref}"\n\t\t(at 0 {_fmt(ry + 2.54)} 0)\n'
        f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t)\n\t)\n"
        f'\t(property "Value" "{name}"\n\t\t(at 0 {_fmt(-ry - 2.54)} 0)\n'
        f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t)\n\t)\n"
        f'\t(property "Footprint" ""\n\t\t(at 0 0 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(hide yes)\n\t\t)\n\t)\n'
        f'\t(property "Datasheet" ""\n\t\t(at 0 0 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(hide yes)\n\t\t)\n\t)\n'
        f'\t(symbol "{name}_1_1"\n'
        f"\t\t(rectangle\n\t\t\t(start {_fmt(-half)} {_fmt(ry)})\n\t\t\t(end {_fmt(half)} {_fmt(-ry)})\n"
        f"\t\t\t(stroke\n\t\t\t\t(width 0.254)\n\t\t\t\t(type default)\n\t\t\t)\n\t\t\t(fill\n\t\t\t\t(type background)\n\t\t\t)\n\t\t)\n"
        f"{pins}"
        f"\t)\n"
        f")"
    )


def to_lib_id(bare_block: str, lib: str, name: str) -> str:
    """Reescribe el nombre externo bare -> 'lib:name' para embeber en lib_symbols."""
    return bare_block.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)


SYMLIB_HEADER = (
    "(kicad_symbol_lib\n\t(version 20251024)\n"
    '\t(generator "kicad_symbol_editor")\n\t(generator_version "10.0")\n'
)


def write_symlib(path: str, symbols: list[str]) -> None:
    """Escribe un .kicad_sym con simbolos bare-name."""
    body = "".join("\t" + s.replace("\n", "\n\t") + "\n" for s in symbols)
    with open(path, "w", encoding="utf-8") as f:
        f.write(SYMLIB_HEADER + body + ")\n")
