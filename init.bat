python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
md parquet
python init_duckdb.py
