/* 
    This Javascript snippet will automate the process of monetizing songs on the opened soundcloud
   upload page
*/


// No of seconds to wait before timeout
let TIMEOUT = 1000;
// No of seconds to wait before filling the next form
const FILL_FORM_INTERVAL = 2;





// Main Script
let page_no = 1;
let no_form_filled = 0;

startMonetizingFromCurrentPage();

// End of main







function startMonetizingFromCurrentPage() {
    monetizeCurrentPage();
    let next_page_btn = nextPage()
    if (next_page_btn) {
        monetizeCurrentPage();
        TIMEOUT += 5000;
        setTimeout(goToNextPage, TIMEOUT);
        TIMEOUT += 5000;
        setTimeout(startMonetizingFromCurrentPage, TIMEOUT); // Wait 5 secs for the next page to load
    }
    else {
        console.log("Monetization Completed!!")
        console.log(`${no_form_filled} Monetization forms are filled in total`);
    }
}



// Monetize all non monetized songs on the current page
function monetizeCurrentPage() {
    // Get all monetize this track btn on the current page
    let all_monetize_btns_ele = document.querySelectorAll("#right-before-content > div.my-3 > div > div > div:nth-child(2) > div > button")
    if (all_monetize_btns_ele) {
        let time_to_fil_form = 1000
        let no_of_forms_in_the_current_page = 0;
        // Click on each of the monetize btn element and fill its form
        all_monetize_btns_ele.forEach(btn_ele => {
            // Check if it is a monetize track btn
            if (btn_ele.textContent == "Monetize this track") {

                setTimeout(waitForFormToBecomeVisibleAndFill, time_to_fil_form, btn_ele);
                // Increasse the interval seconds
                time_to_fil_form += (FILL_FORM_INTERVAL * 1000);
                TIMEOUT += (FILL_FORM_INTERVAL * 1000)
                no_form_filled++;
                no_of_forms_in_the_current_page++;
            }
        },)
        console.log(`Found ${no_form_filled} Monetization forms to be filled`);

    }
    else {
        // Wait for the page to load all tracks
        setTimeout(monetizeCurrentPage, 5000);
    }
}


// - Wait for the form window (#monetization-form) to become visible
function waitForFormToBecomeVisibleAndFill(form_btn) {

    form_btn.click()
    let form_ele = document.getElementById("monetization-form");
    if (form_ele) {  // Form is present. Fill and submit it
        fillMonetizationForm(form_ele);
        setTimeout(function () { console.log("Filled a form") }, TIMEOUT);
    }
    else {
        // Form element is not visible, wait and try again
        setTimeout(waitForFormToBecomeVisibleAndFill, (TIMEOUT * 1000), form_btn); // Wait for Timeout secs   
    }
}


// - Fill the form and submit
function fillMonetizationForm(form_ele) {

    form_ele.querySelector("div > div:nth-child(1) > div > label > div.mt-1 > div > div > button").click(); // Click on the content rating 
    // Get the content rating select list
    let content_rating_select_list_ele = form_ele.querySelector("div > div:nth-child(1) > div > label > div.mt-1 > div > ul");
    let rating_options = content_rating_select_list_ele.getElementsByTagName("li");
    // Loop through the rating options and selct the Explicit option
    for (let i = 0; i < rating_options.length; i++) {
        if (rating_options[i].textContent == "Explicit") {
            rating_options[i].click();
            break;
        }
    }
    // In the songwriter options select "Another writer"
    form_ele.querySelector("div.mb-3 > div > div:nth-child(1) > div.flex > label > div.mt-1 > label:nth-child(2) > div > input").click();

    // Mark that you agree to the T/C
    form_ele.querySelector("div:nth-child(15) > div input").click()

    // Submit the form_ele
    form_ele.querySelector("div:nth-child(16) > button:nth-child(2)").click();

    // Click on the cancel btn
    form_ele.querySelector("div:nth-child(16) > button").click();
}
