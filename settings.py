class Settings:
    HEADLESS = True

    TIMEOUT: int = 30

    SUNO_BASE_URL = "https://app.suno.ai/"
    NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES = 2

    SOUND_CLOUD_BASE_URL = "https://soundcloud.com/"
    SOUND_CLOUD_ARTIST_BASE_URL = "https://artists.soundcloud.com/"

    # No of credits on the suno account
    NO_SESSIONS_TO_RUN_DAILY = 5

    INTERVAL_IN_HOURS = 3

    CONCURRENT_PROCESS = 5

    MAX_RETRY = 2

    # Set to True if your running main.py. Leave False if you are running main2.py
    USE_LOG_OUT = True

    from seleniumbase import Driver as webDriver

    DRIVER = webDriver(
        uc=True, undetectable=True, headless2=HEADLESS, guest_mode=True, disable_gpu=True,
        no_sandbox=True, incognito=True, user_data_dir=None
    )



