class Settings:
    HEADLESS = True

    TIMEOUT: int = 20

    SUNO_BASE_URL = "https://app.suno.ai/"
    NO_OF_TRACKS_SUNO_ACCOUNT_GENERATES = 2

    SOUND_CLOUD_BASE_URL = "https://soundcloud.com/"
    SOUND_CLOUD_ARTIST_BASE_URL = "https://artists.soundcloud.com/"

    # No of credits on the suno account
    NO_SESSIONS_TO_RUN_DAILY = 5

    # No of process to run concurrently
    CONCURRENT_PROCESS = 5

    MAX_RETRY = 2

    # Set to True if your running main.py. Leave False if you are running main2.py
    LOCAL_TESTING = False

    # No of secs to wait for a suno track to be ready for download
    MAX_TIME_FOR_SUNO_GENERATION = 120
