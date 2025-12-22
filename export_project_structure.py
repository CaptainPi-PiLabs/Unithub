# save as export_structure.py and run: python export_structure.py

import os

EXCLUDE_DIRS = {
    "venv", ".venv", "__pycache__", "migrations",
    "static", "media", ".git"
}

EXCLUDE_EXT = {".pyc", ".sqlite3", ".db"}

MAX_DEPTH = 6   # prevents huge trees; adjust as needed


def list_tree(root, prefix="", depth=0):
    if depth > MAX_DEPTH:
        return

    try:
        entries = sorted(os.listdir(root))
    except PermissionError:
        return

    for idx, name in enumerate(entries):
        path = os.path.join(root, name)

        if name in EXCLUDE_DIRS:
            continue
        if os.path.isfile(path):
            ext = os.path.splitext(name)[1]
            if ext in EXCLUDE_EXT:
                continue

        connector = "└── " if idx == len(entries) - 1 else "├── "
        print(prefix + connector + name)

        if os.path.isdir(path):
            next_prefix = prefix + ("    " if idx == len(entries) - 1 else "│   ")
            list_tree(path, next_prefix, depth + 1)


if __name__ == "__main__":
    print("Project structure:\n")
    list_tree(".")
