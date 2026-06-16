"""
ECG Biosensor PCB Auto-Finish Script
=====================================
Run this inside KiCad's Scripting Console:
  Tools → Scripting Console → paste or exec(open('ecg_pcb_autofinish.py').read())

Or from CLI (headless):
  python ecg_pcb_autofinish.py

Steps performed:
  1. Move decoupling caps (C1, C2, C3) closer to U1 (AD8232)
  2. Add a 3-pin output header (ECG_OUT, SDN, GND)
  3. Autoroute all remaining ratsnest connections
  4. Add GND copper fill zone on both F.Cu and B.Cu
  5. Run DRC and report violations
"""

import pcbnew
import os
import sys

# ── helpers ────────────────────────────────────────────────────────────────────

def mm(val):
    """Convert mm to KiCad internal units (nm in KiCad 7+)."""
    return pcbnew.FromMM(val)

def get_fp(board, ref):
    """Return footprint by reference designator, or None."""
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    return None

def fp_pos(fp):
    """Return footprint position as (x_mm, y_mm)."""
    pos = fp.GetPosition()
    return (pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y))

def set_pos(fp, x_mm, y_mm):
    """Set footprint position in mm."""
    fp.SetPosition(pcbnew.VECTOR2I(mm(x_mm), mm(y_mm)))

# ── 1. Load board ──────────────────────────────────────────────────────────────

BOARD_PATH = r"C:\Users\sivak\OneDrive\Documents\ecg-biosensor\hardware\ecg_biosensor.kicad_pcb"

if not os.path.exists(BOARD_PATH):
    # Try to get the already-open board from KiCad GUI
    try:
        board = pcbnew.GetBoard()
        BOARD_PATH = board.GetFileName()
        print(f"[INFO] Using open board: {BOARD_PATH}")
    except Exception:
        print("[ERROR] Board file not found and no board open in KiCad.")
        print(f"        Expected: {BOARD_PATH}")
        print("        Update BOARD_PATH at the top of this script.")
        sys.exit(1)
else:
    board = pcbnew.LoadBoard(BOARD_PATH)
    print(f"[INFO] Loaded board: {BOARD_PATH}")

# ── 2. Move decoupling caps close to U1 ───────────────────────────────────────

print("\n[STEP 1] Repositioning decoupling capacitors near U1...")

u1 = get_fp(board, "U1")
if u1 is None:
    print("[WARN] U1 not found — skipping cap repositioning.")
else:
    ux, uy = fp_pos(u1)
    print(f"        U1 centre: ({ux:.2f}, {uy:.2f}) mm")

    # Place caps in a tight row 3 mm above U1, spaced 3 mm apart
    cap_refs   = ["C1", "C2", "C3"]
    cap_offset_x = [-3.0, 0.0, 3.0]   # relative to U1 centre
    cap_offset_y = -6.0                 # above U1

    for ref, dx in zip(cap_refs, cap_offset_x):
        cap = get_fp(board, ref)
        if cap:
            set_pos(cap, ux + dx, uy + cap_offset_y)
            print(f"        {ref} → ({ux+dx:.2f}, {uy+cap_offset_y:.2f}) mm")
        else:
            print(f"[WARN]  {ref} not found.")

# ── 3. Add output header J2 (ECG_OUT, SDN#, GND) ─────────────────────────────

print("\n[STEP 2] Adding output header J2...")

existing_j2 = get_fp(board, "J2")
if existing_j2:
    print("        J2 already exists — skipping.")
