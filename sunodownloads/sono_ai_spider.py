import re

from selenium.common import JavascriptException
from seleniumbase.common.exceptions import TimeoutException

from utils import sign_in_with_microsoft, download_image, rename_downloaded_audio_file, scroll_down, \
    rename_track_with_version_number
from settings import Settings
from helpers import wait_for_elements_presence, handle_exception, wait_for_elements_to_be_clickable


class SunoAI:
    def __init__(self, driver):
        """
        :param driver: Seleniumbase driver object
        """
        self.driver = driver
        self.driver.set_window_size(1920, 1080)

    # Login into suno
    def sign_in(self, username, password, max_retry=Settings.MAX_RETRY):
        """
        Opens the sign-in page on suno and sign in to an account using a Microsoft account credential
        :param username: Account username
        :param password: Account password
        :param max_retry:
        """
        print(f"Starting Suno process for {username}")
        if max_retry <= 0:
            self.driver.close()
            return
        try:
            self.driver.get(Settings.SUNO_BASE_URL + "sign-in")
            # Click on sign in with Microsoft
            wait_for_elements_to_be_clickable(self.driver,
                                              "button.cl-socialButtonsIconButton.cl-socialButtonsIconButton__microsoft")[
                0].click()
            sign_in_with_microsoft(self.driver, username, password)
            secs_waited_for = 0
            while not re.search(f"^{Settings.SUNO_BASE_URL}", self.driver.current_url):
                if secs_waited_for < Settings.TIMEOUT:
                    self.driver.sleep(1)
                secs_waited_for += 1
            print("Login Success")
        except Exception:
            print(f"Unable to login {username}. Retrying ...")
            return self.sign_in(username, password, (max_retry - 1))

    def sign_out(self):
        """
        Sign out from a logged in suno account
        """
        # Click on the menu option button
        wait_for_elements_to_be_clickable(self.driver, "button.cl-userButtonTrigger")[0].click()
        # Click sign out button
        wait_for_elements_to_be_clickable(self.driver, "button.cl-userButtonPopoverActionButton__signOut")[0].click()
        self.driver.sleep(3)

    def create_song(self, prompt):
        """
        Create a music on suno.ai using the given prompt as the track description
        :param prompt: Prompt to use to generate track lyrics
        """
        print("Creating tracks ....")

        prompt_input_ele = "div.chakra-stack.css-131jemj > div.chakra-stack.css-10k728o > textarea"
        wait_for_elements_to_be_clickable(self.driver, prompt_input_ele)[0].clear()
        self.driver.type(prompt_input_ele, prompt, timeout=Settings.TIMEOUT)
        self.driver.click("div.chakra-stack.css-10k728o > div > button.chakra-button")

    @handle_exception(retry=True)
    def get_generated_tracks_selection(self) -> list:
        """
        Get the option btns of the newly created tracks.
       """
        select_btns = wait_for_elements_presence(
            self.driver,
            "button.chakra-button.chakra-menu__menu-button.css-o244em")[-Settings.NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES::]
        return select_btns

    def wait_for_new_track(self):
        self.driver.sleep(2)
        secs_waited_for = 0
        while self.driver.execute_script(
                "return (document.querySelector('.chakra-spinner.css-12wh8ho'))") and secs_waited_for <= Settings.TIMEOUT:
            self.driver.sleep(1)
            secs_waited_for += 1

    def wait_for_new_track_to_be_ready(self):
        """
        Wait for a set number of minutes until the track is ready for download
        """
        print(
            f"Waiting for track to be ready for download within {Settings.MAX_TIME_FOR_SUNO_GENERATION / 60} minutes ....")
        scroll_down(self.driver)
        max_wait_limit_in_secs = 0
        while max_wait_limit_in_secs < Settings.MAX_TIME_FOR_SUNO_GENERATION:
            if self.driver.execute_script(
                    "return (document.querySelector('div.css-yle5y0 > div > div > div > div > div > div > div > button.chakra-menu__menuitem > div.chakra-spinner'))"):
                self.driver.sleep(1)
                max_wait_limit_in_secs += 1
            else:
                break
        else:
            return False

        try:
            download_btns = wait_for_elements_to_be_clickable(self.driver,
                                                              "div.css-yle5y0 > div > div > div > div > div > div > div > button.chakra-menu__menuitem")
            # Check if the list is not empty
            if download_btns and download_btns[3].is_enabled():
                self.driver.execute_script("arguments[0].scrollIntoView();", download_btns[3])
            return True
        except TimeoutException:
            print(f"Track was not ready for download after {Settings.MAX_TIME_FOR_SUNO_GENERATION / 60} minutes")
            return False

    def download_track(self, username, track_title, tags, genre):
        print("Downloading Track ...")
        self.driver.execute_script(
            "document.querySelectorAll('div.css-yle5y0 > div > div > div > div > div > div > div > button.chakra-menu__menuitem')[3].click()")

        # Get the img download link
        try:
            img_src = self.driver.execute_script(
                "return (document.querySelector('div.css-rdnx5m > img').getAttribute('src'))")
            img_path = download_image(img_src, track_title)
        except JavascriptException:
            print("Unable to extract image. suno could not generate an image for the track")
            img_path = ""

        # Format tag list
        tag_str = tags.text.split(" ")
        # Store the track info
        track_details = {
            "account": username,
            "title": track_title,
            "genre": genre,
            "tag_list": tag_str,
            "img_path": img_path
        }
        print(track_details)
        return track_details

    @handle_exception()
    def scrap_details(self) -> tuple:
        """
        Scraps the webpage for track titles and genre names
        """
        all_titles = wait_for_elements_presence(self.driver, "p.chakra-text.css-1fq6tx5")[
                     -Settings.NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES::]
        all_genre_list = wait_for_elements_presence(self.driver, "p.chakra-text.css-1icp0bk")[
                         -Settings.NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES::]
        return all_titles, all_genre_list

    def run(self, account_username, all_prompt_info, store_into):
        """
        Use a list of prompts to generate track and suno and store the details (title, genre, tag_list) of the downloaded track
        to the store_into list variable.
        :param account_username: Logged in suno account username
        :param all_prompt_info: list of prompts to use to generate track on suno
        :param store_into: List to store the details of the downloaded track
        """
        print("Opening the create track page ...")
        self.driver.get(Settings.SUNO_BASE_URL + "create")
        for prompt in all_prompt_info:
            no_of_credit = self.driver.get_text(".chakra-text.css-itvw0n", timeout=Settings.TIMEOUT).split(" ")[0]
            if int(no_of_credit) < 10:
                print("Not enough credits")
                self.driver.quit()
                return

            # Create tracks with a given prompt
            self.create_song(prompt["prompt"])
            self.wait_for_new_track()
            generated_tracks_sel_btn = self.get_generated_tracks_selection()
            index = 0
            for btn_ele in generated_tracks_sel_btn:
                self.driver.execute_script("arguments[0].click()", btn_ele)

                if not self.wait_for_new_track_to_be_ready():
                    generated_tracks_sel_btn[index].click()
                    continue
                scraped_details = self.scrap_details()

                track_title: str = scraped_details[0][index].text
                # Check if the title exists in the formally downloaded track titles
                for each in store_into:
                    if each['title'] in track_title:
                        # Add extra text to the duplicated track title
                        new_track_title = rename_track_with_version_number(track_title)
                        rename_downloaded_audio_file(track_title, (new_track_title + ".mp3"))
                        track_title = new_track_title
                track_tags = scraped_details[1][index]
                genre = prompt["genre"]
                downloaded_track = self.download_track(account_username, track_title, track_tags, genre)

                index += 1
                if downloaded_track:
                    store_into.append(downloaded_track)
                self.driver.sleep(1)
            self.driver.refresh()

        self.driver.sleep(4)


def run_suno_bot(driver, username, password, prompt, store):
    """
    Runs the Suno Ai bot
    :param driver: Seleniumbase webdriver
    :param username: Microsoft username
    :param password: Microsoft password
    :param prompt: List of prompts to use to create tracks on Suno AI
    :param store: List to store all downloaded tracks info
    """

    suno_bot = SunoAI(driver)

    suno_bot.sign_in(username, password)
    suno_bot.run(username, prompt, store)
    if Settings.LOCAL_TESTING:
        suno_bot.driver.quit()
    else:
        suno_bot.sign_out()
        suno_bot.driver.delete_all_cookies()
