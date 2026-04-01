# ruff: noqa: E701, E731
# import uuid
from typing import Tuple
from kiutils.board import Board, GrRect
from kiutils.footprint import Footprint, FpRect
from kiutils.items.common import Position, Net
from kiutils.utils import sexpr
from pprint import pprint
import json

MCU_FP = "./components/RP2040-Zero/RP2040-Zero.pretty/rp2040-zero-tht.kicad_mod"
KEY_FP = "./components/AH49FNTR_G1/AH49FNTR_G1.pretty/SC59_DIO_KeyswitchOutline_NoRuleArea.kicad_mod"
KEY_MOS_FP = "./components/AH49FNTR_G1/AH49FNTR_G1.pretty/SC59_DIO_KeyswitchOutline_NoRuleArea_mosfet.kicad_mod"
TLA_FP = "./components/TLA2528IRTER/TLA2528IRTER.pretty/WQFN16_RTE_TEX_with_caps_and_Rs.kicad_mod"

def count(start=0, step=1):
    # count(10) → 10 11 12 13 14 ...
    # count(2.5, 0.5) → 2.5 3.0 3.5 ...
    n = start
    while True:
        yield n
        n += step

def islice(iterable, *args):
    # islice('ABCDEFG', 2) → A B
    # islice('ABCDEFG', 2, 4) → C D
    # islice('ABCDEFG', 2, None) → C D E F G
    # islice('ABCDEFG', 0, None, 2) → A C E G

    s = slice(*args)
    start = 0 if s.start is None else s.start
    stop = s.stop
    step = 1 if s.step is None else s.step
    if start < 0 or (stop is not None and stop < 0) or step <= 0:
        raise ValueError

    indices = count() if stop is None else range(max(start, stop))
    next_i = start
    for i, element in zip(indices, iterable):
        if i == next_i:
            yield element
            next_i += step


def batched(iterable, n, *, strict=False):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        if strict and len(batch) != n:
            raise ValueError('batched(): incomplete batch')
        yield batch

