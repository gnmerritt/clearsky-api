document.addEventListener('DOMContentLoaded', function() {
    const selectionForm = document.getElementById('search-form');
    const loadingScreen = document.getElementById('loading-screen');
    const resultContainer = document.getElementById('result-container');
    const resultText = document.getElementById('result-text');
    const indexContainer = document.getElementById('index-container');
    const formContainer = document.getElementById('form-container');
    const baseContainer = document.getElementById('base-container');
    const blockListContainer = document.getElementById('blocklist-container');

    let requestInProgress = false;
    const submitButton = document.getElementById('submit-button');

    // Function to show the loading screen
    function showLoadingScreen() {
        console.log('showLoadingScreen() called');
        loadingScreen.style.display = 'block';
    }

    // Function to hide the loading screen
    function hideLoadingScreen() {
        console.log('hideLoadingScreen() called');
        loadingScreen.style.display = 'none';
    }

    // Function to show the result container
    function showResultContainer() {
        console.log('showResultContainer() called');
        resultContainer.style.display = 'block';
    }

    // Function to hide the result container
    function hideResultContainer() {
        console.log('hideResultContainer() called');
        resultContainer.style.display = 'none';
    }

    function showBlockListContainer() {
        console.log('showBlockListContainer() called');
        blockListContainer.style.display = 'block';
    }

    function hideBaseContainer() {
        console.log('hideBaseContainer() called.');
        baseContainer.style.display = 'none';
    }

    function showBaseContainer() {
        console.log('showBaseContainer() called.');
        baseContainer.style.display = 'block';
    }

    function hideBlockListContainer() {
        console.log('hideBlockListContainer() called');
        blockListContainer.style.display = 'none';
    }

    function hideIndexContainer() {
        console.log('hideIndexContainer() called');
        indexContainer.style.display = 'none';
    }

    function showIndexContainer() {
        console.log('showIndexContainer() called.');
        indexContainer.style.display = 'block';
    }

    // Function to display the result data
    function showResult(data) {
        console.log('showResult() called');
        console.log(data);
        console.log(data.count);
        resultText.innerHTML = ''; // Clear the previous result text

        if (data.result) {
            const resultParagraph = document.createElement('p');
            resultParagraph.textContent = data.result;
            resultText.appendChild(resultParagraph);
            hideLoadingScreen();
            showResultContainer();
        }
        else if (data.block_list) {
            if (Array.isArray(data.block_list)) {
                const blockListData = document.getElementById('block-list-data');
                const userHeading = document.getElementById('user-heading');
                const blockCount = document.getElementById('block-count');
                const fragment = document.createDocumentFragment();

                userHeading.textContent = 'For User: ' + data.user;
                blockCount.textContent = `Total Blocked Users: ${data.count}`;

                blockListData.innerHTML = '';

                data.block_list.forEach(item => {
                    const timestamp = new Date(item.timestamp);
                    const formattedDate = timestamp.toLocaleDateString(); // Format date as per locale
                    const blockItem = document.createElement('li');

                    blockItem.textContent = `Handle: ${item.handle}, Date: ${formattedDate}`;
                    blockListData.appendChild(blockItem);

                    hideLoadingScreen();
                    showBlockListContainer();
                });
            }
            else {
                const noResultParagraph = document.createElement('p');
                noResultParagraph.textContent = 'No result found.';
                resultText.appendChild(noResultParagraph);
                hideLoadingScreen();
                showResultContainer(); // Show result container
            }
        }
        else if (data.count) {
            // Display result container with total count
            console.log(data.count);
//                const countParagraph = document.createElement('p');
            resultText.textContent = `Total User count: ${data.count}`;
//                resultText.appendChild(countParagraph);
            hideLoadingScreen();
            showResultContainer();
        }
        else {
            const noResultParagraph = document.createElement('p');
            noResultParagraph.textContent = 'No result found.';
            resultText.appendChild(noResultParagraph);
            hideLoadingScreen();
            showResultContainer(); // Show result container
        }
    }

    // Function to handle errors and show the index container if needed
    function handleErrors(error) {
        console.error("Error fetching data:", error);

        const errorParagraph = document.createElement('p');
        errorParagraph.textContent = 'Error fetching data. Please try again later.';
        resultText.appendChild(errorParagraph);

        hideLoadingScreen(); // Hide the loading screen in case of an error
        hideResultContainer(); // Hide the result container and show the index container
        hideBlockListContainer();
    }

    // Add event listener to the form submit button
    selectionForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission
        console.log('Form submit button clicked');

        optionSelected = document.getElementById("selection").value;
        console.log(optionSelected);

        if (optionSelected === "5") {
            var confirmed = window.confirm("This will take an extremely long time! Do you want to proceed?");
//            alert("This will take a long time!");
            if (!confirmed) {
                return;
            }
        }

        if (requestInProgress) {
            // A request is already in progress, do not make another request
            return;
        }

        // Mark that a request is in progress
        requestInProgress = true;

        submitButton.disabled = true; // Disable the form submission button
        hideBaseContainer();
        hideIndexContainer();
        showLoadingScreen(); // Show the loading screen

        // Perform your form submission or AJAX request using JavaScript Fetch API or Axios
        fetch('/selection_handle', {
            method: 'POST',
            body: new FormData(selectionForm)
        })
        .then(response => {
            // Check if the response status is successful (HTTP 200-299)
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            // Return the response JSON data
            return response.json();
        })
        .then(data => {
            // Update the resultText container with the server response
            console.log("show data in submit event listener.");
            console.log(data);
            showResult(data);

            // Reset the requestInProgress flag to allow future requests
            requestInProgress = false;
            submitButton.disabled = false; // Re-enable the form submission button
        })
        .catch(error => {
            // Handle any errors here
            handleErrors(error); // Call the function to handle errors and show the index container
            showBaseContainer();
            showIndexContainer();
        // Reset the requestInProgress flag in case of an error
        requestInProgress = false;
        submitButton.disabled = false;
        });
    });

    // Add event listener to the selection dropdown
    selection.addEventListener('change', function() {
        if (selection.value === '4') {
            // If "Get Total Users Count" is selected, disable the identifier field
            identifier.value = '';
            identifier.readOnly = true;
        } else {
            // Enable the identifier field
            identifier.readOnly = false;
        }
    });
});