import sys
import glob

def ensure_pcbnew():
    try:
        import pcbnew
        return
    except ImportError:
        pass

    candidates = [
        "/usr/lib/python3/dist-packages",
        "/usr/lib/kicad/lib/python3/dist-packages",
        "/usr/local/lib/python3/dist-packages",
    ]
    candidates += glob.glob("/usr/lib/python3.*/dist-packages")
    candidates += glob.glob("/usr/lib/kicad/lib/python3.*/dist-packages")

    for path in candidates:
        sys.path.insert(0, path)
        try:
            import pcbnew
            return
        except ImportError:
            sys.path.pop(0)

    raise ImportError(
        "pcbnew not found. Install KiCad (e.g. 'sudo apt install kicad') "
        "or activate a venv created with --system-site-packages."
    )
