import logging

import selenium.webdriver as webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


class SiteTools:
    def __init__(self, driver: webdriver.Chrome):
        self._driver = driver

    def _close_popup(self) -> bool:
        try:
            close_popup = self._driver.find_element(By.CLASS_NAME, "CloseButton")
            close_popup.click()
            logging.debug(f"Popup closed")
            return True
        except NoSuchElementException:
            logging.debug(f"Popup not found")
            return False
