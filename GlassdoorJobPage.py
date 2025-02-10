import logging
import re
import time
from datetime import datetime

import selenium.webdriver as webdriver
from selenium.common import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from SiteTools import SiteTools


class GlassdoorJobPage(SiteTools):
    def __init__(self, driver: webdriver.Remote, job_element: WebElement):
        super().__init__(driver)
        self._job_element = job_element
        self.job_id = int(self._job_element.find_element(By.XPATH, './..').get_attribute("data-jobid"))

    def parse_job(self, country: str, date: datetime) -> dict:
        job_id = self.job_id
        job_record = {
            'id': job_id,
            'country': country,
            'datetime': date,
            'age': None,
            'link': None,
            'job_title': None,
            'job_location': None,
            'salary_range': None,
            'salary_range_est_type': None,
            'company_name': None,
            'company_rating': None,
            'job_description': None,
            'job_description_html': None,
            'salary_range_2': None,
            'salary_range_2_period': None,
            'salary_median_est': None,
            'salary_median_est_period': None,
            "company_size": None,
            "company_founded": None,
            "employment_type": None,
            "company_industry": None,
            "company_sector": None,
            "company_revenue": None,
            "company_recommend_to_friend": None,
            "company_approve_of_ceo": None,
            "company_ceo_name": None,
            "company_ceo_ratings": None,

            "career_opportunities_rating": None,
            "comp_and_benefits_rating": None,
            "culture_and_values_rating": None,
            "senior_management_rating": None,
            "work_life_balance_rating": None,
            "trust_reviews_html": None,
            "benefit_rating": None,
            'company_id': None,
            'company_link': None,
            'skills': None,
        }

        self._close_popup()

        job_element = self._job_element
        try:
            job_element.click()
        except ElementClickInterceptedException:
            logging.debug('Click intercepted, try close popup and open job')
            self._close_popup()
            job_element.click()

        try:
            job_record['age'] = job_element.find_element(By.CSS_SELECTOR, '[data-test="job-age"]').text
        except NoSuchElementException:
            logging.warning(f'Failed to parse vacation age for {job_id}')

        try:
            job_title = job_element.find_element(By.CSS_SELECTOR, '[data-test="job-title"]')
            job_record['link'] = job_title.get_attribute("href")
            job_record['job_title'] = job_title.text
        except NoSuchElementException:
            logging.warning(f'Failed to parse link and title for {job_id}')

        try:
            job_record['job_location'] = job_element.find_element(By.CSS_SELECTOR, '[data-test="emp-location"]').text
        except NoSuchElementException:
            logging.info(f'Failed to parse job location for {job_id}')

        try:
            descr_snippet = job_element.find_element(By.CSS_SELECTOR, '[data-test="descSnippet"]')
            descr_snippet_children = descr_snippet.find_elements(By.TAG_NAME, 'div')
            if len(descr_snippet_children) >= 2:
                skills_html = descr_snippet_children[1].get_attribute('innerHTML')
                skills_match = re.findall('<b>.*</b>\\s*(.+)', skills_html)
                if skills_match:
                    job_record['skills'] = [skill.strip() for skill in skills_match[0].split(',')]
                else:
                    logging.warning("Skills in job description snippet don't match")
        except NoSuchElementException:
            logging.warning(f'Cannot find job description snippet for {job_id}')

        try:
            salary_range = job_element.find_element(By.CSS_SELECTOR, '[data-test="detailSalary"]')
            job_record['salary_range'] = salary_range.text
            job_record['salary_range_est_type'] = salary_range.find_element(
                By.XPATH,
                'span[starts-with(@class,"JobCard_salaryEstimateType")]'
            ).text
        except NoSuchElementException:
            logging.info(f'Failed to parse salary for {job_id}')

        try:
            job_record['company_name'] = job_element.find_element(
                By.XPATH,
                './/span[starts-with(@class,"EmployerProfile_compactEmployerName")]'
            ).text
            try:
                job_record['company_rating'] = job_element.find_element(
                    By.XPATH,
                    './/div[starts-with(@class,"EmployerProfile_ratingContainer")]'
                ).text
            except NoSuchElementException:
                pass
        except NoSuchElementException:
            logging.warning(f'Failed to parse company for {job_id}')

        if not self._ensure_tab_selected(job_element):
            logging.info('Failed, will skip details')
            return job_record

        attempts = 0
        while not self._click_show_more() and attempts <= 10:
            time.sleep(1)
            attempts += 1

        details = JobDetails(self._driver, job_id)
        try:
            details.parse_details(job_record)
        except NoDetailsTabException:
            logging.error(f'Job description for {job_id} not loaded')

        return job_record

    def _click_show_more(self) -> bool:
        self._close_popup()
        try:
            btn = self._driver.find_element(By.XPATH, '//button[starts-with(@class,"ShowMoreCTA")]')
            expanded_state = btn.get_attribute('aria-expanded')
            logging.debug(f"Show more button state {expanded_state}")
            if expanded_state == 'false':
                btn.click()
                return False
            elif expanded_state == 'true':
                return True
            else:
                raise ShowMoreUnexpectedState(expanded_state)
        except NoSuchElementException:
            logging.debug('No show more button')
            return False
        except ElementClickInterceptedException:
            logging.debug('Click intercepted, try close popup')
            self._close_popup()
            return False

    @staticmethod
    def _ensure_tab_selected(job_element: WebElement) -> bool:
        attempts = 0
        while not GlassdoorJobPage._check_tab_selected(job_element) and attempts < 8:
            if attempts == 0:
                print('Job element not activated - try more .', end='')
            else:
                print('.', end='')
            job_element.click()
            time.sleep(1)
            attempts += 1

        return GlassdoorJobPage._check_tab_selected(job_element)

    @staticmethod
    def _check_tab_selected(job_element: WebElement) -> bool:
        return job_element.get_attribute('data-selected') == 'true'


