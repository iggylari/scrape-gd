import json
import logging

from gpt import GptClient, GeneralColumns, GptColumns


class JobProcessor:
    def __init__(self, client: GptClient):
        self.client = client

    def gpt_process(self, id_: int, country: str, job_title: str, job_description: str) -> dict:
        job_text = f"Job title: {job_title}\n{job_description}"
        parsed_description = json.loads(self.client.analyze_job_description(job_text))
        out_descr = {
            GeneralColumns.ID.value: id_,
            GeneralColumns.COUNTRY.value: country,
            GeneralColumns.OTHER.value: None,
            GeneralColumns.TRANSLATION.value: None
        }
        for col, val in parsed_description.items():
            if col in GptColumns:
                if col == GptColumns.SALARY:
                    out_descr[col] = ensure_salary_value(val)
                elif col in [GptColumns.DE_JOB, GptColumns.SE_JOB, GptColumns.VISA_SUPPORT, GptColumns.WORK_PERMIT_REQUIRED]:
                    out_descr[col] = ensure_boolean(val)
                else:
                    out_descr[col] = val
            else:
                if out_descr[GeneralColumns.OTHER.value] is None:
                    out_descr[GeneralColumns.OTHER.value] = {}
                out_descr[GeneralColumns.OTHER.value][col] = val
                logging.warning(f"Unknown column {col} for {id_}")

        for col in GptColumns:
            if not col in out_descr:
                logging.debug(f"{col} not found in GPT answer for {id_}")
                out_descr[col] = None

        language = (out_descr[GptColumns.LANGUAGE.value]) or ''
        if language.casefold() != 'English'.casefold():
            out_descr[GeneralColumns.TRANSLATION.value] = self.client.translate(job_text)
        return out_descr


def ensure_salary_value(val):
    if type(val) is dict:
        if val:
            return json.dumps(val)
        else:
            return None
    elif val is None:
        return val
    else:
        logging.warning(type(val))
        logging.warning(val)
        return json.dumps({'value': val})


def ensure_boolean(val):
    val = str(val).casefold()
    if val == 'True'.casefold():
        return True
    elif val == 'False'.casefold():
        return False
    else:
        return None