else:
    # Try standard KiCad connector library
    lib_id = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    try:
        fp_j2 = pcbnew.FootprintLoad(
            pcbnew.FOOTPRINT_LIBRARY_TABLE().FindRow("Connector_PinHeader_2.54mm").GetFullURI(True),
            "PinHeader_1x03_P2.54mm_Vertical"
        )
    except Exception:
        # Fallback: use pcbnew plugin loader
        try:
            fp_j2 = board.GetDesignSettings()  # placeholder; real load below
            fp_j2 = pcbnew.FootprintLoad(
                pcbnew.SETTINGS_MANAGER().GetUserSettingsPath(),
                lib_id
            )
        except Exception:
            fp_j2 = None

    if fp_j2 is None:
        # Build a minimal 3-pin header manually if library load fails
        print("        [WARN] Could not load footprint from library.")
        print("               Creating bare-pad 3-pin header instead.")
        fp_j2 = pcbnew.FOOTPRINT(board)
        fp_j2.SetFPID(pcbnew.LIB_ID("", "PinHeader_1x03"))
        for i in range(3):
            pad = pcbnew.PAD(fp_j2)
            pad.SetNumber(str(i + 1))
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetSize(pcbnew.VECTOR2I(mm(1.6), mm(1.6)))
            pad.SetDrillSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
            pad.SetPosition(pcbnew.VECTOR2I(mm(0), mm(i * 2.54)))
            fp_j2.Add(pad)

    fp_j2.SetReference("J2")
    fp_j2.SetValue("OUTPUT_HDR")

    # Place J2 to the right of U1 with some clearance
    if u1:
        ux, uy = fp_pos(u1)
        set_pos(fp_j2, ux + 15.0, uy)
    else:
        set_pos(fp_j2, 60.0, 40.0)

    board.Add(fp_j2)
    j2x, j2y = fp_pos(fp_j2)
    print(f"        J2 placed at ({j2x:.2f}, {j2y:.2f}) mm")
    print("        Pin 1 = ECG_OUT  |  Pin 2 = SDN#  |  Pin 3 = GND")
    print("        NOTE: Connect nets manually in KiCad schematic, then")
    print("              re-import netlist to wire J2 pads to ECG_OUT/SDN#/GND.")

# ── 4. Autoroute remaining ratsnest ───────────────────────────────────────────

print("\n[STEP 3] Autorouting unconnected nets...")

# KiCad 7/8 exposes a basic router; for full autorouting use FreeRouting via DSN export.
# We use the built-in interactive router in batch mode where possible.

router_settings = board.GetDesignSettings()

# Set sensible trace widths for ECG analog signals
DEFAULT_TRACE_WIDTH = mm(0.25)   # 0.25 mm — adequate for low-current analog
POWER_TRACE_WIDTH   = mm(0.5)    # 0.5 mm for VCC / GND

try:
    # Attempt to use pcbnew's built-in auto-connectivity repair
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    unconnected = connectivity.GetUnconnectedCount()
    print(f"        Unconnected nets before routing: {unconnected}")

    if unconnected == 0:
        print("        Board is already fully connected — nothing to route.")
    else:
        print("        pcbnew scripting API does not expose a full autorouter.")
        print("        Exporting board as Specctra DSN for FreeRouting...")

        dsn_path = BOARD_PATH.replace(".kicad_pcb", "_autoroute.dsn")
        ses_path = BOARD_PATH.replace(".kicad_pcb", "_autoroute.ses")

        exporter = pcbnew.SPECCTRA_DB()
        exporter.ExportPCB(board, dsn_path)
        print(f"        DSN exported → {dsn_path}")
        print()
        print("  ┌─────────────────────────────────────────────────────────────┐")
        print("  │  MANUAL STEP: Run FreeRouting on the exported DSN           │")
        print("  │                                                             │")
        print("  │  Option A – FreeRouting GUI:                                │")
        print("  │    java -jar FreeRouting.jar                                │")
        print("  │    File → Open → select _autoroute.dsn                     │")
        print("  │    Autorouter → Start                                       │")
        print("  │    File → Export Specctra Session → save as _autoroute.ses  │")
        print("  │                                                             │")
        print("  │  Option B – FreeRouting headless:                           │")
        print("  │    java -jar FreeRouting.jar -de _autoroute.dsn \\           │")
        print("  │         -dr _autoroute.ses                                  │")
        print("  └─────────────────────────────────────────────────────────────┘")
        print()
        print("        After FreeRouting, import .ses back:")
        print("          File → Import → Specctra Session in KiCad")
        print("        OR run the import section of this script (see below).")

        # ── SES import (run after FreeRouting produces the .ses file) ──
        if os.path.exists(ses_path):
            print(f"\n        Detected existing SES: {ses_path}")
            print("        Importing routed session into board...")
            importer = pcbnew.SPECCTRA_DB()
            importer.ImportPCB(board, ses_path)
            board.BuildConnectivity()
            remaining = board.GetConnectivity().GetUnconnectedCount()
            print(f"        Unconnected after import: {remaining}")

except AttributeError as e:
    print(f"        [WARN] pcbnew API limitation: {e}")
    print("        Export DSN manually: File → Export → Specctra DSN")

# ── 5. Add GND copper fill zone ───────────────────────────────────────────────

