import time
#import undetected_chromedriver as webdriver
import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, \
    ElementClickInterceptedException, ElementNotInteractableException

from GlassdoorJobPage import GlassdoorJobPage


class GlassdoorSite:
    def __init__(self, driver: webdriver.Remote, domain: str):
        self.__driver = driver
        self.__open_site(domain)

    def __open_site(self, domain: str) -> None:
        search_url = f"https://{domain}/Job/data-engineer-jobs-SRCH_KO0,13.htm?sortBy=date_desc"
        self.__driver.get(search_url)

    def parse_all_jobs(self, n_pages: int = 0) -> list[GlassdoorJobPage]:
        self.__close_login_popup()
        self.__close_cookies_popup()
        page_index = 1
        while self.__load_more():
            print('.', end='')
            if n_pages and page_index >= n_pages:
                break
            page_index += 1

        all_jobs = self.__driver.find_elements(By.CSS_SELECTOR, '[data-test="job-card-wrapper"]')
        return [GlassdoorJobPage(self.__driver, job) for job in all_jobs]

    def __close_login_popup(self) -> None:
        try:
            # Check for login popup, if present then click CloseButton
            close_login_popup = self.__driver.find_element(By.CLASS_NAME, "CloseButton")
            close_login_popup.click()
        except NoSuchElementException:
            pass

    def __close_cookies_popup(self) -> None:
        try:
            cookies_btn = self.__driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookies_btn.click()
        except NoSuchElementException:
            pass
        except ElementNotInteractableException:
            pass

    def __load_more(self) -> bool:
        all_matches_button = None
        attempts = 0
        while not all_matches_button and attempts <= 5:
            time.sleep(1)
            self.__close_login_popup()
            self.__close_cookies_popup()
            try:
                all_matches_button = self.__driver.find_element(By.CSS_SELECTOR, '[data-test="load-more"]')
                if all_matches_button and all_matches_button.get_attribute('data-loading') != 'true':
                    all_matches_button.click()
                    return True
            except NoSuchElementException:
                break
            except StaleElementReferenceException:
                pass
            except ElementClickInterceptedException:
                self.__close_cookies_popup()
            all_matches_button = None
            attempts += 1

        return False
