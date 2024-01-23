# Auto Track Generation and Auto Upload

>> #### This is a automation project that generates tracks on suno based a prompt and genre rules and upload these downloaded tracks to a soundcloud artist profile.

> Support concurrent sessions in cases of multiple suno.ai or souncloud accounts

### Usage
> - Create a virtual environment
> - Download and extract the zip file
> - Open the extracted folder with your favorite code editor
> - On the terminal:
> > pip install -r requirements.txt
> - After requirements installation
> - Add the log in credentials as an enviroment variable
> > python main.py

###### Note: Run main2.py only on production on cloud server e.g heroku dyno

> #### Open the settings.py to view how the program can be customized and modified

### Process Flow
The automation process is divided into two main sections.
- Suno Track Generation
- SoundCloud Tracks Uploads and Monetization


### Suno Track Generations
> This section creates, download track on and from suno.ai platform

Below are the serial process for its execution
 - Log into a suno account using the associated microsoft credentials
 - Accepts list of prompts and genre rules
 - Generate tracks based on the number of credit available on the suno account
 - Extrack Track images and tags 
 - Downloads the track
 - Organizes the downloads such that a track is grouped with its image, tag and genre
 - Return the result list of each downloads for further processing


### SoundCloud Tracks Uploads and Monetization
> This section basically upload the available downloaded tracks to a soundcloud 
artist account and then monetizes the uploaded tracks after it has been synchronized.

Below are the process for the execution
- Log into an soundcloud artist profile using the associated google credentials
- Accepts a list of downloaded result which has been organised from the suno downloand module
- Upload the tracks available in the download list along with the track image and associated tags
- Synchronize the uploads tracks with soundcloud
- Monetize all un monetized tracks available on the account.

#

> #### Developer: Weber