import pcbnew

board = pcbnew.LoadBoard("../parakeyt-docs/reference-design/reference-design.kicad_pcb")
pcbnew.ExportSpecctraDSN(board, "out.dsn")


