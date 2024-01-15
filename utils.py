import os
import re
import time
from datetime import datetime
import requests
from settings import Settings


def parse_prompts() -> dict:
    """
        Go through the suno_ao_music_genre_prompt txt file and get the genres names and prompts.
        Organize the data such that the genre name becomes the key and the value is the list of prompts for the
        genre name
    """
    file = None
    try:
        file = open("suno_prompts_v2.txt")
    except FileNotFoundError:
        file = open("suno_prompts.txt")
    finally:
        try:
            data = file.readlines()
            single_prompt = {}
            current_index = 0
            empty = []
            for each in data:
                #  Checks if the line is not empty
                if not (len(each) <= 1):
                    # Get the genre name
                    if re.search("^#", each):
                        current_genre = each.strip("#").removeprefix(" ").strip("\n")
                        single_prompt["genre"] = current_genre

                        # Check if there was a former genre
                        if re.search("^#", data[current_index - 1]):
                            empty.append(data[current_index - 1])
                        current_index += 1
                        continue

                    prefix = re.search("^..\\s", each)
                    # Remove any number prefix
                    if prefix:
                        each = each.removeprefix(prefix.group())

                    single_prompt["prompt"] = each.strip("\n")
                    current_index += 1
                    break
                else:
                    empty.append(each)
                current_index += 1

            file.close()

            # Remove the last prompt from the file
            data.pop(current_index - 1)
            for lines in empty:
                data.remove(lines)
            # Save the updated prompts list into a file
            with open("suno_prompts_v2.txt", mode="w") as fp:
                for lines in data:
                    fp.write(lines)
            return single_prompt
        except ValueError:
            # Reset the genre selection file
            os.remove(os.path.join(os.getcwd(), "suno_prompts_v2.txt"))
            return parse_prompts()

def get_available_platform_accounts_v2(account_type) -> list:
    """
    Get all platform credential that are stored on the virtual environment
    This assumes that the password is same for all platform account.

    :param account_type: (suno, soundcloud)
    """

    all_platform_username_environ_keys = [each for each in os.environ.keys() if
                                      re.search(f"^{account_type}.+username", each.lower())]
    password_list = [each for each in os.environ.keys() if
                     re.search(f"^{account_type}.+password", each.lower())]
    password = os.getenv(password_list[0])
    all_accounts = []
    for username in all_platform_username_environ_keys:
        try:
            all_accounts.append({
                "username": os.getenv(username),
                "password": password
            })

        except (AttributeError, ValueError):
            pass
    return all_accounts


def sign_in_with_microsoft(driver, username, password):
    """
        Sign in to Microsoft account using the username and password.
        This assumes the Microsoft account does not use device authentication
        :param driver: Webdriver object
        :param username: Account username
        :param password: Account password

    """
    print("Signing in with microsoft")
    driver.type("#i0116", username, timeout=Settings.TIMEOUT)
    driver.click_if_visible("#idSIButton9")

    # Type password
    driver.type("#i0118", password, timeout=Settings.TIMEOUT)
    driver.click_if_visible("#idSIButton9")
    if re.search(f"^{Settings.SUNO_BASE_URL}", driver.current_url):
        return

    driver.click_if_visible("#KmsiCheckboxField", timeout=Settings.TIMEOUT)
    driver.click_if_visible("#idSIButton9", timeout=Settings.TIMEOUT)


def sign_in_with_google(driver, username, password):
    """
    Sign in to a Google account using the username and password.
    This assumes the Google account uses device authentication
    :param driver: Webdriver object
    :param username: Account username
    :param password: Account password

    """
    driver.sleep(3)
    print("Enter username")
    print(driver.page_source)
    driver.type("input#identifierId", username, timeout=Settings.TIMEOUT)
    print("Waiting for continue btn")

    driver.click_if_visible("div#identifierNext > div > button", timeout=Settings.TIMEOUT)
    # driver.sleep(3)
    print("Clicked username continue btn")


    # Type password
    print("Enter password")

    driver.type("div#password > div > div > div > input", password, timeout=Settings.TIMEOUT)
    driver.click_if_visible("#passwordNext > div > button", timeout=Settings.TIMEOUT)

    print("Enter password continue btn")
    driver.sleep(3)


