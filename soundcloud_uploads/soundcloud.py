import re
import time
import pyperclip
from selenium.common import ElementClickInterceptedException, JavascriptException

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase.common.exceptions import TimeoutException, NoSuchWindowException, NoSuchElementException

from helpers import handle_exception, wait_for_elements_presence, wait_for_elements_to_be_clickable
from settings import Settings
from utils import sign_in_with_google, get_all_downloaded_audios, scroll_down

SOUND_CLOUD_BASE_URL = "https://api.soundcloud.com/"


class SoundCloud:

    def __init__(self, driver):
        self.driver = driver
        self.result = {
            "account": "",
            "upload_count": 0,
            "monetization_count": 0
        }
        self.driver.set_window_size(1920, 1080)

    def login(self, link, username, password, retry=Settings.MAX_RETRY):
        """
        Log in to soundcloud account using Google credentials
        redirected
        :param link: A soundcloud redirect link with client_id, request_type data
        :param username: Account username
        :param password: Account password
        :param retry:
        """
        print(f"Logging in to Soundcloud with: {username}")
        if retry == 0:
            print(f"Retrying countdown {retry}")
            self.driver.quit()
            return False

        self.driver.uc_open(link)
        self.result['account'] = username

        google_sign_option = wait_for_elements_presence(self.driver,
                                                        "div.provider-buttons > div > button.google-plus-signin.sc-button-google")[
            0]
        google_sign_option.click()
        while re.search(f"^{SOUND_CLOUD_BASE_URL}", self.driver.current_url):
            time.sleep(1)

        # Proceed to sign in with Google
        try:
            sign_in_with_google(self.driver, username, password)
        except Exception as e:
            print(e)
            return self.login(link, username, password, (retry - 1))

        secs_waited_for = 0
        print("processing login ...")
        # Wait for soundcloud redirection or if the Google account needs a code verification
        while not re.search(f"^{Settings.SOUND_CLOUD_ARTIST_BASE_URL}+overview", self.driver.current_url):
            if secs_waited_for > Settings.TIMEOUT:
                print("retry login")
                return self.login(link, username, password, (retry - 1))
            time.sleep(1)
            secs_waited_for += 1

        self.driver.sleep(2)
        print("Login success")

        # Accept cookies
        try:
            self.driver.click_if_visible("#onetrust-accept-btn-handler", timeout=Settings.TIMEOUT)
            print("Accepted cookies")
        except ElementClickInterceptedException:
            # Handle the case where the button is intercepted
            print("Button is intercepted by another element")
            # Use JavaScript to click on the button
            button = self.driver.execute_script(
                "return document.getElementById('onetrust-accept-btn-handler');")
            self.driver.execute_script("arguments[0].click();", button)

        except TimeoutException:
            print("Cannot find cookies")
            pass
        return True

    def log_out(self):
        """
        Logs out from a logged in soundcloud account
        """
        # Clicks on the menu option
        wait_for_elements_to_be_clickable(self.driver, "#headlessui-menu-button-6")[0].click()
        # Click on the sign-out button
        wait_for_elements_to_be_clickable(self.driver, "#headlessui-menu-item-11")[0].click()
        # Wait for timeout until the log-out is completed
        sec_waited_for = 0
        while self.driver.current_url == Settings.SOUND_CLOUD_ARTIST_BASE_URL and sec_waited_for < Settings.TIMEOUT:
            time.sleep(1)

    @handle_exception(retry=True)
    def upload_tracks(self, downloaded_audios_info: list):
        """
        Upload downloaded tracks from suno_ai_spider run to the given to the artist profile
        """
        print(downloaded_audios_info)
        if not downloaded_audios_info:
            print("No tracks to upload.")
            return

        self.driver.uc_open(Settings.SOUND_CLOUD_BASE_URL.replace("secure.", "") + "upload")

        # Dismiss if any pop up window shows up
        self.driver.sleep(2)
        self.driver.press_keys("button", Keys.ESCAPE)

        # Select the choose file to upload btn
        selected_audios = get_all_downloaded_audios()

        # Click on not to create playlist
        self.driver.execute_script('document.querySelector("input.sc-checkbox-input.sc-visuallyhidden").click()')
        self.driver.sleep(2)

        # Upload the audio files
        print("Uploading files")

        wait_for_elements_to_be_clickable(self.driver, "input.chooseFiles__input.sc-visuallyhidden")[0].send_keys(
            "\n".join(selected_audios))
        genre_name = downloaded_audios_info[0]['genre']
        print(f"Genre name is: {genre_name}")
        self.driver.sleep(1)

        # Wait for all audio to upload
        print("Processing Uploads ... ")
        upload_status = self.driver.get_text("span.uploadButton__title", timeout=Settings.TIMEOUT)
        while "processing" in upload_status.lower() or "uploading" in upload_status.lower():
            self.driver.sleep(1)
            upload_status = self.driver.get_text("span.uploadButton__title")
        print("Upload processing done")

        all_uploads_titles = wait_for_elements_presence(self.driver,
                                                        'div.baseFields__data > div.baseFields__title > div.textfield > div.textfield__inputWrapper > input')
        all_uploads_img = wait_for_elements_presence(self.driver, 'input.imageChooser__fileInput.sc-visuallyhidden')
        all_uploads_tags = wait_for_elements_presence(self.driver, 'input.tagInput__input.tokenInput__input')

        print("Filling Tracks upload form ...")
        for each in all_uploads_titles:
            for audio_info in downloaded_audios_info:
                if each.get_attribute("value").lower() == audio_info["title"].lower():
                    track_index = all_uploads_titles.index(each)
                    # Upload the track image
                    all_uploads_img[track_index].send_keys(audio_info["img_path"])
                    # Set the additional tracks tags
                    # Convert the tag list to a string separated by spaces
                    tag_list_str = " ".join(audio_info["tag_list"])
                    # Copy the tag list string to the clipboard
                    pyperclip.copy(tag_list_str)
                    # Paste the tag list string from the clipboard
                    all_uploads_tags[track_index].send_keys(Keys.CONTROL, 'v')
                    self.driver.sleep(1)
                    break
        self.driver.execute_script(open("soundcloud_uploads/upload.js").read(), genre_name)
        print(f"{len(all_uploads_titles)} tracks has been uploaded")
        self.result['upload_count'] = len(all_uploads_img)
        self.driver.sleep(5)

    def fill_monetization_form(self, btn_ele, no_of_retry=3):
        """ Fills the monetization form for a track and retry for the no_of_retry if a javascript error is raised"""
        self.driver.execute_script("arguments[0].click()", btn_ele)
        wait_for_elements_presence(self.driver, "#monetization-form")
        self.driver.sleep(1)
        fill_form_js_script = """
            let form_ele = document.getElementById("monetization-form");

            // Click on the content rating 
            form_ele.querySelector("div > div:nth-child(1) > div > label > div.mt-1 > div > div > button").click(); 

            // Get the content rating select list
            let content_rating_select_list_ele = form_ele.querySelector("div > div:nth-child(1) > div > label > div.mt-1 > div > ul");
            let rating_options = content_rating_select_list_ele.getElementsByTagName("li");

            // Loop through the rating options and select the Explicit option
            for (let i = 0; i < rating_options.length; i++) {
                if (rating_options[i].textContent == "Explicit") {
                    rating_options[i].click();
                    break;
                }
            }
            // In the songwriter options select "Another writer"
            form_ele.querySelector("div.mb-3 > div > div:nth-child(1) > div.flex > label > div.mt-1 > label:nth-child(2) > div > input").click();

            // Mark that you agree to the T/C
            form_ele.querySelector("div:nth-child(15) > div input").click()

            // Submit the form_ele
            form_ele.querySelector("div:nth-child(16) > button:nth-child(2)").click();

            // Click on the cancel btn
            form_ele.querySelector("div:nth-child(16) > button").click();
        """
        try:
            self.driver.execute_script(fill_form_js_script)
        except JavascriptException:
            # If this exception is raised. Re-run the function and execute the script again
            self.driver.execute_script("arguments[0].click()", btn_ele)
            if not no_of_retry <= 0:
                self.fill_monetization_form(btn_ele, (no_of_retry - 1))
            else:
                print("Retry exceeded")
        except NoSuchElementException:
            pass
        except Exception as e:
            print(e)

    def monetize_track(self, max_num_of_pages=3):
        """
            Monetize all the monetized tracks on the account. Paginates to the next page if need be
        """

        print("Monetizing Tracks ....")
        #  Check if the account is allowed for monetization
        try:
            not_allowed_text = self.driver.get_text("#right-before-content > div", timeout=Settings.TIMEOUT)
            if not_allowed_text == "You don't have access to this page.":
                return False
        except TimeoutException:
            pass

        self.driver.sleep(2)

        # Get the monetization btn elements
        try:
            WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Monetize this track')]")))
            all_monetize_track_btns = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Monetize this track')]")
        except TimeoutException:
            try:
                self.driver.refresh()
                WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Monetize this track')]")))
                all_monetize_track_btns = self.driver.find_elements(
                    By.XPATH, "//button[contains(text(), 'Monetize this track')]")
            except TimeoutException:
                print("No song to monetize!")
                all_monetize_track_btns = []

        print(f"Found {len(all_monetize_track_btns)} tracks to monetize")
        for btn_ele in all_monetize_track_btns:
            if btn_ele.text == "Monetize this track":
                self.fill_monetization_form(btn_ele)
                self.driver.sleep(2)
        #  Adds the no of tracks monetized from a page to the result attribute
        self.result["monetization_count"] += len(all_monetize_track_btns)
        scroll_down(self.driver)
        # Paginates to the next page if not more than the max_num_of_pages
        try:
            pagination_btn = self.driver.execute_script('return (document.querySelector("#right-before-content > div.w-full.h-full.flex.items-center.justify-center.gap-x-2 > button:nth-child(2)"))')
            if max_num_of_pages > 0:
                if pagination_btn.textContent == "Next" and not pagination_btn.disabled:
                    print("Navigating to monetization next page")
                    pagination_btn.click()
                    self.driver.sleep(3)
                    self.monetize_track((max_num_of_pages - 1))
        except JavascriptException:
            pass
        print(f"{len(all_monetize_track_btns)} tracks has been monetized")

    @handle_exception()
    def sync_soundcloud_tracks(self):
        """
        Navigates to soundcloud monetization and clicks on synchronize with soundcloud btn then wait for a minute
        :return:
        """
        print("Synchronizing ...")
        self.driver.get(Settings.SOUND_CLOUD_ARTIST_BASE_URL + "monetization")
        try:
            self.driver.click_if_visible("#right-before-content > div > div > button", timeout=Settings.TIMEOUT)
            print(f"Waiting for {300 / 60} minute(s) for soundcloud synchronization")
            self.driver.sleep(300)
            return True
        except (TimeoutException, IndexError):
            return False


def run_soundcloud_bot(driver, link, username, password, store, soundcloud_result: list):
    """
    Run the soundcloud action bot
    :@param driver: Seleniumbase webdriver object
    :param link: Authentication link from soundcloud
    :param username:  registered username
    :param password: Soundcloud password
    :param store: List of all downloaded tracks from suno AI bot
    :param soundcloud_result: List to store the result of the soundcloud bot run
    """
    try:

        soundcloud_bot = SoundCloud(driver)
    except NoSuchWindowException:
        soundcloud_bot = SoundCloud(driver)
    if not soundcloud_bot.login(link, username, password):
        return
    soundcloud_bot.upload_tracks(store)
    if soundcloud_bot.sync_soundcloud_tracks():
        soundcloud_bot.driver.get(Settings.SOUND_CLOUD_ARTIST_BASE_URL + "monetization")
        soundcloud_bot.monetize_track()
    soundcloud_result.append(soundcloud_bot.result)
    if Settings.LOCAL_TESTING:
        driver.quit()
    return
