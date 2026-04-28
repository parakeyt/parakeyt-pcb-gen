import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from router import routePCB, findJava

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", required=True, help="input .kicad_pcb file to route")
args = parser.parse_args()

java = findJava()
result = routePCB(args.input, java)
sys.exit(0 if result == 0 else 1)
