from datetime import datetime

import duckdb
from duckdb import DuckDBPyConnection
from pandas import DataFrame

from gpt import GeneralColumns, GptColumns


class DuckDbStorage:
    def __init__(self, path: str):
        self._path = path
        pass

    def get_existing_ids(self) -> set[int]:
        with self._connect() as ddb:
            # TODO: check for items with empty description
            return set([int(row[0]) for row in ddb.execute("SELECT DISTINCT(id) FROM raw_glassdoor").fetchall()])

    def get_not_empty_ids(self, country: str) -> set[int]:
        with self._connect() as ddb:
            sql = f"SELECT DISTINCT(id) FROM raw_glassdoor WHERE job_description IS NOT NULL AND country = '{country}'"
            return set([int(row[0]) for row in ddb.execute(sql).fetchall()])

    def save(self, dataframe: DataFrame):
        with self._connect() as ddb:
            ddb.register('dataframe', dataframe)
            return ddb.execute('INSERT INTO raw_glassdoor SELECT * FROM dataframe')

    def mark_active(self, job_ids: list[int], country: str, date: datetime):
        with self._connect() as ddb:
            dataframe = DataFrame(data={'id': list(job_ids)})
            ddb.register('dataframe', dataframe)
            sql = (f"INSERT INTO job_active_status (id, country, datetime) "
                   f"SELECT id, '{country}' AS country, '{date}' AS datetime "
                   f"FROM dataframe")
            ddb.execute(sql)

    def get_not_gpt_processed_jobs(self, count: int, countries: list[str] = None) -> DataFrame:
        country_filter = f"AND rg.country IN ({', '.join([f"'{c}'" for c in countries])})" if countries else ''
        with self._connect(True) as ddb:
            sql = f"""SELECT id, country, job_title, job_description 
    FROM raw_glassdoor rg 
    WHERE NOT EXISTS (FROM gpt_processed gp WHERE gp.id=rg.id AND gp.country=rg.country)
        AND job_description IS NOT NULL
        {country_filter} 
    ORDER BY datetime DESC 
    LIMIT {count}"""
            ddb.execute(sql)
            return ddb.df()

    def save_gpt_processed(self, dataframe: DataFrame):
        columns = [str(col) for col in GeneralColumns] + [str(col) for col in GptColumns]
        columns_str = ', '.join(columns)
        with self._connect() as ddb:
            ddb.register('dataframe', dataframe)
            return ddb.execute(f"INSERT INTO gpt_processed({columns_str}) SELECT {columns_str} FROM dataframe")

    def create_tables(self) -> None:
        commands = [
            """CREATE TABLE IF NOT EXISTS raw_glassdoor(
    id BIGINT, 
    country VARCHAR, 
    datetime TIMESTAMP, 
    age VARCHAR, 
    link VARCHAR, 
    job_title VARCHAR, 
    job_location VARCHAR, 
    salary_range VARCHAR, 
    salary_range_est_type VARCHAR, 
    company_name VARCHAR, 
    company_rating VARCHAR, 
    job_description VARCHAR, 
    job_description_html VARCHAR, 
    salary_range_2 VARCHAR, 
    salary_range_2_period VARCHAR, 
    salary_median_est VARCHAR, 
    salary_median_est_period VARCHAR, 
    company_size VARCHAR, 
    company_founded VARCHAR, 
    employment_type VARCHAR, 
    company_industry VARCHAR, 
    company_sector VARCHAR, 
    company_revenue VARCHAR, 
    company_recommend_to_friend VARCHAR, 
    company_approve_of_ceo VARCHAR, 
    company_ceo_name VARCHAR, 
    company_ceo_ratings DOUBLE, 
    career_opportunities_rating VARCHAR, 
    comp_and_benefits_rating VARCHAR, 
    culture_and_values_rating VARCHAR, 
    senior_management_rating VARCHAR, 
    work_life_balance_rating VARCHAR, 
    trust_reviews_html VARCHAR, 
    benefit_rating VARCHAR, 
    company_id INTEGER, 
    company_link VARCHAR,
    skills VARCHAR[])""",
            'CREATE TABLE IF NOT EXISTS job_active_status(id BIGINT NOT NULL, country VARCHAR NOT NULL, datetime TIMESTAMP NOT NULL)',
            """CREATE TABLE IF NOT EXISTS gpt_processed(
    id BIGINT NOT NULL,
    country VARCHAR NOT NULL,
    other JSON,
    de_job BOOLEAN,
    se_job BOOLEAN,
    employer VARCHAR,
    salary JSON,
    technologies VARCHAR[],
    interview VARCHAR[],
    eligibility VARCHAR,
    visa_support BOOLEAN,
    language VARCHAR,
    languages_required VARCHAR[],
    grade VARCHAR,
    work_model VARCHAR,
    translation VARCHAR,
    work_permit_required BOOLEAN)"""
        ]
        with self._connect() as ddb:
            for sql in commands:
                ddb.execute(sql)

    def _connect(self, readonly: bool = False) -> DuckDBPyConnection:
        return duckdb.connect(self._path, read_only=readonly)
