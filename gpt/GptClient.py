import os
from openai import OpenAI

from gpt.GptColumns import GptColumns


class GptClient:
    def __init__(self):
        self._client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    def analyze_job_description(self, text: str) -> str:
        prompt = F"""In the given job description, extract information, put into JSON object (without markup) with keys:
        Key {GptColumns.DE_JOB}: Is this job related to Data Engineering ("True"/"False")? 
        Key {GptColumns.SE_JOB}: Is this job related to Software Engineering ("True"/"False")? 
        Key {GptColumns.EMPLOYER}: Employer name. 
        Key {GptColumns.SALARY}: Salary, if numbers are provided. JSON object with possible keys "min", "max", "value"
        Key {GptColumns.TECHNOLOGIES}: List all tools, programming languages and technologies used by employer, required or desirable for the candidate. Use exact single-word names for them: "Azure" for Microsoft Azure, "AWS" for Amazon Web Services or Amazon cloud, "GCP" for Google Cloud. Put into simple array.
        Key {GptColumns.INTERVIEW}: Any facts about interview process. Put into simple array.
        Key {GptColumns.ELIGIBILITY}: Which candidates are eligible, if stated.
        Key {GptColumns.WORK_PERMIT_REQUIRED}: Is candidate required to have a work permit or be a citizen ("True"/"False")?
        Key {GptColumns.LANGUAGE}: language of the job description
        Key {GptColumns.LANGUAGES_REQUIRED}: language required (in a simple array), if stated
        Key {GptColumns.GRADE}: job engineering level, one of: Intern, Junior, Middle, Senior, Architect, Lead, Principal, Staff, Distinguished, Fellow, if stated
        Key {GptColumns.WORK_MODEL}: office, hybrid, remote or WFA (for 100% remote or work-from-anywhere), if stated"""

        response = self._client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )

        return response.output_text

    def translate(self, text: str) -> str:
        prompt = 'Translate job description in English'
        response = self._client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )
        return response.output_text
