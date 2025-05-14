import json
import os
import pathlib

RUNTIME_DIR = pathlib.Path('runtime')
PARQUET_DIR = RUNTIME_DIR / 'parquet'
PICKLE_DIR = RUNTIME_DIR / 'pickle'
COOKIES_SUFFIX = 'cookies.json'


def prepare_dirs():
    os.makedirs(PARQUET_DIR, exist_ok=True)
    os.makedirs(PICKLE_DIR, exist_ok=True)


def save_cookies(cookies: list, site: str):
    with open(RUNTIME_DIR / f"{site}_{COOKIES_SUFFIX}", 'w') as f:
        json.dump(cookies, f)


def load_cookies(site: str) -> list:
    path = RUNTIME_DIR / f"{site}_{COOKIES_SUFFIX}"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    else:
        print(f"Cookies file not found: {path}")
        return []
