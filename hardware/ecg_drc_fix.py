"""
ECG Biosensor PCB — Targeted DRC Fix Script v2
Run from KiCad Scripting Console or Windows CMD.
"""
import re, uuid, shutil, os, sys

PCB_IN  = r"C:\Users\sivak\OneDrive\Documents\ecg-biosensor\hardware\ECG-Biosensor-AD8232.kicad_pcb"
PCB_OUT = r"C:\Users\sivak\OneDrive\Documents\ecg-biosensor\hardware\ECG-Biosensor-AD8232-fixed.kicad_pcb"

# Auto-detect if running locally
if not os.path.exists(PCB_IN):
    here = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
    alt  = os.path.join(here, "ECG-Biosensor-AD8232.kicad_pcb")
    if os.path.exists(alt):
        PCB_IN  = alt
        PCB_OUT = os.path.join(here, "ECG-Biosensor-AD8232-fixed.kicad_pcb")
    else:
        print(f"[ERROR] Board not found at:\n  {PCB_IN}\n  {alt}")
        sys.exit(1)

with open(PCB_IN, 'r', encoding='utf-8') as f:
    pcb = f.read()

shutil.copy(PCB_IN, PCB_IN + ".bak")
print(f"[INFO] Loaded {len(pcb)} chars. Backup created.")

def uid(): return str(uuid.uuid4())

# ── Helpers ───────────────────────────────────────────────────────────────────

def insert_before_closing(text, block):
    text = text.rstrip()
    assert text.endswith(')'), "PCB file doesn't end with ')'"
    return text[:-1].rstrip() + '\n' + block + '\n)'

def seg(x1, y1, x2, y2, w, layer, net):
    return (f'\t(segment (start {x1} {y1}) (end {x2} {y2})'
            f' (width {w}) (layer "{layer}") (net {net}) (uuid "{uid()}"))')

# ── A. Move caps close to U1 (direct string replace on (at x y)) ─────────────
# Component (at x y) lines — replace only the line that matches exactly,
# identified by surrounding context (footprint ref on next property line).
# Strategy: split into footprint blocks, edit each, rejoin.

def reposition_fps(text, moves):
    """moves = {ref: (new_x, new_y)}"""
    # Split on footprint start markers
    # Each block: everything from (footprint ... to the next top-level (footprint or end
    parts  = re.split(r'(?=\n\t\(footprint )', text)
    result = []
    for part in parts:
        ref_m = re.search(r'property "Reference" "([^"]+)"', part)
        if ref_m and ref_m.group(1) in moves:
            ref = ref_m.group(1)
            nx, ny = moves[ref]
            # Replace the (at X Y) or (at X Y angle) line
            part = re.sub(
                r'(\(at )([0-9.-]+) ([0-9.-]+)(\))',
                lambda m: f'{m.group(1)}{nx} {ny}{m.group(4)}',
                part, count=1
            )
            print(f"[FIX A] {ref} → ({nx}, {ny})")
        result.append(part)
    return ''.join(result)

pcb = reposition_fps(pcb, {"C1": (45, 38), "C2": (48, 38), "C3": (51, 38)})

# ── B. Add J2 footprint (9-pin 2.54mm header) at (75, 45) ────────────────────
J2_X, J2_Y = 75.0, 45.0
J2_NETS = {
    1: ("VCC",     1), 2: ("GND",     3), 3: ("ECG_OUT", 6),
    4: ("LO_PLUS", 9), 5: ("LO_MINUS",8), 6: ("VCC",     1),
    7: ("REFOUT", 10), 8: ("IAOUT",  11), 9: ("",        0),
}
pad_size, drill, pitch = 1.7, 1.0, 2.54

pads = []
for n in range(1, 10):
    py = (n - 1) * pitch
    net_name, net_code = J2_NETS[n]
    shape = "rect" if n == 1 else "circle"
    net_cl = f'(net {net_code} "{net_name}") ' if net_code > 0 else ""
    pads.append(
        f'\t\t(pad "{n}" thru_hole {shape} (at 0 {py:.4f})'
        f' (size {pad_size} {pad_size}) (drill {drill})'
        f' (layers "*.Cu" "*.Mask") {net_cl}(uuid "{uid()}"))'
    )

j2_fp = '\n'.join([
    f'\t(footprint "ecg_kicad:HDR-TH_9P-P2.54-V"',
    f'\t\t(layer "F.Cu") (uuid "{uid()}")',
    f'\t\t(at {J2_X} {J2_Y})',
    f'\t\t(property "Reference" "J2"',
    f'\t\t\t(at 0 -2 0) (layer "F.SilkS") (uuid "{uid()}")',
    f'\t\t\t(effects (font (size 1 1) (thickness 0.15))))',
    f'\t\t(property "Value" "OUTPUT_HDR"',
    f'\t\t\t(at 0 25 0) (layer "F.Fab") (uuid "{uid()}")',
    f'\t\t\t(effects (font (size 1 1) (thickness 0.15))))',
    f'\t\t(fp_line (start -1.77 -0.5) (end 1.77 -0.5)'
    f' (stroke (width 0.05) (type default)) (layer "F.CrtYd") (uuid "{uid()}"))',
    f'\t\t(fp_line (start 1.77 -0.5) (end 1.77 23.36)'
    f' (stroke (width 0.05) (type default)) (layer "F.CrtYd") (uuid "{uid()}"))',
    f'\t\t(fp_line (start 1.77 23.36) (end -1.77 23.36)'
    f' (stroke (width 0.05) (type default)) (layer "F.CrtYd") (uuid "{uid()}"))',
    f'\t\t(fp_line (start -1.77 23.36) (end -1.77 -0.5)'
    f' (stroke (width 0.05) (type default)) (layer "F.CrtYd") (uuid "{uid()}"))',
] + pads + ['\t)'])

