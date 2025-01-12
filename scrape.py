import argparse
import sys

import selenium.webdriver as webdriver
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from wakepy import keep

from GlassdoorSite import GlassdoorSite
from DuckDbStorage import DuckDbStorage
from ParquetStorage import ParquetStorage
from SiteData import SiteData
from constants import SITES, DB_PATH


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

        storage = DuckDbStorage(DB_PATH)
        existing_ids = storage.get_not_empty_ids(country)

        date = datetime.now()
        site_data = parse_site(site, country, existing_ids, date, n_pages)
        df = pd.DataFrame(site_data.new_jobs)
        row_count = len(df.index)
        print(f"{row_count} job records")
        print(df.count())

        if row_count:
            try:
                storage.save(df)
                storage.mark_active(site_data.active_job_ids, country, date)
            except Exception as ex:
                print(ex, file=sys.stderr)

            parquet_storage = ParquetStorage(country, date)
            parquet_storage.save(df)

        if site_data.error:
            print(site_data.error, file=sys.stderr)
        driver.quit()

    return 0


def create_webdriver() -> webdriver.Remote:
    options = webdriver.ChromeOptions()
    return webdriver.Chrome(options=options)


def parse_site(site: GlassdoorSite, country: str, existing_ids: set[int], date: datetime, n_pages: int = 0) -> SiteData:
    job_pages = site.parse_all_jobs(n_pages)
    if not job_pages:
        input("Check for captcha and resume")
        job_pages = site.parse_all_jobs(n_pages)

    site_data = SiteData()
    try:
        for job in tqdm(job_pages, desc="Progress"):
            if job.job_id in existing_ids:
                site_data.active_job_ids.add(job.job_id)
                continue

            job_record = job.parse_job(country, date)
            if job_record:
                site_data.new_jobs.append(job_record)
    except Exception as e:
        site_data.error = e
    finally:
        return site_data


if __name__ == '__main__':
    sys.exit(main())