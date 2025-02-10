from datetime import datetime

from pandas import DataFrame


class ParquetStorage:
    def __init__(self, country: str, date: datetime):
        self._country = country
        self._date = date
        pass

    def save(self, dataframe: DataFrame) -> None:
        date_str = self._date.strftime('%y-%m-%d %H%M%S')
        dataframe.to_parquet(f'parquet/data_{self._country}_{date_str}.parquet', compression='gzip')
