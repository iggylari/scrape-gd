import duckdb
from duckdb import DuckDBPyConnection
from pandas import DataFrame


class DuckDbStorage:
    def __init__(self, path: str):
        self.__path = path
        pass

    def get_existing_ids(self) -> set[int]:
        with self.__connect() as ddb:
            # TODO: check for items with empty description
            return set([int(row[0]) for row in ddb.execute("SELECT DISTINCT(id) FROM raw_glassdoor").fetchall()])

    def get_not_empty_ids(self, country: str) -> set[int]:
        with self.__connect() as ddb:
            sql = f"SELECT DISTINCT(id) FROM raw_glassdoor WHERE job_description IS NOT NULL AND country = '{country}'"
            return set([int(row[0]) for row in ddb.execute(sql).fetchall()])

    def save(self, dataframe: DataFrame):
        with self.__connect() as ddb:
            ddb.register('dataframe', dataframe)
            return ddb.execute('INSERT INTO raw_glassdoor SELECT * FROM dataframe')

    def __connect(self) -> DuckDBPyConnection:
        return duckdb.connect(self.__path)
