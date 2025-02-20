import sys

from pandas import DataFrame
import json

import constants
from DuckDbStorage import DuckDbStorage
from gpt import GptClient, GptColumns, GeneralColumns


def main() -> int:
    client = GptClient()
    storage = DuckDbStorage(constants.DB_PATH)
    jobs_df = storage.get_not_gpt_processed_jobs(10)
    gpt_processed_rows = []
    for row in jobs_df.iterrows():
        id_ = row[1]['id']
        job_text = 'Job title: ' + row[1]['job_title'] + '\n' + row[1]['job_description']
        parsed_description = json.loads(client.analyze_job_description(job_text))
        out_descr = {
            GeneralColumns.ID.value: id_,
            GeneralColumns.COUNTRY.value: row[1][GeneralColumns.COUNTRY],
            GeneralColumns.OTHER.value: None
        }
        for col, val in parsed_description.items():
            if col in GptColumns:
                if col == GptColumns.SALARY:
                    out_descr[col] = ensure_salary_value(val)
                else:
                    out_descr[col] = val
            else:
                if out_descr[GeneralColumns.OTHER.value] is None:
                    out_descr[GeneralColumns.OTHER.value] = {}
                out_descr[GeneralColumns.OTHER.value][col] = val
                print(f"Unknown column {col} for {id_}")

        for col in GptColumns:
            if not col in out_descr:
                print(f"{col} not found in GPT answer for {id_}")

        if parsed_description[GptColumns.LANGUAGE.value].casefold() != 'English'.casefold():
            out_descr[GeneralColumns.TRANSLATION.value] = client.translate(job_text)
        print(parsed_description)
        gpt_processed_rows.append(out_descr)

    processed_df = DataFrame(gpt_processed_rows)
    print(processed_df)
    storage.save_gpt_processed(processed_df)

    return 0


def ensure_salary_value(val):
    if type(val) is dict:
        if val:
            return json.dumps(val)
        else:
            return None
    elif val is None:
        return val
    else:
        print(type(val))
        print(val)
        return json.dumps({'value': val})


if __name__ == '__main__':
    sys.exit(main())