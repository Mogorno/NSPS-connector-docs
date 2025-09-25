# 1. Clone the repository

```
git clone https://github.com/Mogorno/NSPS-connector-docs.git
cd NSPS-connector-docs
```

# 2. Create & activate a virtual environment

```
# create venv
python -m venv .venv

# activate venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate
```

# 3. Install dependencies

```
pip install -r requirements.txt
```

# 4. Verify installation

```
mkdocs --version
```

# 5. Run local dev server

```
mkdocs serve
# then open http://127.0.0.1:8000/
```

# 6. Build static site

```
mkdocs build
```