import pcbnew

board = pcbnew.LoadBoard("test.kicad_pcb")
counter = 1

for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("REF"):
        fp.SetReference(f"SW{counter}")
        counter += 1

board.Save("test.kicad_pcb")
print(f"Done! {counter - 1} switches renamed.")