import pcbnew
from pathlib import Path
import subprocess
from termcolor import colored
import os

router = Path("freerouting-2.1.0.jar")
pcb1 = Path("routerTest.kicad_pcb")
ses1 = Path("output.ses")

# Main PCB routing function
# pcb: path to kicad_pcb file to be routed
# ses: file path for output session file
def routePCB(pcb=pcb1, ses=ses1):

    print("Converting PCB to DSN")
    x = pcb2dsn(pcb)

    if not x:
        print("PCB routing failed.")
        return -1
    
    dsn = Path('input.dsn')
    print("Routing PCB...")
    try:
        result = subprocess.run(
        [java, "-Djava.awt.headless=true", "-jar", str(router), 
        "-de", str(dsn), "-do", str(ses)],
        check=True, timeout=40
    )
    except subprocess.TimeoutExpired as e:
        print(colored("Autorouter timed out. Adjust PCB or finish routing manually."), 'yellow')
        return 1
    except FileNotFoundError:
        print(colored("Java Runtime Environment not found. Please install the newest version of Java.", "red"))
        print(colored("If you still get this error, please set your JAVA_HOME environment variable.", "red"))
        return -1

    print("Autorouter Finished")
    return 0

def pcb2dsn(pcb):
    board = pcbnew.LoadBoard(pcb)
    result = pcbnew.ExportSpecctraDSN(board, 'input.dsn')
    if not result:
        print(colored("ERROR: PCB to DSN conversion failed. Please verify that the PCB is valid", 'red'))
    return result

def findJava():
    java_home = os.environ.get("JAVA_HOME")
    print(java_home)
    if java_home:
        candidate = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if candidate.exists():
            return str(candidate)
    return "NULL"


def main():
    global java
    java = findJava()
    routePCB()

if __name__ == "__main__":
    main()