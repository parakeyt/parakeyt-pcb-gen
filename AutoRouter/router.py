import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from find_pcbnew import ensure_pcbnew
ensure_pcbnew()

import pcbnew
from pathlib import Path
import subprocess
from termcolor import colored
import os
from specctraHandler import SES_to_PCB

SCRIPT_DIR = Path(__file__).parent
router = SCRIPT_DIR / "freerouting-2.1.0.jar"
pcb1 = str(SCRIPT_DIR / "test.kicad_pcb")
ses1 = SCRIPT_DIR / "output.ses"

# Main PCB routing function
# pcb: path to kicad_pcb file to be routed, result is saved back to the same file
def routePCB(pcb: str, java):
    pcb = Path(pcb)
    ses = pcb.with_suffix(".ses")

    print("Converting PCB to DSN")
    x = pcb2dsn(pcb)

    if not x:
        print("PCB routing failed.")
        return -1

    dsn = pcb.with_suffix(".dsn")
    print("Routing PCB. This may take a while (up to 7 min), please be patient...")
    try:
        result = subprocess.run(
            [java, "-jar", str(router),
             "-de", str(dsn), "-do", str(ses)],
            check=True, timeout=420, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(colored(f"Autorouter failed with exit code {e.returncode}.", "red"))
        if e.stderr:
            print(e.stderr.decode())
        return -1
    except FileNotFoundError:
        print(colored("Java Runtime Environment not found. Please install the newest version of Java.", "red"))
        print(colored("If you still get this error, please set your JAVA_HOME environment variable.", "red"))
        return -1

    print("Autorouter Finished")

    SES_to_PCB(ses, pcb, pcb)
    print("Added traces to PCB.")
    add_ground_plane(pcb, pcb)
    add_ground_plane(pcb, pcb, layer=pcbnew.B_Cu)
    print("Added ground plane to PCB.")
    return 0

def pcb2dsn(pcb):
    pcb = Path(pcb)
    board = pcbnew.LoadBoard(str(pcb))
    if not board:
        print(colored("ERROR: Could not load board.", "red"))
        return
    result = pcbnew.ExportSpecctraDSN(board, str(pcb.with_suffix(".dsn")))
    if not result:
        print(colored("ERROR: PCB to DSN conversion failed. Please verify that the PCB is valid", 'red'))
    return result

def add_ground_plane(board_path, output_path, net_name="GND", layer=pcbnew.F_Cu):
    board_path = str(board_path)
    output_path = str(output_path)

    if not Path(board_path).exists():
        raise FileNotFoundError(f"PCB file not found: {board_path}")

    board = pcbnew.LoadBoard(board_path)
    if board is None:
        raise RuntimeError(f"Failed to load PCB: {board_path}")

    net = board.FindNet(net_name)
    if net is None:
        available = [n.GetNetname() for n in board.GetNets()]
        raise ValueError(f"Net '{net_name}' not found. Available nets: {available}")

    # Extract the board outline from Edge.Cuts
    outline = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(outline, False):
        raise RuntimeError("Failed to extract board outline. Ensure Edge.Cuts layer forms a closed shape.")

    # Build the zone matching the board outline
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)

    poly = outline.Outline(0)
    for i in range(poly.PointCount()):
        pt = poly.CPoint(i)
        zone.AppendCorner(pcbnew.VECTOR2I(pt.x, pt.y), -1)

    board.Add(zone)

    # Fill all zones — clearances from pads, traces, and footprints are handled automatically
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    board.Save(output_path)
    return output_path


def findJava():
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if candidate.exists():
            return str(candidate)
    return "java"


def main():
    java = findJava()
    routePCB(pcb1, java)

if __name__ == "__main__":
    main()