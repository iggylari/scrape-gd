import argparse
import logging
import os
import sys
from datetime import datetime

import utils
from json import JSONDecodeError

from pandas import DataFrame
from tqdm import tqdm

import constants
from DuckDbStorage import DuckDbStorage
from gpt import GptClient, GeneralColumns, JobProcessor

BATCH_SIZE = 50


def main() -> int:
    parser = argparse.ArgumentParser(
        prog='Glassdoor scraper',
        description='Process job descriptions with GPT to obtain and systematize various job characteristics'
    )
    parser.add_argument('-n', default=10, type=int)
    parser.add_argument('-c', '--countries', nargs='+', choices=[c for _, c, _ in constants.SITES])
    args = parser.parse_args()

    utils.prepare_dirs()

    processor = JobProcessor(GptClient())
    storage = DuckDbStorage(constants.DB_PATH)
    for start in range(0, args.n, BATCH_SIZE):
        count = min(BATCH_SIZE, args.n - start)
        jobs_df = storage.get_not_gpt_processed_jobs(count, args.countries or None)
        if jobs_df.empty:
            logging.info("No more jobs to process")
            break

        gpt_processed_rows = []
        try:
            jobs_data = zip(jobs_df['id'], jobs_df[GeneralColumns.COUNTRY], jobs_df['job_title'], jobs_df['job_description'])
            for id_, country, title, descr in tqdm(jobs_data, nrows=len(jobs_df.index), desc="Progress"):
                try:
                    out_descr = processor.gpt_process(id_, country, title, descr)
                    gpt_processed_rows.append(out_descr)
                except JSONDecodeError as ex:
                    logging.error(ex)
                    date_str = datetime.now().strftime('%y-%m-%d %H%M%S')
                    filename = f'{utils.RUNTIME_DIR}/parse_error_{date_str}.json'
                    print(ex.doc, file=open(filename, 'w'))
        finally:
            if gpt_processed_rows:
                processed_df = DataFrame(gpt_processed_rows)
                print(len(processed_df), 'jobs processed')
                save(storage, processed_df)

    return 0


def save(storage: DuckDbStorage, df: DataFrame) -> None:
    """Save DataFrame to DuckDb Storage. If failed, will try to save to Parquet file, otherwise desperately try to
    pickle."""
    try:
        storage.save_gpt_processed(df)
    except:
        date_str = datetime.now().strftime('%y-%m-%d %H%M%S')
        filename = f'{utils.PARQUET_DIR}/gpt_{date_str}.parquet'
        try:
            df.to_parquet(filename, compression='gzip')
        except:
            filename = f'{utils.PICKLE_DIR}/gpt_{date_str}.pkl'
            df.to_pickle(filename)
        logging.error(f"Failed to save to DuckDB. Saved to {filename}")
        raise


if __name__ == '__main__':
    sys.exit(main())