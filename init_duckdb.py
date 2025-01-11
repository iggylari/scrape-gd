import sys

from DuckDbStorage import DuckDbStorage
from constants import DB_PATH


def main():
    DuckDbStorage(DB_PATH).create_tables()


if __name__ == '__main__':
    sys.exit(main())