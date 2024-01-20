import os
import json
import time
import redis
import random

from selenium.common import InvalidSessionIdException
from seleniumbase import Driver
from apscheduler.schedulers.blocking import BlockingScheduler
from seleniumbase.common.exceptions import NoSuchWindowException

from settings import Settings
from sunodownloads.sono_ai_spider import run_suno_bot
from soundcloud_uploads.soundcloud import run_soundcloud_bot
from helpers import create_driver
from utils import parse_prompts, get_available_platform_accounts_v2, send_daily_statistics, delete_uploaded_files

sched = BlockingScheduler()


def wait_randomly():
    """ Wait for a random no of secs with the range of 5"""
    time.sleep(random.randint(1, 5))


@sched.scheduled_job('cron', day_of_week='mon-sun', hour=2)
def automation_process():
    # Connect to the redis server
    r = redis.from_url(os.environ.get("REDISCLOUD_URL"))
    r.flushall()

    wait_randomly()

    all_suno_accounts = get_available_platform_accounts_v2("suno")
    all_soundcloud_accounts = get_available_platform_accounts_v2("soundcloud")
    no_of_downloaded_tracks = 0

    print(f"Got {len(all_suno_accounts)} suno accounts")
    print(f"Got {len(all_soundcloud_accounts)} soundcloud accounts")

    # Run only if suno and soundcloud account are available
    if len(all_suno_accounts) > 0 and len(all_soundcloud_accounts) > 0:

        wait_randomly()

        # Creates the webdriver
        webdriver = create_driver()

        # Get or set the prompt to use
        all_prompt_info = [json.loads(item) for item in r.lrange("daily_prompts", 0, -1)]
        if not all_prompt_info:
            all_prompt_info = [parse_prompts() for _ in range(5)]
            for item in all_prompt_info:
                r.lpush("daily_prompts", json.dumps(item))

        genre_used = all_prompt_info[0]['genre']
        print(f"Genre used: {genre_used}")

        # Get or set the next suno account index to use
        current_suno_act_index = r.get("next_suno_acct_index")
        if current_suno_act_index is None:
            # This show this is the first dyno to run. Set the index the next dyno will use
            r.set("next_suno_acct_index", 1)
            current_suno_act_index: int = 0
        else:
            r.set("next_suno_acct_index", (int(current_suno_act_index) + 1))

        while int(current_suno_act_index) < len(all_suno_accounts):
            suno_acct = all_suno_accounts[int(current_suno_act_index)]
            suno_download_result = []



            try:
                run_suno_bot(webdriver, suno_acct[0], suno_acct[1], all_prompt_info, suno_download_result)
            except (NoSuchWindowException, InvalidSessionIdException):
                # Recreate the webdriver if an error was raised
                webdriver = create_driver()
                # Retry the bot if it fails
                try:
                    run_suno_bot(webdriver, suno_acct[0], suno_acct[1], all_prompt_info, suno_download_result)
                except Exception:
                    print("Exception from suno")
                    pass
            finally:
                pass

            # Append or set to the list of downloaded suno download result on the redis server
            stored_suno_download_result = [json.loads(item) for item in r.lrange("suno_download_results", 0, - 1)]
            if stored_suno_download_result is None:
                # This means this is the first suno account to complete its download
                # Serialize and Save each item in the suno_download_result to the redis server

                for item in suno_download_result:
                    r.lpush("suno_download_results", json.dumps(item))
            else:
                stored_suno_download_result.extend(suno_download_result)
                # Serialize and Save each item in the suno_download_result to the redis server
                for item in stored_suno_download_result:
                    r.lpush("suno_download_results", json.dumps(item))

            # Add to the number of downloaded_tracks
            no_of_downloaded_tracks: int = r.get("no_of_downloaded_tracks")
            if no_of_downloaded_tracks is None:
                r.set("no_of_downloaded_tracks", len(suno_download_result))
            else:
                r.set("no_of_downloaded_tracks", (int(no_of_downloaded_tracks) + len(suno_download_result)))

            wait_randomly()
            print(f"Current number of downloaded tracks: {no_of_downloaded_tracks}")
            print(f"Suno downloads finished for account {suno_acct[0]}")

            # Upload downloaded tracks to soundcloud whenever 5 suno acct has ended
            if ((int(r.get('next_suno_acct_index')) + 1) % 5) == 0:
                wait_randomly()

                print("Starting soundcloud upload and monetization")

                # Get or set the active soundcloud account index to run
                current_soundcloud_acct_index: int = r.get("next_soundcloud_acct_index")
                if current_soundcloud_acct_index is None:
                    # This shows this is the first dyno to run soundcloud. Set the next index for the next dyno
                    r.set("next_soundcloud_acct_index", 1)
                    current_soundcloud_acct_index = 0
                elif int(current_soundcloud_acct_index) <= (len(all_soundcloud_accounts) - 1):
                    r.set("next_soundcloud_acct_index", (int(current_soundcloud_acct_index) + 1))
                else:
                    continue

                try:
                    no_of_downloaded_tracks = int(r.get("no_of_downloaded_tracks"))
                except TypeError:
                    no_of_downloaded_tracks = 0
                print(f"Soundcloud index to use: {current_soundcloud_acct_index}")

                # Upload and monetize tracks on all soundcloud accounts
                soundcloud_link = os.getenv("SOUNDCLOUD_LINK")

                all_suno_download_results = []
                while (int(current_soundcloud_acct_index)) < len(all_soundcloud_accounts):
                    print("Preparing to start process")
                    # Get all the suno download results stored on the redis server
                    all_suno_download_results = [json.loads(item) for item in r.lrange("suno_download_results", 0, -1)]

                    # If this is the last soundcloud to run, free the suno_download_result list from the redis server
                    if int(current_soundcloud_acct_index) == (len(all_soundcloud_accounts) - 1):
                        r.delete("suno_download_results")

                    running_soundcloud_acct = all_soundcloud_accounts[int(current_soundcloud_acct_index)]
                    print(running_soundcloud_acct)
                    soundcloud_results = []
                    try:
                        run_soundcloud_bot(
                            webdriver, soundcloud_link, running_soundcloud_acct[0],
                            running_soundcloud_acct[1], all_suno_download_results, soundcloud_results
                        )
                    except Exception:
                        print("Got exception from Soundcloud")

                    else:
                        wait_randomly()
                        # Store the soundcloud result on the redis server
                        # Get the previously stored result from the redis server
                        previous_stored = [json.loads(item) for item in r.lrange("soundcloud_results", 0, -1)]
                        for each in previous_stored:
                            for result in soundcloud_results:
                                if each["account"] == result["account"]:
                                    result["upload_count"] += each["upload_count"]
                                    result["monetization_count"] += each["monetization_count"]
                                    r.lpush("soundcloud_results", json.dumps(result))

                    # Close and re-open a driver after each soundcloud operation is completed
                    webdriver.quit()
                    webdriver = create_driver()

                    # Set the next soundcloud account index to run
                    current_soundcloud_acct_index = int(r.get("next_soundcloud_acct_index"))
                    r.set("next_soundcloud_acct_index", (current_soundcloud_acct_index + 1))
                # Reset the soundcloud account index
                r.set("next_soundcloud_acct_index", 0)

                # Delete the stored information about the uploaded tracks
                delete_uploaded_files(all_suno_download_results)

            current_suno_act_index = int(r.get("next_suno_acct_index"))
            r.set("next_suno_acct_index", (current_suno_act_index + 1))

        webdriver.quit()
        # Send the report of the whole activities to the set telegram user

        soundcloud_results = [json.loads(result) for result in r.lrange("soundcloud_results", 0, -1)]

        # Send the alert notification if other dynos has not sent it
        try:
            current_soundcloud_acct_index = int(r.get("next_soundcloud_acct_index"))
            if current_soundcloud_acct_index == 0:
                print("Sending result stats ...")
                send_daily_statistics(no_of_downloaded_tracks, len(all_suno_accounts), genre_used, soundcloud_results)
        except TypeError:
            pass

    else:
        print("No Soundcloud account or Suno account found !!")


# sched.start()

