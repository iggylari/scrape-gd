import argparse
import logging
import random
import sys
import time

import selenium.webdriver as webdriver
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from wakepy import keep

from GlassdoorSite import GlassdoorSite
from DuckDbStorage import DuckDbStorage
from ParquetStorage import ParquetStorage
from SiteData import SiteData
from constants import SITES, QUERIES, DB_PATH


def main() -> int:
    parser = argparse.ArgumentParser(
        prog='Glassdoor scraper',
        description='Acquires job information from Glassdoor search pages')
    parser.add_argument('-c', '--countries', nargs='+', choices=[c for _, c in SITES])
    parser.add_argument('-p', '--pages', default=0, type=int)
    parser.add_argument('-d', '--debug', default=False, type=bool)
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=log_level)
    sites = SITES if args.countries is None else [s for s in SITES if s[1] in args.countries]

    with keep.running():
        return parse_sites(sites, QUERIES, args.pages)


def parse_sites(sites: list[tuple[str, str]], queries: list[str], n_pages: int = 0) -> int:
    searches = [(s, c, q) for s, c in sites for q in queries]
    random.shuffle(searches)
    for domain, country, query in searches:
        print(domain, country)
        driver = create_webdriver()
        site = GlassdoorSite(driver, domain, query)

        storage = DuckDbStorage(DB_PATH)
        existing_ids = storage.get_not_empty_ids(country)

        date = datetime.now()
        site_data = parse_site(site, country, existing_ids, date, n_pages)
        df = pd.DataFrame(site_data.new_jobs)
        row_count = len(df.index)
        print(f"{row_count} new job records")

        if row_count:
            try:
                storage.save(df)
                storage.mark_active(site_data.active_job_ids, country, date)
            except Exception as ex:
                logging.error(ex)

            parquet_storage = ParquetStorage(country, date)
            parquet_storage.save(df)

        driver.quit()

        if site_data.error:
            if site_data.error is KeyboardInterrupt:
                raise site_data.error

            logging.error(site_data.error)

    return 0


def create_webdriver() -> webdriver.Remote:
    options = webdriver.ChromeOptions()
    return webdriver.Chrome(options=options)


def parse_site(site: GlassdoorSite, country: str, existing_ids: set[int], date: datetime, n_pages: int = 0) -> SiteData:
    attempts = 0
    while not (job_pages := site.parse_all_jobs(n_pages)) and attempts <= 10:
        print('.', end='')
        attempts += 1
        time.sleep(attempts)

    if not job_pages:
        input(" --- Check for captcha and resume:")
        job_pages = site.parse_all_jobs(n_pages)

    processed_ids = set()   # To avoid duplicates
    site_data = SiteData()
    try:
        for job in tqdm(job_pages, desc="Progress"):
            if job.job_id in processed_ids:
                continue
            if job.job_id in existing_ids:
                site_data.active_job_ids.add(job.job_id)
                continue

            job_record = job.parse_job(country, date)
            if job_record:
                site_data.new_jobs.append(job_record)
                if job_record['job_description'] is not None:
                    processed_ids.add(job.job_id)
    except Exception as e:
        site_data.error = e
    finally:
        return site_data


if __name__ == '__main__':
    sys.exit(main())