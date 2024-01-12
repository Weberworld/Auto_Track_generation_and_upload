/* 
    This script is responsible for automatically assigning genre name to uploaded songs on soundcloud
    To run the script: Copy and paste the script in chrome dev tools console and press enter
*/




return (function upload_tracks(genre_name){
    // Set to true if you want to use custom name
    const USE_CUSTOM_NAME = false;

    // Input the genre name you want to use
    const GENRE_NAME = genre_name;


    // // Get the list of all uploaded songs title
    let all_uploaded_song_titles = [];
    document.querySelectorAll("div.baseFields__data > div.baseFields__title > div.textfield > div.textfield__inputWrapper > input").forEach(title_ele => {
        all_uploaded_song_titles.push(title_ele.value);
    })

    // Get the list of all uploaded songs genre selection element button
    let all_uploaded_song_genre_ele = document.querySelectorAll("div.baseFields__genreSelect > div > div > button");


    // Get the list of all uploaded songs save button
    let all_uploaded_song_save_btn_ele = document.querySelectorAll("div.activeUpload__formButtons.sc-button-toolbar > button.sc-button-cta.sc-button")


    // Create an object for each song with its title as the key, genre_element and their save_btn_element as the nested object
    let all_upload_songs_info = {}
    for (let index = 0; index < all_uploaded_song_save_btn_ele.length; index++) {
        let single_song_info = {
            "genre": all_uploaded_song_genre_ele[index],
            "save_btn": all_uploaded_song_save_btn_ele[index],

        }
        all_upload_songs_info[all_uploaded_song_titles[index]] = single_song_info;
    }

    let upload_count = 0;
    let input_list = []
    // Loop through the song settings variable and set its value to the song genre
    for (let song_title in all_upload_songs_info) {
        if (Object.hasOwnProperty.call(all_upload_songs_info, song_title)) {
            try {

                all_upload_songs_info[song_title].genre.click();// Click on the current song genre selection button
                // Get the genre selection list element
                let genre_selection_list_ele = document.querySelectorAll("div > div > div > div.g-scrollable-inner > div > section > ul");
                for (let i = 0; i < genre_selection_list_ele.length; i++) {
                    let each_genre_name_list = genre_selection_list_ele[i].getElementsByTagName("a");
                    for (let index = 0; index < each_genre_name_list.length; index++) {
                        if (each_genre_name_list[index].text.toLowerCase() == GENRE_NAME.toLowerCase()) {
                            each_genre_name_list[index].click();
                            console.log(`Set Track:${song_title} to    Genre - ${GENRE_NAME}`);
                            upload_count++;
                             // Click on the song save btn
                            all_upload_songs_info[song_title]["save_btn"].click();
                            break;
                        }
                    }
                }
                console.log(`Set Track:${song_title} to    Genre - ${GENRE_NAME}`);

            }
            catch {
                () => { console.log("You have made a typo error in the track title settings") };
            }
        }
    }

    console.log(`"${upload_count}" Tracks has been uploaded`)
    console.log("Automation completed!!")


})(arguments[0]);


    // End of Script