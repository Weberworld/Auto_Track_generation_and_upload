import logging
import time

from settings import Settings
from selenium.common import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(filename="stderr.log", format="%(asctime)s  --  %(levelname)s -- %(message)s")
logger = logging.getLogger()

logger.setLevel(logging.INFO)


MAX_RETRIES = 5


def retry_func(func, no_of_retries, *args, **kwargs):
    if no_of_retries > 0:
        return
    else:
        # Call the func and return if the function runs without any fails
        if func(*args, **kwargs):
            return
        else:
            # Recursively retry the func for the no_of_retries if any fail on initial call
            return retry_func(func, (no_of_retries - 1), *args, **kwargs)


def handle_exception(retry=False):
    """
    Event handler that handles common web exceptions e.g (Timeout, NoSuchElementFound)
    :param retry: flag, if you need to retry the function after it encountered a particular error
    """
    def wrapper(func):
        def inner_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                print(e)
                logger.info("Handled Unknown Exception")

                if retry:
                    print("Retrying function")
                    logger.log(logging.WARNING, "Retrying du")
                    return func(*args, **kwargs)
            finally:
                pass
        return inner_func
    return wrapper


def wait_for_elements_presence(driver, selector: str) -> list:
    """

    :param driver: an active chrom webdriver
    :param selector: CSS locator of an element
    :return: The list of elements it waited for, if the function did not enter timeout
    """
    try:
        WebDriverWait(driver, Settings.TIMEOUT).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, selector)))
        return driver.find_elements(By.CSS_SELECTOR, selector)
    except TimeoutException:
        try:
            WebDriverWait(driver, Settings.TIMEOUT).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
            return driver.find_elements(By.CSS_SELECTOR, selector)
        except TimeoutException:
            raise TimeoutException


def wait_for_elements_to_be_clickable(driver, selector: str) -> list:
    """
    Returns a list of selector elements when they are clickable within a timeout range

    Try to get the element twice if they are not clickable yet
    :param driver: Current webdriver
    :param selector: CSS locator of an element
    :return:
    """

    try:
        WebDriverWait(driver, Settings.TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        return driver.find_elements(By.CSS_SELECTOR, selector)

    except TimeoutException:
        try:
            WebDriverWait(driver, Settings.TIMEOUT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            return driver.find_elements(By.CSS_SELECTOR, selector)
        except TimeoutException:
            return []
