import pcbnew
from pathlib import Path
import subprocess
from termcolor import colored
import os
from specctraHandler import SES_to_PCB

SCRIPT_DIR = Path(__file__).parent
router = SCRIPT_DIR / "freerouting-2.1.0.jar"
pcb1 = str(SCRIPT_DIR / "routerTest.kicad_pcb")
ses1 = SCRIPT_DIR / "output.ses"

# Main PCB routing function
# pcb: path to kicad_pcb file to be routed
# ses: file path for output session file
def routePCB(pcb=pcb1, ses=ses1):

    print("Converting PCB to DSN")
    x = pcb2dsn(pcb)

    if not x:
        print("PCB routing failed.")
        return -1
    
    dsn = SCRIPT_DIR / 'input.dsn'
    print("Routing PCB...")
    try:
        result = subprocess.run(
        [java, "-Djava.awt.headless=true", "-jar", str(router),
        "-de", str(dsn), "-do", str(ses)],
        check=True, timeout=40, stderr=subprocess.PIPE
    )
    except subprocess.TimeoutExpired as e:
        print(colored("Autorouter timed out. Adjust PCB or finish routing manually.", 'yellow'))
        return 1
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

    SES_to_PCB(ses1, pcb1, SCRIPT_DIR / "output.kicad_pcb")
    print("Added traces to PCB.")
    add_ground_plane(SCRIPT_DIR / "output.kicad_pcb", SCRIPT_DIR / "output.kicad_pcb")
    print("Added ground plane to PCB.")
    return 0

def pcb2dsn(pcb):
    board = pcbnew.LoadBoard(pcb)
    if not board:
        print(colored("ERROR: Could not load board.", "red"))
        return
    result = pcbnew.ExportSpecctraDSN(board, str(SCRIPT_DIR / 'input.dsn'))
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
    if not board.GetBoardPolygonOutlines(outline):
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
    global java
    java = findJava()
    routePCB()

if __name__ == "__main__":
    main()