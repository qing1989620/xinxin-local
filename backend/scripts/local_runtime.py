"""Small read-only interface for the Windows launcher. Prints no owner data."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.runtime import active_tasks, source_fingerprint, missing_dependencies

if __name__ == "__main__":
    if sys.argv[1:] == ["fingerprint"]:
        print(source_fingerprint(ROOT))
    elif len(sys.argv) == 3 and sys.argv[1] == "active-tasks":
        print(active_tasks(Path(sys.argv[2])))
    elif sys.argv[1:] == ["check-dependencies"]:
        missing = missing_dependencies(ROOT)
        if missing:
            print("Dependencies to synchronize: " + ", ".join(missing))
            raise SystemExit(1)
    else:
        raise SystemExit("Expected fingerprint, check-dependencies or active-tasks DIRECTORY")
