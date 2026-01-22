import subprocess
import pathlib
import pcbnew
import sys

def PCB_to_DSN(input_path, output_path):
    board = pcbnew.LoadBoard(input_path)

    if not (pcbnew.ExportSpecctraDSN(board, output_path)):
        raise AttributeError("Error returned from ExportSpecctraDSN(). Check your files.")
    
    return output_path
    
def SES_to_PCB()