import os
import re
import time

import pyperclip
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from seleniumbase import Driver
from seleniumbase.common.exceptions import NoSuchElementException

from helpers import handle_exception, wait_for_elements_presence, wait_for_elements_to_be_clickable
from settings import Settings
from utils import sign_in_with_google, get_all_downloaded_audios, send_telegram_message

SOUND_CLOUD_BASE_URL = "https://api.soundcloud.com/"


class SoundCloud:

    def __init__(self):
        self.driver = Driver(uc=True, headless2=Settings.HEADLESS, guest_mode=True, disable_gpu=True, no_sandbox=True,  incognito=True)
        self.result = {
            "account": "",
            "upload_count": 0,
            "monetization_count": 0
        }

    def login(self, link, username, password, retry=Settings.MAX_RETRY):
        """
        Log in to soundcloud account using Google credentials
        redirected
        :param link: A soundcloud redirect link with client_id, request_type data
        :param username: Account username
        :param password: Account password
        """
        if retry == 0:
            self.driver.close()
            return

        self.driver.uc_open(link)
        print("Logging in with google")
        self.result['account'] = username
        google_sign_option = wait_for_elements_presence(self.driver,
                                                        "div.provider-buttons > div > button.google-plus-signin.sc-button-google")[
            0]
        google_sign_option.click()
        print("Clicked on google sign in")
        while re.search(f"^{SOUND_CLOUD_BASE_URL}", self.driver.current_url):
            time.sleep(1)
        # Proceed to sign in with Google
        try:
            sign_in_with_google(self.driver, username, password)
        except Exception as e:
            print(e)
            return self.login(link, username, password, (retry - 1))

        secs_waited_for = 0
        # Wait for soundcloud redirection or if the Google account needs a code verification
        while not re.search(f"^{Settings.SOUND_CLOUD_ARTIST_BASE_URL}+overview", self.driver.current_url):
            if secs_waited_for < Settings.TIMEOUT:
                time.sleep(1)
                secs_waited_for += 1
            else:
                return self.login(link, username, password, (retry - 1))

        self.driver.sleep(2)
        print("Login success")

    @handle_exception(retry=True)
    def upload_tracks(self, downloaded_audios_info):
        """
        Upload downloaded tracks from suno_ai_spider run to the given to the artist profile
        """

        self.driver.get(Settings.SOUND_CLOUD_BASE_URL.replace("secure.", "") + "upload")

        print("Uploading tracks ...")
        # Accept cookies
        try:
            wait_for_elements_presence(self.driver, "#onetrust-accept-btn-handler")[0].click()
        except Exception:
            pass
        self.driver.click_if_visible(".loginButton", timeout=Settings.TIMEOUT)
        self.driver.sleep(5)
        # Select the choose file to upload btn
        selected_audios = get_all_downloaded_audios()
        # Click on not to create playlist
        try:
            wait_for_elements_presence(self.driver, "input.sc-checkbox-input.sc-visuallyhidden")
            self.driver.execute_script("document.querySelector('input.sc-checkbox-input.sc-visuallyhidden').click()")
        except Exception as e:
            pass
        self.driver.sleep(2)
        # Upload the audio files
        self.driver.find_element("input.chooseFiles__input.sc-visuallyhidden").send_keys("\n".join(selected_audios))
        time.sleep(Settings.TIMEOUT)
        genre_name = downloaded_audios_info[0]['genre']

        self.driver.sleep(1)
        # Wait for all audio to upload
        upload_status = self.driver.get_text("span.uploadButton__title")
        while "processing" in upload_status.lower() or "uploading" in upload_status.lower():
            self.driver.sleep(1)
            upload_status = self.driver.get_text("span.uploadButton__title")

        all_uploads_titles = wait_for_elements_presence(self.driver,
                                                        'div.baseFields__data > div.baseFields__title > div.textfield > div.textfield__inputWrapper > input')
        all_uploads_img = wait_for_elements_presence(self.driver, 'input.imageChooser__fileInput.sc-visuallyhidden')
        all_uploads_tags = wait_for_elements_presence(self.driver, 'input.tagInput__input.tokenInput__input')
        all_uploaded_song_save_btn_ele = wait_for_elements_presence(self.driver,
                                                                    "div.activeUpload__formButtons.sc-button-toolbar > button.sc-button-cta.sc-button")
        print(f"Got {len(all_uploaded_song_save_btn_ele)} save btns")
        for each in all_uploads_titles:
            for audio_info in downloaded_audios_info:
                if each.get_attribute("value").lower() == audio_info["title"].lower():
                    print("Seen an upload")
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
                    self.driver.sleep(2)
                    break
        self.driver.execute_script(open("soundcloud_uploads/upload.js").read(), genre_name)
        self.result['upload_count'] = len(all_uploads_img)
        self.driver.sleep(2)

    def monetize_track(self):
        """
            Monetize all the monetized tracks on the account. Paginates to the next page if need be
        """

        print("Monetizing Tracks ....")
        not_allowed_text = self.driver.get_text("#right-before-content > div", timeout=Settings.TIMEOUT)
        if not_allowed_text == "You don't have access to this page.":
            return False

        self.driver.sleep(2)
        all_monetize_track_btns = wait_for_elements_to_be_clickable(self.driver,
                                                                    "#right-before-content > div.my-3 > div > div > div:nth-child(2) > div > button")
        for btn_ele in all_monetize_track_btns:
            if btn_ele.text == "Monetize this track":
                btn_ele.click()
                wait_for_elements_presence(self.driver, "#monetization-form")
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

                self.driver.execute_script(fill_form_js_script)
                self.driver.sleep(3)
        #  Adds the no of tracks monetized from a page to the result attribute
        self.result["monetization_count"] += len(all_monetize_track_btns)
        pagination_btn = wait_for_elements_to_be_clickable(self.driver,
                                                           "#right-before-content > div.w-full.h-full.flex.items-center.justify-center.gap-x-2 > button:nth-child(2)")
        for each in pagination_btn:
            if each.text == "Next":
                print("Navigating to monetization next page")
                each.click()
                self.monetize_track()
                break
        print(f"{len(all_monetize_track_btns)} tracks has been monetized")
        return

    @handle_exception()
    def sync_soundcloud_tracks(self):
        """
        Navigates to soundcloud monetization and clicks on synchronize with soundcloud btn then wait for a minute
        :return:
        """
        print("Synchronizing ...")
        self.driver.get(Settings.SOUND_CLOUD_ARTIST_BASE_URL + "monetization")
        try:
            self.driver.execute_script('document.querySelector("#right-before-content > div > div > button").click()')
            print("Waiting for a minute for soundcloud synchronization")
            self.driver.sleep(60)
            return True
        except Exception:
            return False


def run_soundcloud_bot(link, username, password, store, soundcloud_result: list):
    """
    Run the soundcloud action bot
    :param link: Authentication link from soundcloud
    :param username:  registered username
    :param password: Soundcloud password
    :param store: List of all downloaded tracks from suno AI bot
    :param soundcloud_result: List to store the result of the soundcloud bot run
    """
    try:
        soundcloud_bot = SoundCloud()
        soundcloud_bot.login(link, username, password)
        soundcloud_bot.upload_tracks(store)
        if soundcloud_bot.sync_soundcloud_tracks():
            soundcloud_bot.driver.get(Settings.SOUND_CLOUD_ARTIST_BASE_URL + "monetization")
            soundcloud_bot.monetize_track()
        soundcloud_result.append(soundcloud_bot.result)
        soundcloud_bot.driver.close()
    except Exception as e:
        print("Exception from Soundcloud")
        print(e)
        pass