print("\n[STEP 4] Adding GND copper fill zone...")

def add_gnd_zone(board, layer, net_name="GND"):
    """Add a filled copper zone covering the board outline on the given layer."""
    # Get board bounding box
    bbox = board.GetBoardEdgesBoundingBox()
    margin = mm(1.0)   # 1 mm inset from board edge

    # Find GND net
    netinfo = board.FindNet(net_name)
    if netinfo is None:
        print(f"        [WARN] Net '{net_name}' not found. "
              "Make sure netlist is imported before running this script.")
        return None

    zone = pcbnew.ZONE(board)
    zone.SetLayer(board.GetLayerID(layer))
    zone.SetNet(netinfo)
    zone.SetMinThickness(mm(0.25))
    zone.SetThermalReliefGap(mm(0.5))
    zone.SetThermalReliefSpokeWidth(mm(0.5))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)

    # Build outline from board bbox with inset
    outline = zone.Outline()
    outline.NewOutline()
    outline.Append(bbox.GetLeft()  + margin, bbox.GetTop()    + margin)
    outline.Append(bbox.GetRight() - margin, bbox.GetTop()    + margin)
    outline.Append(bbox.GetRight() - margin, bbox.GetBottom() - margin)
    outline.Append(bbox.GetLeft()  + margin, bbox.GetBottom() - margin)

    board.Add(zone)
    print(f"        GND zone added on {layer}")
    return zone

# Add GND fill on front and back copper layers
gnd_f = add_gnd_zone(board, "F.Cu")
gnd_b = add_gnd_zone(board, "B.Cu")

# Fill all zones
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
print("        Zones filled.")

# ── 6. DRC ────────────────────────────────────────────────────────────────────

print("\n[STEP 5] Running DRC...")

try:
    drc = pcbnew.DRC_ENGINE()
    drc.InitEngine(board)
    drc.RunTests()
    markers = board.GetDRCMarkers() if hasattr(board, "GetDRCMarkers") else []

    # Collect DRC results via markers on the board
    drc_items = list(board.Markers())
    errors   = [m for m in drc_items if m.GetSeverity() == pcbnew.SEVERITY_ERROR]
    warnings = [m for m in drc_items if m.GetSeverity() == pcbnew.SEVERITY_WARNING]

    print(f"        DRC complete — {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors:
        print("\n  ── DRC ERRORS ──────────────────────────────────────────────────")
        for i, m in enumerate(errors[:20], 1):   # cap output at 20
            desc = m.GetItemDescription(pcbnew.UNITS_PROVIDER(
                pcbnew.GetUserUnits(), pcbnew.EDA_DATA_TYPE_DISTANCE))
            print(f"  [{i:02d}] {desc}")
        if len(errors) > 20:
            print(f"  ... and {len(errors)-20} more. Open KiCad DRC dialog for full list.")

    if warnings:
        print("\n  ── DRC WARNINGS ────────────────────────────────────────────────")
        for m in warnings[:10]:
            desc = m.GetItemDescription(pcbnew.UNITS_PROVIDER(
                pcbnew.GetUserUnits(), pcbnew.EDA_DATA_TYPE_DISTANCE))
            print(f"  [W] {desc}")

    if not errors and not warnings:
        print("        ✓ Board passes DRC with no errors or warnings.")

except Exception as e:
    print(f"        [WARN] DRC engine error: {e}")
    print("        Run DRC manually: Inspect → Design Rules Checker in KiCad GUI.")

# ── 7. Save board ─────────────────────────────────────────────────────────────

out_path = BOARD_PATH.replace(".kicad_pcb", "_autofinish.kicad_pcb")
board.Save(out_path)
print(f"\n[DONE] Board saved → {out_path}")
print()
print("Next steps:")
print("  1. Open the saved board in KiCad and verify component positions visually.")
print("  2. If unconnected nets remain, run FreeRouting on the exported DSN")
print("     and import the .ses session file back into KiCad.")
print("  3. Wire J2 pads to ECG_OUT / SDN# / GND nets in the schematic,")
print("     update PCB from schematic, then re-run this script.")
print("  4. Re-run DRC in the KiCad GUI (Inspect → Design Rules Checker)")
print("     and resolve any remaining clearance or unconnected errors.")
print("  5. Generate Gerbers: File → Fabrication Outputs → Gerbers for JLCPCB.")
