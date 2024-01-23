import logging

from settings import Settings
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(filename="stderr.log", format="%(asctime)s  --  %(levelname)s -- %(message)s")
logger = logging.getLogger()

logger.setLevel(logging.INFO)


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
                logger.info(e)

                if retry:
                    print("Retrying function")
                    logger.log(logging.WARNING, f"Retrying function {func.__name__}")
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
            return []


def wait_for_elements_to_be_clickable(driver, selector: str, timeout=Settings.TIMEOUT) -> list:
    """
    Returns a list of selector elements when they are clickable within a timeout range

    Try to get the element twice if they are not clickable yet
    :param driver: Current webdriver
    :param selector: CSS locator of an element
    :param timeout: No of secs to wait until element is clickable. Defaults to settings timeout
    :return:
    """

    try:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        return driver.find_elements(By.CSS_SELECTOR, selector)

    except TimeoutException:
        try:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            return driver.find_elements(By.CSS_SELECTOR, selector)
        except TimeoutException:
            return []


def create_driver():
    """
    Creates a webdriver
    @return:  object
    """
    from seleniumbase import Driver as webDriver

    driver = webDriver(
        uc=True, undetectable=True, headless2=Settings.HEADLESS, guest_mode=True, disable_gpu=True,
        no_sandbox=True, incognito=True, user_data_dir=None
    )
    return driver