import os
import shutil
import sys

if len(sys.argv) < 2:
    print("Usage: copy_md_to_ghpages.py <gh-pages-clone-path>")
    sys.exit(2)

GH_PAGES_DIR = sys.argv[1]
DOCS_DIR = "docs"
LLMS_FILE = "llms.txt"

# Copy llms.txt into the root of gh-pages
if os.path.exists(LLMS_FILE):
    shutil.copy2(LLMS_FILE, os.path.join(GH_PAGES_DIR, "llms.txt"))

for root, _, files in os.walk(DOCS_DIR):
    for f in files:
        if not f.endswith(".md"):
            continue

        src_path = os.path.join(root, f)
        rel_path = os.path.relpath(src_path, DOCS_DIR)
        dest_path = os.path.join(GH_PAGES_DIR, rel_path)

        # Make sure the destination directory exists
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Copy the file as-is
        shutil.copy2(src_path, dest_path)