pcb = insert_before_closing(pcb, j2_fp)
print(f"[FIX B] J2 added at ({J2_X}, {J2_Y}) with 9 pins and net assignments")

# ── C. Add missing traces (10 unconnected nets from DRC) ─────────────────────
W, WP = 0.25, 0.4
traces = [
    # VCC: U1.pad13 → C3.pad1
    seg(49.87, 40.0, 61.3, 40.0,  WP, "F.Cu", 1),
    # GND: U1.EP(pad21) → U1.pad14, then to C3.pad2
    seg(48.0,  40.0, 49.87, 39.5, WP, "F.Cu", 3),
    seg(62.7,  40.0, 62.7,  39.5, WP, "F.Cu", 3),
    seg(62.7,  39.5, 49.87, 39.5, WP, "F.Cu", 3),
    # RLD: bridge existing track stub to pad4
    seg(45.9589, 41.1711, 46.13, 40.5, W, "F.Cu", 4),
    # ECG_INP: J1.pad5 → U1.pad2
    seg(25.95, 42.7, 25.95, 39.5, W, "F.Cu", 5),
    seg(25.95, 39.5, 46.13, 39.5, W, "F.Cu", 5),
    # ECG_INN: J1.pad3 → U1.pad3
    seg(28.95, 42.7, 28.95, 40.0, W, "F.Cu", 7),
    seg(28.95, 40.0, 46.13, 40.0, W, "F.Cu", 7),
    # LO_PLUS: J2.pin4 (75, 45+3*2.54=52.62) → U1.pad12
    seg(75.0, 52.62, 75.0, 40.5,  W, "F.Cu", 9),
    seg(75.0, 40.5,  49.87, 40.5, W, "F.Cu", 9),
    # LO_MINUS: J2.pin5 (75, 45+4*2.54=55.16) → U1.pad11
    seg(75.0, 55.16, 75.0, 41.0,  W, "F.Cu", 8),
    seg(75.0, 41.0,  49.87, 41.0, W, "F.Cu", 8),
    # ECG_OUT: U1.pad10 (≈49.0, 47.0) → J2.pin3 (75, 45+2*2.54=50.08)
    seg(49.0, 47.0, 49.0, 50.08,  W, "F.Cu", 6),
    seg(49.0, 50.08, 75.0, 50.08, W, "F.Cu", 6),
]
pcb = insert_before_closing(pcb, '\n'.join(traces))
print(f"[FIX C] {len(traces)} traces added for 10 unconnected nets")

# ── D. Fix board outline (replace all Edge.Cuts, add closed rectangle) ────────
# Remove every gr_line that touches Edge.Cuts layer
def strip_edge_cuts(text):
    # Match multi-line gr_line blocks containing Edge.Cuts
    pattern = re.compile(
        r'\t\(gr_line\s*\(start[^)]+\)\s*\(end[^)]+\)\s*\(stroke[^}]+?\)\s*\(layer "Edge\.Cuts"\)[^)]*\)\s*\n',
        re.DOTALL
    )
    new, n = pattern.subn('', text)
    # Also try simpler single-line format
    pattern2 = re.compile(r'\t\(gr_line[^\n]+Edge\.Cuts[^\n]+\n')
    new, n2 = pattern2.subn('', new)
    print(f"[FIX D] Removed {n+n2} existing Edge.Cuts segments")
    return new

pcb = strip_edge_cuts(pcb)

outline = '\n'.join([
    f'\t(gr_line (start 20 13.5) (end 160 13.5)'
    f' (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid()}"))',
    f'\t(gr_line (start 160 13.5) (end 160 70)'
    f' (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid()}"))',
    f'\t(gr_line (start 160 70) (end 20 70)'
    f' (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid()}"))',
    f'\t(gr_line (start 20 70) (end 20 13.5)'
    f' (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid()}"))',
])
pcb = insert_before_closing(pcb, outline)
print("[FIX D] Closed board outline added: 140 × 56.5 mm")

# ── E. GND copper fill zones ──────────────────────────────────────────────────
def gnd_zone(layer):
    return (
        f'\t(zone (net 3) (net_name "GND") (layer "{layer}") (uuid "{uid()}")\n'
        f'\t\t(hatch edge 0.5)\n'
        f'\t\t(connect_pads (clearance 0.5))\n'
        f'\t\t(min_thickness 0.25)\n'
        f'\t\t(filled_areas_thickness no)\n'
        f'\t\t(fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))\n'
        f'\t\t(polygon (pts\n'
        f'\t\t\t(xy 21 14.5) (xy 159 14.5) (xy 159 69) (xy 21 69)\n'
        f'\t\t))\n'
        f'\t)'
    )
pcb = insert_before_closing(pcb, gnd_zone("F.Cu") + '\n' + gnd_zone("B.Cu"))
print("[FIX E] GND copper fill zones added (F.Cu + B.Cu)")

# ── Save ──────────────────────────────────────────────────────────────────────
with open(PCB_OUT, 'w', encoding='utf-8') as f:
    f.write(pcb)

print(f"\n{'='*60}")
print(f"[DONE] → {PCB_OUT}")
print(f"{'='*60}")
print("""
Next steps in KiCad:
  1. File → Open → ECG-Biosensor-AD8232-fixed.kicad_pcb
  2. Press B  (Fill All Zones — applies GND pour)
  3. Inspect → Design Rules Checker → Run DRC
  4. Reroute any traces flagged by DRC using Interactive Router
  5. File → Fabrication Outputs → Gerbers (JLCPCB profile)
""")