class JobDetails:
    def __init__(self, driver: webdriver.Remote, job_id: int):
        self._driver = driver
        self._job_id = job_id
        self._init_tab()

    def _init_tab(self):
        try:
            job_details_tab = self._driver.find_element(
                By.XPATH,
                './/div[starts-with(@class,"JobDetails_jobDetailsContainer")]'
            )
        except NoSuchElementException:
            raise NoDetailsTabException()

        try:
            job_details_tab.find_element(By.ID, f'jd-job-title-{self._job_id}')
        except NoSuchElementException:
            raise JobTitleNotFoundException(self._job_id)

        self._tab = job_details_tab

    def parse_details(self, job_record: dict) -> None:
        job_id = self._job_id

        try:
            employer_profile = self._tab.find_element(
                By.XPATH,
                './/a[starts-with(@class,"EmployerProfile_profileContainer_")]'
            )
            job_record['company_id'] = int(employer_profile.get_attribute('id'))
            job_record['company_link'] = employer_profile.get_attribute("href")
        except NoSuchElementException:
            pass

        try:
            job_description = self._tab.find_element(
                By.XPATH,
                './/div[starts-with(@class,"JobDetails_jobDescription_")]'
            )
            job_record['job_description'] = job_description.text
            job_record['job_description_html'] = job_description.get_attribute('innerHTML')
            length1 = len(job_record['job_description'])
            if length1 < 1000:
                time.sleep(1)
                job_record['job_description'] = job_description.text
                job_record['job_description_html'] = job_description.get_attribute('innerHTML')
                length2 = len(job_record['job_description'])
                if length2 > length1:
                    logging.warning(f'More description after retry {job_id}')
        except NoSuchElementException:
            logging.warning(f'Failed to parse job description for {job_id}')

        try:
            salary_estimate = self._tab.find_element(
                By.XPATH,
                './/div[starts-with(@class,"SalaryEstimate_salaryEstimateContainer_")]'
            )
            try:
                salary_range = salary_estimate.find_element(
                    By.XPATH,
                    './/div[starts-with(@class,"SalaryEstimate_salaryRange")]'
                )
                job_record['salary_range_2'] = salary_range.text.split('/')[0]
                job_record['salary_range_2_period'] = salary_range.find_element(
                    By.XPATH,
                    'span[starts-with(@class,"SalaryEstimate_payPeriod")]'
                ).text
            except NoSuchElementException:
                logging.info(f'Failed to parse salary range 2 from job details for {job_id}')
            try:
                salary_estimate_number = salary_estimate.find_element(
                    By.XPATH,
                    './/div[starts-with(@class,"SalaryEstimate_salaryEstimateNumber")]'
                )
                job_record['salary_median_est'] = salary_estimate_number.find_element(
                    By.XPATH,
                    'div[starts-with(@class,"SalaryEstimate_medianEstimate")]'
                ).text.split('/')[0]
                job_record['salary_median_est_period'] = salary_estimate_number.find_element(
                    By.XPATH,
                    'div[starts-with(@class,"SalaryEstimate_payPeriod")]'
                ).text
            except NoSuchElementException:
                logging.info(f'Failed to parse salary median for {job_id}')
        except NoSuchElementException:
            logging.info(f'Failed to parse salary 2 for {job_id}')

        company_overview_values = self._tab.find_elements(
            By.XPATH,
            './/div[starts-with(@class,"JobDetails_overviewItemValue")]'
        )
        if len(company_overview_values) == 6:
            job_record.update({
                "company_size": company_overview_values[0].text,
                "company_founded": company_overview_values[1].text,
                "employment_type": company_overview_values[2].text,
                "company_industry": company_overview_values[3].text,
                "company_sector": company_overview_values[4].text,
                "company_revenue": company_overview_values[5].text
            })

        company_recommend_donuts = self._tab.find_elements(
            By.XPATH,
            './/ul[starts-with(@class,"JobDetails_employerStatsDonuts")]//div[starts-with(@class,"JobDetails_donutWrapper")]'
        )
        if len(company_recommend_donuts) == 2:
            job_record["company_recommend_to_friend"] = company_recommend_donuts[0].text
            job_record["company_approve_of_ceo"] = company_recommend_donuts[1].text

        try:
            ceo_wrapper = self._tab.find_element(
                By.XPATH,
                './/div[starts-with(@class,"JobDetails_ceoTextWrapper")]'
            )
            job_record["company_ceo_name"] = ceo_wrapper.find_element(
                By.XPATH,
                'div[starts-with(@class,"JobDetails_ceoName")]'
            ).text

            ceo_ratings = ceo_wrapper.find_element(By.XPATH, 'span[starts-with(@class,"JobDetails_donutText")]').text
            if ceo_ratings != '':
                try:
                    job_record["company_ceo_ratings"] = int(''.join([c for c in ceo_ratings.split(' ')[0] if c.isdigit()]))
                except ValueError:
                    logging.error(f"Error when parsing CEO ratings: '{ceo_ratings}'")

        except NoSuchElementException:
            logging.info(f'Failed to parse CEO rating for {job_id}')

        company_ratings = self._tab.find_elements(
            By.XPATH,
            './/div[starts-with(@class,"JobDetails_ratingScore")]'
        )
        if len(company_ratings) == 5:
            job_record["career_opportunities_rating"] = company_ratings[0].text
            job_record["comp_and_benefits_rating"] = company_ratings[1].text
            job_record["culture_and_values_rating"] = company_ratings[2].text
            job_record["senior_management_rating"] = company_ratings[3].text
            job_record["work_life_balance_rating"] = company_ratings[4].text

        try:
            job_record["trust_reviews_html"] = self._tab.find_element(
                By.XPATH,
                './/div[starts-with(@class,"JobDetails_reviewSection")]'
            ).get_attribute('innerHTML')
        except NoSuchElementException:
            logging.info(f'Failed to parse company trust reviews for {job_id}')

        try:
            job_record["benefit_rating"] = self._tab.find_element(
                By.XPATH,
                './/div[starts-with(@class,"CompanyBenefitReview_benefitRatingSection")]//div[@id="rating-headline"]'
            ).text
        except NoSuchElementException:
            logging.info(f'Failed to parse company benefit rating for {job_id}')


class NoDetailsTabException(Exception):
    pass


class JobTitleNotFoundException(Exception):
    def __init__(self, job_id):
        message = f'No element with id jd-job-title-{job_id} found. Cannot verify that the description page corresponds to job tab'
        super().__init__(message)


class ShowMoreUnexpectedState(Exception):
    def __init__(self, state):
        message = f'Show More button in unexpected state: {state}'
        super().__init__(message)
