import logging
import time
#import undetected_chromedriver as webdriver
import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, \
    ElementClickInterceptedException, ElementNotInteractableException

from GlassdoorJobPage import GlassdoorJobPage
from SiteTools import SiteTools


class GlassdoorSite(SiteTools):
    def __init__(self, driver: webdriver.Remote, domain: str, query: str):
        super().__init__(driver)
        self._open_site(domain, query)

    def _open_site(self, domain: str, query: str) -> None:
        search_url = f"https://{domain}/Job/{query}?sortBy=date_desc"
        self._driver.get(search_url)

    def parse_all_jobs(self, n_pages: int = 0) -> list[GlassdoorJobPage]:
        self._close_popup()
        self._close_cookies_popup()
        page_index = 1
        while self._load_more():
            print('.', end='')
            if n_pages and page_index >= n_pages:
                break
            page_index += 1

        self._close_cookies_popup()

        all_jobs = self._driver.find_elements(By.CSS_SELECTOR, '[data-test="job-card-wrapper"]')
        return [GlassdoorJobPage(self._driver, job) for job in all_jobs]

    def _close_cookies_popup(self) -> None:
        try:
            cookies_btn = self._driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookies_btn.click()
        except NoSuchElementException:
            pass
        except ElementNotInteractableException:
            pass

    def _load_more(self) -> bool:
        all_matches_button = None
        attempts = 0
        while not all_matches_button and attempts <= 5:
            time.sleep(1)
            self._close_popup()
            self._close_cookies_popup()
            try:
                all_matches_button = self._driver.find_element(By.CSS_SELECTOR, '[data-test="load-more"]')
                if all_matches_button and all_matches_button.get_attribute('data-loading') != 'true':
                    all_matches_button.click()
                    return True
            except NoSuchElementException:
                break
            except StaleElementReferenceException:
                logging.debug('all_matches_button stale, try more')
            except ElementNotInteractableException:
                logging.warning('all_matches_button not interactable, try more')
            except ElementClickInterceptedException:
                self._close_cookies_popup()
            all_matches_button = None
            attempts += 1

        return False
