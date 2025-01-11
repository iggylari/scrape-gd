from datetime import datetime

from pandas import DataFrame


class ParquetStorage:
    def __init__(self, country: str, date: datetime):
        self.__country = country
        self.__date = date
        pass

    def save(self, dataframe: DataFrame) -> None:
        date_str = self.__date.strftime('%y-%m-%d %H%M%S')
        dataframe.to_parquet(f'parquet/data_{self.__country}_{date_str}.parquet', compression='gzip')
