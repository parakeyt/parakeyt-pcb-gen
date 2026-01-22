# ruff: noqa: E701, E731
# import uuid
from typing import Tuple
from kiutils.board import Board, GrRect
from kiutils.footprint import Footprint
from kiutils.items.common import Position, Net
from kiutils.utils import sexpr
# from pprint import pprint
import json

MCU_FP = "./components/RP2040-Zero/RP2040-Zero.pretty/rp2040-zero-tht.kicad_mod"
KEY_FP = "./components/AH49FNTR_G1/AH49FNTR_G1.pretty/SC59_DIO_KeyswitchOutline_NoRuleArea.kicad_mod"
CAP_FP = "./components/CAP/C_0805_2012Metric_Pad1.18x1.45mm_HandSolder.kicad_mod"
ADC_FP = "./components/TLA2528IRTER/TLA2528IRTER.pretty/WQFN16_RTE_TEX.kicad_mod"
GPIO_FP = "./components/TLC59208FIRGYR/TLC59208FIRGYR.pretty/RGY16_2P55X2P05.kicad_mod"

# cap_fp2 = Footprint.from_file("./components/CAP/C_0805_2012Metric_Pad1.18x1.45mm_HandSolder.kicad_mod")
base = Board.create_new()
net_counter = 0
def new_net(s: str) -> Net:
    global net_counter
    return Net(net_counter := net_counter + 1, s)

u = 19.05




v3_3 = new_net("+3.3v")
gnd = new_net("GND")
sda = new_net("SDA")
scl = new_net("SCL")
base.nets.extend([v3_3, gnd, sda, scl])

with open("config.json", "r") as f:
    config = json.load(f)

def find_margins(fp_filepath: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    start, end = None, None
    s = None
    with open(fp_filepath, "r") as f:
        s = f.read()

    data = sexpr.parse_sexp(s)
    for a in data:
        if type(a) is not list: continue
        if a[0] != "fp_rect": continue  
        ismargin = False
        for b in a[1:]:
            if b[0] != "layer": continue
            if b[1] == "Margin": ismargin = True
    
        if not ismargin: continue
        for b in a[1:]:
            if b[0] == "start": start = [b[1], b[2]]
            if b[0] == "end": end = [b[1], b[2]]

    assert start is not None, f"could not find margin start in {fp_filepath}!"
    assert end is not None, f"could not find margin end in {fp_filepath}!"
    return start, end

def set_net(fp: Footprint, pad: int, net: Net):
    pad = next(filter(lambda a: a.number == str(pad), fp.pads), None)
    assert pad is not None, f"could not find pad {pad}!"
    pad.net = net

# groups keys into seperate matrices
def group_keys(keys: list[dict]) -> list[list[list]]:
    # TODO: implement
    return [[[keys[0], keys[1], keys[2]], [keys[3], keys[4], keys[5]], [keys[6], keys[7], keys[8]]]]

mcu_x, mcu_y, mcu_rotation = config["mcu"]["pos"]
mcu_start, mcu_end = find_margins(MCU_FP)
mcu_fp = Footprint.from_file(MCU_FP)
mcu_fp.position = Position(mcu_x * u - mcu_start[0], mcu_y * u - mcu_start[1], mcu_rotation)
base.footprints.append(mcu_fp)

set_net(mcu_fp, 21, v3_3)
set_net(mcu_fp, 22, gnd)
set_net(mcu_fp, 1, sda)
set_net(mcu_fp, 2, scl)


matrices = group_keys(config["keys"])

for mi, matrix in enumerate(matrices):
    # create footprints and set positions
    col_nets = [new_net(f"m{mi}c{ci}") for ci in range(len(matrix))]
    row_nets = [new_net(f"m{mi}c{ci}") for ci in range(max(map(len, matrix)))]
    base.nets.extend(col_nets)
    base.nets.extend(row_nets)

    for ri, row in enumerate(matrix):
        for ci, elem in enumerate(row):
            key_fp = Footprint.from_file(KEY_FP)
            x, y, a = elem["pos"]
            key_fp.position = Position((x+0.5) * u, (y+0.5) * u, a)
            
            set_net(key_fp, 1, row_nets[ri])
            set_net(key_fp, 2, col_nets[ci])
            set_net(key_fp, 3, gnd)
            
            base.footprints.append(key_fp)
    
    # do adc expander
    # want to place on the bounding box for the keys, then want to place on an open space near the mcu
    adc_fp = Footprint.from_file(ADC_FP)
    adc_pins = [15, 16, 1, 2, 3, 4, 5, 6]
    decap_net = new_net(f"decap{mi}")
    for ci, col_net in enumerate(col_nets):
        set_net(adc_fp, adc_pins[ci], col_net)
    set_net(adc_fp, 14, sda)
    set_net(adc_fp, 13, scl)
    set_net(adc_fp, 17, gnd)
    set_net(adc_fp, 10, v3_3) # dvdd
    set_net(adc_fp, 7, v3_3) # avdd
    set_net(adc_fp, 8, decap_net)

    decap_fp = Footprint.from_file(CAP_FP)
    set_net(decap_fp, 1, decap_net)
    set_net(decap_fp, 2, gnd)
    
    # TODO: for mi > 2 use resistors
    addr_nets = [decap_net, None]
    if addr_nets[mi] is not None:
        set_net(adc_fp, 11, addr_nets[mi])

    # do led driver
    gpio_fp = Footprint.from_file(GPIO_FP)
    set_net(gpio_fp, 15, sda)
    set_net(gpio_fp, 14, scl)
    set_net(gpio_fp, 16, v3_3)
    set_net(gpio_fp, 17, gnd) # EPAD
    set_net(gpio_fp, 8, gnd)
    set_net(gpio_fp, 13, v3_3) # active-low reset

    # addresses 0, 7, 6 are reserved
    set_net(gpio_fp, 1, v3_3 if mi + 1 & 1 else gnd)
    set_net(gpio_fp, 2, v3_3 if (mi + 1 << 1) & 1 else gnd)
    set_net(gpio_fp, 3, v3_3 if (mi + 1 << 2) & 1 else gnd)

    row_pins = [4, 5, 6, 7, 9, 10, 11, 12]
    for ri, row_net in enumerate(row_nets):
        set_net(gpio_fp, row_pins[ri], row_net)

    # thermal vias
    for pin in range(18, 24):
        set_net(gpio_fp, pin, gnd)

    # do gnd cap for both
    cap1_fp = Footprint.from_file(CAP_FP)
    set_net(cap1_fp, 1, v3_3)
    set_net(cap1_fp, 2, gnd)

    # set positions of everything
    adc_fp.position = Position(100, 100)
    gpio_fp.position = Position(100, 110)
    decap_fp.position = Position(105, 120)
    cap1_fp.position = Position(100, 120)

    base.footprints.extend([adc_fp, gpio_fp, cap1_fp, decap_fp])
    base.nets.extend([decap_net])


width, height = config["width"], config["length"]
base.graphicItems.append(GrRect(Position(0, 0), Position(width * u, height * u), "Edge.Cuts"))

base.to_file("./test.kicad_pcb")


# pprint.pprint(Board.from_file("./simplest.kicad_pcb"))

