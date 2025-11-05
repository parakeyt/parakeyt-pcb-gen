
import uuid
from kiutils.schematic import Schematic, SchematicSymbol, Position, Property, SymbolProjectInstance, SymbolProjectPath
from kiutils.symbol import SymbolLib, Symbol

rp2040_lib = SymbolLib.from_file("./components/RP2040-Zero/RP2040-Zero.kicad_sym")
sym: Symbol = next(filter(lambda a: a.entryName == "rp2040-zero", rp2040_lib.symbols))
sym.libId = "rp2040-zero"

base = Schematic.create_new()
base.libSymbols.append(sym)
base.uuid = uuid.uuid4()

rp2040_sym = SchematicSymbol()
rp2040_sym.uuid = uuid.uuid4()
rp2040_sym.libId = "rp2040-zero"
rp2040_sym.position = Position(50.0, 50.0, 0)
rp2040_sym.unit = 1
rp2040_sym.inBom = 1
rp2040_sym.onBoard = True
rp2040_sym.pins = {str(i): uuid.uuid4() for i in range(1, 24)}
rp2040_sym.instances.append(SymbolProjectInstance("", [SymbolProjectPath(f"/{base.uuid}", "MCU1")]))

rp2040_sym.properties.append(Property("Reference", "MCU1", position=rp2040_sym.position))
rp2040_sym.properties.append(Property("Value", "RP2040-Zero", position=rp2040_sym.position))
rp2040_sym.properties.append(Property("Footprint", "RP2040-Zero:rp2040-zero-tht", position=rp2040_sym.position))
# print(rp2040_sym)

base.schematicSymbols.append(rp2040_sym)
base.to_file("test.kicad_sch")



# print(Schematic.from_file("../parakeyt-docs/reference-design/reference-design.kicad_sch").to_file("test.kicad_sch"))