def download_image(link, image_name):
    """
    Downloads an image from link and store it into the downloaded_files folder
    :param image_name: Name to store the image with
    :param link: link to download the image
    :return: Returns the path to the image location
    """

    with open("downloaded_files/images/" + image_name + ".png", mode="wb") as handle:
        res = requests.get(link, stream=True)

        for block in res.iter_content(1024):
            if not block:
                break
            handle.write(block)
    return os.path.join(os.getcwd(), f"downloaded_files/images/{image_name}.png")


def get_all_downloaded_audios() -> list:
    """
    Returns a list of all downloaded audio paths from a suno download session
    :return:
    """

    download_dir = os.path.join(os.getcwd(), "downloaded_files")
    all_downloaded_audio_files_path = [os.path.join(download_dir, audio_file) for audio_file in os.listdir(download_dir)
                                       if
                                       os.path.isfile(os.path.join(download_dir, audio_file))]
    return all_downloaded_audio_files_path


def delete_downloaded_files():
    """
    Deletes all downloaded files from a run session
    :return:
    """
    track_dir = os.path.join(os.getcwd(), "downloaded_files")
    img_dir = os.path.join(os.getcwd(), "downloaded_files/images")

    for file_path in os.listdir(track_dir):
        abs_file_path = os.path.join(track_dir, file_path)
        if os.path.isfile(abs_file_path) and file_path != "driver_fixing.lock":
            os.remove(abs_file_path)

    for img_path in os.listdir(img_dir):
        abs_img_path = os.path.join(img_dir, img_path)
        if os.path.isfile(abs_img_path) and img_path != "driver_fixing.lock":
            os.remove(abs_img_path)


def send_telegram_message(message: str):
    """
    Sends a message to a telegram account
    :param message: Message to send
    """
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&parse_mode=HTML&text={message}'
        # Sends the message
        requests.get(url)
    except Exception:
        pass


def send_daily_statistics(all_downloaded_audios_info: list, all_suno_accounts: list, genre: str,
                          result_from_soundcloud: list):
    """
    Send a statistical telegram report of daily process routine
    :param all_downloaded_audios_info: List of all downloaded tracks  info
    :param all_suno_accounts: List of dicts containing all available suno accounts
    :param genre: Genre name used
    :param result_from_soundcloud: List of all result the soundcloud bot returns
    :return:
    """
    date = datetime.now().date().strftime("%d/%m/%Y")
    total_songs = len(all_downloaded_audios_info)
    total_suno_accounts = len(all_suno_accounts)

    telegram_message = f"🎶 <b>Résumé de la production musicale - <i>{date}</i></b> 🎶\n\n"
    telegram_message += f"🌐 <b>Statistiques globales - Comptes Suno AI</b>\n\n"
    telegram_message += f"— Nom du genre utilisé : <i>{genre}</i>\n"
    telegram_message += f"— Nombre total de chansons créées : <i>{total_songs}</i>/<i>{total_suno_accounts * 10}</i> attendues\n"
    telegram_message += f"— Comptes Suno AI utilisés : <i>{total_suno_accounts}</i>\n\n"
    telegram_message += f"📝 <b>Détails par compte SoundCloud</b>\n\n"

    for index, upload_details in enumerate(result_from_soundcloud, start=1):
        telegram_message += f"🔹 Compte SoundCloud <i>{index}</i> - <i>{upload_details['account']}</i>\n"
        telegram_message += f"— Chansons téléversées : <i>{upload_details['upload_count']}</i>/<i>{total_suno_accounts * 10}</i> attendues\n"
        telegram_message += f"— Chansons monétisées : <i>{upload_details['monetization_count']}</i>\n"
        if index < len(result_from_soundcloud):
            telegram_message += f"——————————————————————————\n"

    send_telegram_message(telegram_message)


def rename_downloaded_audio_file(filename, new_filename):
    print("Renaming downloaded audio")
    try:
        dir_path = os.path.join(os.getcwd(), "downloaded_files")
        os.rename(os.path.join(dir_path, (filename + ".mp3")), os.path.join(dir_path, new_filename))
        print(f"Renamed {filename} to {new_filename}")
    except FileNotFoundError:
        pass
