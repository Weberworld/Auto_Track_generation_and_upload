import re
from selenium.common import StaleElementReferenceException
from utils import sign_in_with_microsoft, download_image, rename_downloaded_audio_file
from settings import Settings
from seleniumbase import Driver
from helpers import wait_for_elements_presence, handle_exception, wait_for_elements_to_be_clickable


class SunoAI:
    def __init__(self):

        self.driver = Driver(uc=True, headless=Settings.HEADLESS, disable_gpu=True, no_sandbox=True)
        self.driver.set_window_size(1200, 800)

    # Login into suno
    def sign_in(self, username, password, max_retry=5):
        """
        Opens the sign-in page on suno and sign in to an account using a Microsoft account credential
        :param max_retry:
        :param username: Account username
        :param password: Account password
        :return:
        """
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

    def create_song(self, prompt):
        """
        Create a music on suno.ai using the given prompt as the track description
        :param prompt: Prompt to use to generate track lyrics
        """
        print("Creating tracks ....")
        self.driver.get(Settings.SUNO_BASE_URL + "create")
        prompt_input_ele = "div.chakra-stack.css-131jemj > div.chakra-stack.css-10k728o > textarea"
        wait_for_elements_presence(self.driver, prompt_input_ele)#[0].send_keys(prompt)
        # self.driver.click("div.chakra-stack.css-10k728o > div > button.chakra-button")

    @handle_exception(retry=True)
    def get_generated_tracks_selection(self, no_of_tracks) -> list:
        self.driver.sleep(3)
        select_btns = wait_for_elements_presence(self.driver,
                                                 "button.chakra-button.chakra-menu__menu-button.css-o244em")[
                      -no_of_tracks::]
        return select_btns

    def select_an_option_from_a_track(self, option_sel_btn_ele, option: int, download=False):
        """
        Selects an option from the track selection list
        :param option_sel_btn_ele:
        :param download: boolean
        :param option: index of the option to select
        :return:
        """
        try:
            option_sel_btn_ele.click()
            self.driver.sleep(2)
            if download:
                loading = True
                while loading:
                    if self.driver.execute_script(
                            "return (document.querySelector('div.css-yle5y0 > div > div > div > div > div > div > div > button.chakra-menu__menuitem > div.chakra-spinner'))"):
                        self.driver.sleep(1)
                    else:
                        loading = False
                wait_for_elements_to_be_clickable(self.driver,
                                                  "div.css-yle5y0 > div > div > div > div > div > div > div > button.chakra-menu__menuitem")[
                    option].click()
                return
        except Exception:
            self.driver.refresh()
            wait_for_elements_presence(self.driver, "button.chakra-button.chakra-menu__menu-button.css-o244em")
            self.select_an_option_from_a_track(option_sel_btn_ele, option, download)

    @handle_exception(retry=True)
    def download_track(self, track_opt_btn_ele):
        """
        Downloads a track
        :param track_opt_btn_ele: Track options selection element
        """
        print("Downloading track ....")
        self.select_an_option_from_a_track(track_opt_btn_ele, option=3, download=True)

    def scrap_details(self) -> tuple:
        """
        Scraps the webpage for track titles and genre names
        :return:
        """
        all_titles = wait_for_elements_presence(self.driver, "p.chakra-text.css-1fq6tx5")[
                     -Settings.NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES::]
        all_genre_list = wait_for_elements_presence(self.driver, "p.chakra-text.css-1icp0bk")[
                         -Settings.NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES::]
        return all_titles, all_genre_list

    def run(self, account_username, prompt_info, store_into):
        """
        Use a prompt to generate track and suno and store the details (title, genre, tag_list) of the downloaded track
        to the store_into list variable.
        :param account_username: Logged in suno account username
        :param prompt_info: prompt to use to generate track on suno
        :param store_into: List to store the details of the downloaded track
        """

        # Create tracks with a given prompt
        self.create_song(prompt_info['prompt'])

        # Download the generated tracks
        generated_tracks_sel_btn = self.get_generated_tracks_selection(Settings.NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES)

        index = 0
        for track_sel_btn in generated_tracks_sel_btn:
            self.download_track(track_sel_btn)
            # Scrap the tracks title and tag list
            scraped_details = self.scrap_details()
            # Get the img download link
            img_src = self.driver.execute_script(
                "return (document.querySelector('div.css-rdnx5m > img').getAttribute('src'))")
            track_title: str = scraped_details[0][index].text
            # Check if the title exists in the formally downloaded track titles
            for each in store_into:
                if each['title'] in track_title:
                    new_track_title = (track_title[0:-3] + " remix")
                    rename_downloaded_audio_file(track_title, new_track_title)
                    track_title = new_track_title

            # Download the track image
            img_path = download_image(img_src, track_title)
            # Format tag list
            tag_str = scraped_details[1][index].text.split(" ")
            # Store the track info
            track_details = {
                "account": account_username,
                "title": scraped_details[0][index].text,
                "genre": prompt_info['genre'],
                "tag_list": tag_str,
                "img_path": img_path
            }
            print(track_details)
            index += 1
            store_into.append(track_details)
            self.driver.sleep(2)
        self.driver.sleep(5)


def run_suno_bot(username, password, prompt, store):
    try:
        suno_bot = SunoAI()
        suno_bot.sign_in(username, password)
        suno_bot.run(username, prompt, store)
        suno_bot.driver.close()
    except Exception as e:
        print("Got exception from suno")
        print(e)
        pass
