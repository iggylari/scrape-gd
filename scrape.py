import argparse
import sys
from typing import Tuple

import selenium.webdriver as webdriver
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from wakepy import keep

from GlassdoorSite import GlassdoorSite
from DuckDbStorage import DuckDbStorage
from ParquetStorage import ParquetStorage

SITES = [
    ("www.glassdoor.ie", "IE"),
    ("www.glassdoor.de", "DE"),
    ("www.glassdoor.fr", "FR"),
    ("www.glassdoor.co.uk", "UK"),
    ("www.glassdoor.nl", "NL")
]


def main() -> int:
    parser = argparse.ArgumentParser(
        prog='Glassdoor scraper',
        description='Acquires job information from Glassdoor search pages')
    parser.add_argument('-c', '--countries', nargs='+', choices=[c for url, c in SITES])
    parser.add_argument('-p', '--pages', default=0, type=int)
    args = parser.parse_args()

    sites = SITES if args.countries is None else [s for s in SITES if s[1] in args.countries]

    with keep.running():
        return parse_sites(sites, args.pages)


def parse_sites(sites: list[tuple[str, str]], n_pages: int = 0) -> int:
    for domain, country in sites:
        print(domain, country)
        driver = create_webdriver()
        site = GlassdoorSite(driver, domain)

        storage = DuckDbStorage('glassdoor.duckdb')
        existing_ids = storage.get_not_empty_ids(country)

        date = datetime.now()
        job_records, parse_exception = parse_site(site, country, existing_ids, date, n_pages)
        df = pd.DataFrame(job_records)
        row_count = len(df.index)
        print(f"{row_count} job records")
        print(df.count())

        if row_count:
            try:
                storage.save(df)
            except Exception as ex:
                print(ex, file=sys.stderr)

            parquet_storage = ParquetStorage(country, date)
            parquet_storage.save(df)

        if parse_exception:
            print(parse_exception, file=sys.stderr)
        driver.quit()

    return 0


def create_webdriver() -> webdriver.Remote:
    options = webdriver.ChromeOptions()
    return webdriver.Chrome(options=options)


def parse_site(site: GlassdoorSite, country: str, existing_ids: set[int], date: datetime, n_pages: int = 0) -> Tuple[list, Exception]:
    job_pages = site.parse_all_jobs(n_pages)
    if not job_pages:
        input("Check for captcha and resume")
        job_pages = site.parse_all_jobs(n_pages)

    job_records = []
    ex = None
    try:
        for job in tqdm(job_pages, desc="Progress"):
            if job.job_id in existing_ids:
                continue

            job_record = job.parse_job(country, date)
            if job_record:
                job_records.append(job_record)
            # break
    except Exception as e:
        ex = e
    finally:
        return job_records, ex


if __name__ == '__main__':
    sys.exit(main())