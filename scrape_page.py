import sys

import selenium.webdriver as webdriver

from GlassdoorJobPage import JobDetails


def create_webdriver():
    options = webdriver.ChromeOptions()
    return webdriver.Chrome(options=options)


def main() -> int:
    #job_id = 1009570843218
    #job_id = 1009585472556
    #job_id = 1009585527457
    job_id = 1009585492999
    url = f'https://www.glassdoor.ie/job-listing/index.htm?jl={job_id}'
    driver = create_webdriver()
    driver.get(url)
    #time.sleep(5)

    job_record = {}
    parser = JobDetails(driver, job_id)
    parser.parse_details(job_record)
    print(job_record)
    return 0


if __name__ == '__main__':
    sys.exit(main())