net_counter = 0
def generate(config): 

    base = Board.create_new()
    def new_net(s: str) -> Net:
        global net_counter
        return Net(net_counter := net_counter + 1, s)

    u = 19.05


    v3_3 = new_net("+3.3v")
    gnd = new_net("GND")
    sda = new_net("SDA")
    scl = new_net("SCL")
    base.nets.extend([v3_3, gnd, sda, scl])

    # with open("config.json", "r") as f:
    #     config = json.load(f)

    width, height = config["width"], config["length"]

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

    def find_margins_fp(fp) -> Tuple[Position, Position]:
        start, end = None, None
        for item in fp.graphicItems:
            if type(item) is FpRect and item.layer == "Margin":
                start = item.start
                end = item.end

        assert start is not None, "could not find margin start!"
        assert end is not None, "could not find margin end!"
        return start, end

    def set_net(fp: Footprint, pad: int, net: Net):
        pad = next(filter(lambda a: a.number == str(pad), fp.pads), None)
        assert pad is not None, f"could not find pad {pad}!"
        pad.net = net

    # groups keys into seperate matrices
    def group_keys(keys: list[dict]) -> list[list[list]]:
        return [list(batched(m, 8)) for m in batched(keys, 64)]

    
        # TODO: implement
        # return [[[keys[0], keys[1], keys[2]], [keys[3], keys[4], keys[5]], [keys[6], keys[7], keys[8]]]]


    def float_range(start, stop, step):
        x = start
        while x < stop:
            yield x
            x += step

    def place(fp):
        fp_start_off, fp_end_off = find_margins_fp(fp)
    
        # set positions of everything
        for x in float_range(0, width*u, u*0.1):
            for y in float_range(0, height*u, u*0.1):

                fp_start = Position(x+fp_start_off.X, y+fp_start_off.X)
                fp_end = Position(x+fp_end_off.X, y+fp_end_off.Y)
                good = True
            
                # check for overlap by looking at silkscreen box
                for other in base.footprints:
                    abs = other.position
                    start_off, end_off = find_margins_fp(other)

                    start = Position(abs.X+start_off.X, abs.Y+start_off.Y)
                    end = Position(abs.X+end_off.X, abs.Y+end_off.Y)

                    if not (fp_end.X <= start.X or\
                       fp_start.X >= end.X or\
                       fp_end.Y <= start.Y or\
                       fp_start.Y >= end.Y):
                        good = False
                        break

                if good:
                    return Position(x, y)

        assert False, "could not find good location"
 
    mcu_x, mcu_y, mcu_rotation = [config["mcu"]["pos"]["x"], config["mcu"]["pos"]["z"], config["mcu"]["pos"]["z"]]
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
        col_nets = [new_net(f"m{mi}c{ci}") for ci in range(max(map(len, matrix)))]
        row_nets = [new_net(f"m{mi}r{ri}") for ri in range(len(matrix))]
        print(col_nets, row_nets)
        base.nets.extend(col_nets)
        base.nets.extend(row_nets)

        for ri, row in enumerate(matrix):

            # add the actual row net that comes from the mosfet
            rn = new_net(f"m{mi}r{ri}MOS")
            base.nets.extend([rn])
        
            for ci, elem in enumerate(row):
                key_fp = Footprint.from_file(KEY_FP if ci != 0 else KEY_MOS_FP)
                # x, y, a = elem["pos"]
                x, y, a = [elem["x"], elem["y"], elem["z"]]
                key_fp.position = Position((x+0.5) * u, (y+0.5) * u, a)
            
                if ci == 0:
                    set_net(key_fp, 4, row_nets[ri])
                    set_net(key_fp, 5, gnd)
                    set_net(key_fp, 6, v3_3)

                set_net(key_fp, 1, rn)
                set_net(key_fp, 2, col_nets[ci])
                set_net(key_fp, 3, gnd)
            
                base.footprints.append(key_fp)
    
        # do adc expander
        # want to place on the bounding box for the keys, then want to place on an open space near the mcu
        adc_fp = Footprint.from_file(TLA_FP)
        adc_pins = [15, 16, 1, 2, 3, 4, 5, 6]
        decap1_net = new_net(f"decap1{mi}")
        addr1_net = new_net(f"addr1{mi}")
        base.nets.extend([decap1_net, addr1_net])
        for ci, col_net in enumerate(col_nets):
            set_net(adc_fp, adc_pins[ci], col_net)
        set_net(adc_fp, 14, sda)
        set_net(adc_fp, 13, scl)
        set_net(adc_fp, 17, gnd)
        set_net(adc_fp, 9, gnd)
        set_net(adc_fp, 10, v3_3) # dvdd
        set_net(adc_fp, 7, v3_3) # avdd
        set_net(adc_fp, 8, decap1_net)
        set_net(adc_fp, 11, addr1_net)

        # C C R R
        # first c is decap net
        set_net(adc_fp, 18, decap1_net) # decap -> gnd
        set_net(adc_fp, 19, gnd)
        # second c is avdd -> gnd
        set_net(adc_fp, 20, v3_3)
        set_net(adc_fp, 19, gnd)
        # first R is decap -> addr
        set_net(adc_fp, 22, decap1_net)
        set_net(adc_fp, 21, addr1_net)
        # second R is addr -> gnd
        set_net(adc_fp, 24, addr1_net)
        set_net(adc_fp, 23, gnd)
        # TODO: specify R values


        gpio_fp = Footprint.from_file(TLA_FP)
        gpio_pins = [15, 16, 1, 2, 3, 4, 5, 6]
        decap2_net = new_net(f"decap2{mi}")
        addr2_net = new_net(f"addr2{mi}")
        base.nets.extend([decap2_net, addr2_net])
        for ri, row_net in enumerate(row_nets):
            set_net(gpio_fp, gpio_pins[ri], row_net)
        set_net(gpio_fp, 14, sda)
        set_net(gpio_fp, 13, scl)
        set_net(gpio_fp, 17, gnd)
        set_net(gpio_fp, 9, gnd)
        set_net(gpio_fp, 10, v3_3) # dvdd
        set_net(gpio_fp, 7, v3_3) # avdd
        set_net(gpio_fp, 8, decap2_net)
        set_net(gpio_fp, 11, addr2_net)
        set_net(gpio_fp, 18, decap2_net)
        set_net(gpio_fp, 19, gnd)
        set_net(gpio_fp, 20, v3_3)
        set_net(gpio_fp, 19, gnd)
        set_net(gpio_fp, 22, decap2_net)
        set_net(gpio_fp, 21, addr2_net)
        set_net(gpio_fp, 24, addr2_net)
        set_net(gpio_fp, 23, gnd)

        # thermal vias
        for pin in range(18, 24):
            set_net(gpio_fp, pin, gnd)

        adc_fp.position = place(adc_fp)
        base.footprints.append(adc_fp)
        gpio_fp.position = place(gpio_fp)
        base.footprints.append(gpio_fp)


    base.graphicItems.append(GrRect(Position(0, 0), Position(width * u, height * u), "Edge.Cuts"))

    base.to_file("./test.kicad_pcb")

               

# pprint.pprint(Board.from_file("./simplest.kicad_pcb"))

