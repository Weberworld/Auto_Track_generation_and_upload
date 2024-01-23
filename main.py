"""
This is to be run only on local testing
"""

import os
import time
from threading import Thread
from settings import Settings
from apscheduler.schedulers.blocking import BlockingScheduler
from helpers import create_driver
from utils import parse_prompts, get_available_platform_accounts_v2, delete_downloaded_files, send_daily_statistics
from soundcloud_uploads.soundcloud import run_soundcloud_bot
from sunodownloads.sono_ai_spider import run_suno_bot

print("started")
sched = BlockingScheduler()


# @sched.scheduled_job('cron', day_of_week='mon-sun', hour=2)
def automation_process():
    all_downloaded_audios_info = list()
    all_suno_accounts = get_available_platform_accounts_v2("suno")
    all_soundcloud_account = get_available_platform_accounts_v2("soundcloud")
    result_from_soundcloud = list()
    print(f"Got {len(all_suno_accounts)} Suno accounts")
    print(f"Got {len(all_soundcloud_account)} Soundcloud accounts")

    # Get the 5 prompts to be used from a single genre
    all_daily_prompts = [parse_prompts() for _ in range(5)]

    genre_used = all_daily_prompts[0]["genre"]

    suno_start_index = 0
    suno_end_index = Settings.CONCURRENT_PROCESS
    while True:
        #   Run 5 suno bot concurrently
        all_suno_threads = []
        for account in all_suno_accounts[suno_start_index:suno_end_index]:
            username = account[0]
            password = account[1]

            suno_thread = Thread(name="Suno Thread {}".format((all_suno_accounts.index(account) + 1)),
                                 target=run_suno_bot,
                                 args=(create_driver(), username, password, all_daily_prompts,
                                       all_downloaded_audios_info))
            suno_thread.start()
            print(suno_thread.name + " started")
            all_suno_threads.append(suno_thread)
            time.sleep(2)

        # Wait for all suno thread to finish
        for suno_thread in all_suno_threads:
            suno_thread.join()

        # Upload the downloaded tracks to soundcloud
        soundcloud_start_index = 0
        soundcloud_end_index = Settings.CONCURRENT_PROCESS
        while True:
            #  Run 5 soundcloud bots concurrently
            all_soundcloud_threads = []
            for account in all_soundcloud_account[soundcloud_start_index:soundcloud_end_index]:
                # Create a SoundCloud bot instance
                username = account[0]
                password = account[1]

                driver = create_driver()

                soundcloud_thread = Thread(name=f"Soundcloud account: {username}", target=run_soundcloud_bot,
                                           args=(driver, os.getenv("SOUNDCLOUD_LINK"), username, password,
                                                 all_downloaded_audios_info, result_from_soundcloud)
                                           )
                soundcloud_thread.start()
                print(soundcloud_thread.name + " started")
                all_soundcloud_threads.append(soundcloud_thread)
                time.sleep(2)

            # Wait for all suno thread to finish
            for soundcloud_thread in all_soundcloud_threads:
                soundcloud_thread.join()

            if soundcloud_end_index >= len(all_soundcloud_account):
                break
            soundcloud_start_index = soundcloud_end_index
            soundcloud_end_index += Settings.CONCURRENT_PROCESS

        delete_downloaded_files()

        if suno_end_index >= len(all_suno_accounts):
            break

        suno_start_index = suno_end_index
        suno_end_index += Settings.CONCURRENT_PROCESS

    print("Sending Message")
    # Send the statistical report for the whole day process
    send_daily_statistics(len(all_downloaded_audios_info), len(all_suno_accounts), genre_used, result_from_soundcloud)

    print("done")


# sched.start()
automation_process()
