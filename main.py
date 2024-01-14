import os
import time
from threading import Thread
from settings import Settings
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from utils import parse_prompts, get_available_platform_accounts_v2, delete_downloaded_files, send_daily_statistics
from soundcloud_uploads.soundcloud import run_soundcloud_bot
from sunodownloads.sono_ai_spider import run_suno_bot

# sched = BackgroundScheduler()


# @sched.scheduled_job('cron', day_of_week='mon-sun', hour=1)
def automation_process():
    all_downloaded_audios_info = list()
    all_suno_accounts = get_available_platform_accounts_v2("suno")
    all_soundcloud_account = get_available_platform_accounts_v2("soundcloud")
    result_from_soundcloud = list()
    genre_used = ""
    for session in range(Settings.NO_SESSIONS_TO_RUN_DAILY):
        prompt_info = parse_prompts()
        genre_used = prompt_info["genre"]

        start_index = 0
        end_index = Settings.CONCURRENT_PROCESS
        while True:
            #   Run 5 suno bot concurrently
            all_suno_threads = []
            for account in all_suno_accounts[start_index:end_index]:
                # Create a suno AI bot instance
                suno_thread = Thread(name="Suno Thread {}".format((all_suno_accounts.index(account) + 1)),
                                     target=run_suno_bot,
                                     args=(
                                         account['username'], account['password'], prompt_info,
                                         all_downloaded_audios_info))
                suno_thread.start()
                print(suno_thread.name + " started")
                all_suno_threads.append(suno_thread)
                time.sleep(2)
                break

            # Wait for all suno thread to finish
            for suno_thread in all_suno_threads:
                suno_thread.join()
            if end_index >= len(all_suno_accounts):
                break
            break

            start_index = end_index
            end_index += Settings.CONCURRENT_PROCESS

        # Sound Cloud Upload and monetization
        start_index = 0
        end_index = Settings.CONCURRENT_PROCESS

        while True:
            #  Run 5 soundcloud bots concurrently
            all_soundcloud_threads = []
            for account in all_soundcloud_account[start_index:end_index]:
                # Create a soundcloud bot instance
                soundcloud_thread = Thread(name=f"Soundcloud account: {account['username']}", target=run_soundcloud_bot,
                                           args=(os.getenv("SOUNDCLOUD_LINK"), account['username'], account['password'],
                                                 all_downloaded_audios_info, result_from_soundcloud)
                                           )
                soundcloud_thread.start()
                print(soundcloud_thread.name + " started")
                all_soundcloud_threads.append(soundcloud_thread)
                time.sleep(2)
                break

            # Wait for all suno thread to finish
            for soundcloud_thread in all_soundcloud_threads:
                soundcloud_thread.join()

            if end_index >= len(all_soundcloud_account):
                break
            break
            start_index = end_index
            end_index += Settings.CONCURRENT_PROCESS

        delete_downloaded_files()
        send_daily_statistics(all_downloaded_audios_info, all_suno_accounts, genre_used, result_from_soundcloud)
        break
        # print(f"\n\nWaiting for the next {Settings.INTERVAL_IN_HOURS} hours before next session")
        time.sleep(60)
    # Send the statistical report for the whole day process
    print("done")
    send_daily_statistics(all_downloaded_audios_info, all_suno_accounts, genre_used, result_from_soundcloud)


# sched.start()
automation_process()
