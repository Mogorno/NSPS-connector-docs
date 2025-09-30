import os
import shutil

DOCS_DIR = "docs"
SITE_DIR = "site"
LLMS_FILE = "llms.txt"

if os.path.exists(LLMS_FILE):
    dest_llms = os.path.join(SITE_DIR, "llms.txt")
    os.makedirs(os.path.dirname(dest_llms), exist_ok=True)
    shutil.copy2(LLMS_FILE, dest_llms)


for root, _, files in os.walk(DOCS_DIR):
    ''' Copy source .md files to the SITE_DIR so that they are available at the same URL '''
    for f in files:
        if f.endswith(".md"):
            src_path = os.path.join(root, f)
            # the relative path inside DOCS_DIR
            rel_path = os.path.relpath(src_path, DOCS_DIR)
            # the destination path
            dest_path = os.path.join(SITE_DIR, rel_path)

            # ensure directory exists in SITE_DIR
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # copy the file
            shutil.copy2(src_path, dest_path)