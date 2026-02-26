import subprocess
import pathlib
import pcbnew
import sys

def PCB_to_DSN(input_path, output_path):
    board = pcbnew.LoadBoard(input_path)

    if not (pcbnew.ExportSpecctraDSN(board, output_path)):
        raise AttributeError("Error returned from ExportSpecctraDSN(). Check your files.")
    
    return output_path
    
def SES_to_PCB(input_path, pcb, output_path):
    input_path = str(input_path)
    output_path = str(output_path)
    pcb = str(pcb)

    if not pathlib.Path(input_path).exists():
        raise FileNotFoundError(f"SES file not found: {input_path}")

    if not pathlib.Path(pcb).exists():
        raise FileNotFoundError(f"PCB file not found: {pcb}")

    board = pcbnew.LoadBoard(pcb)
    if board is None:
        raise RuntimeError(f"Failed to load PCB: {pcb}")

    if not pcbnew.ImportSpecctraSES(board, input_path):
        raise RuntimeError(f"Failed to import SES file: {input_path}")

    board.Save(output_path)
    return
