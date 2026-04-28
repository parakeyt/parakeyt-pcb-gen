import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from find_pcbnew import ensure_pcbnew
ensure_pcbnew()

import pcbnew

def label_switches(pcb_path: str):
    board = pcbnew.LoadBoard(pcb_path)
    counter = 1

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("REF"):
            fp.SetReference(f"SW{counter}")
            counter += 1

    board.Save(pcb_path)
    print(f"Done! {counter - 1} switches renamed.")
