document.addEventListener('DOMContentLoaded', function() {
    const selectionForm = document.getElementById('search-form');
    const loadingScreen = document.getElementById('loading-screen');
    const resultContainer = document.getElementById('result-container');
    const resultText = document.getElementById('result-text');
    const indexContainer = document.getElementById('index-container');
    const formContainer = document.getElementById('form-container');
    const baseContainer = document.getElementById('base-container');
    const blockListContainer = document.getElementById('blocklist-container');
    const comingSoonContainer = document.getElementById('comingsoon-container');
    const errorContainer = document.getElementById('error-container');
    const pendingRequestContainer = document.getElementById('pending-request-container');
    const timeoutContainer = document.getElementById('timeout-container');
    const submitButton = document.getElementById('submit-button');
    const identifierInput = document.getElementById('identifier');
    const TIMEOUT_DURATION = 180000;

//    // Example: Push a new state with the state object
//    function pushNewState() {
//        history.pushState({ fromBackButton: true }, 'Home', '/');
//    }

//    // Handle the back button behavior
//    window.addEventListener('popstate', function(event) {
//        if (event.state && event.state.fromBackButton) {
//            console.log("inside");
//            window.location.href = '/';
//        }
//    });

//    pushNewState();

    function handleTimeout() {
        // Perform actions when the server doesn't respond within the specified timeout
        // For example, you can display an error message or take other appropriate actions.
        console.log('Server request timed out. Please try again later.');
        hideInProgressContainer(); // Hide the "request in progress" container if it was shown
        showTimeoutContainer(); // Show the error container with a timeout message
    }

    // Function to show the loading screen
    function showLoadingScreen() {
        console.log('showLoadingScreen() called');
        loadingScreen.style.display = 'block';
    }

    function showComingSoonContainer() {
        console.log('showLoadingScreen() called');
        comingSoonContainer.style.display = 'block';
    }

    function hideComingSoonContainer() {
        console.log('hideLoadingScreen() called');
        comingSoonContainer.style.display = 'none';
    }

    // Function to hide the loading screen
    function hideLoadingScreen() {
        console.log('hideLoadingScreen() called');
        loadingScreen.style.display = 'none';
    }

    function showErrorContainer() {
        console.log('showErrorContainer() called');
        errorContainer.style.display = 'block';
    }

    function hideErrorContainer() {
        console.log('hideErrorContainer() called');
        errorContainer.style.display = 'none';
    }

    function showInProgressContainer() {
        console.log('showInProgressContainer() called');
        pendingRequestContainer.style.display = 'block'
    }

    function hideInProgressContainer() {
        console.log('hideInProgressContainer() called');
        pendingRequestContainer.style.display = 'none'
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
        console.log('hideBaseContainer() called');
        baseContainer.style.display = 'none';
    }

    function showBaseContainer() {
        console.log('showBaseContainer() called');
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
        console.log('showIndexContainer() called');
        indexContainer.style.display = 'block';
    }

    // Function to display the result data
    function showResult(data) {
        console.log('showResult() called');
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
                    const formattedDate = timestamp.toLocaleDateString('en-US', {timeZone: 'UTC'}); // Format date
                    const blockItem = document.createElement('li');

                    blockItem.textContent = `Handle: ${item.handle}, Date: ${formattedDate}`;
                    blockListData.appendChild(blockItem);
                });
                hideLoadingScreen();
                showBlockListContainer();
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
            resultText.textContent = `Total User count: ${data.count}`;
            hideLoadingScreen();
            showResultContainer();
        }
        else if (data.who_block_list) {
            const blockListData = document.getElementById('block-list-data');
            const userHeading = document.getElementById('user-heading');
            const blockCount = document.getElementById('block-count');
            const fragment = document.createDocumentFragment();

            userHeading.textContent = 'For User: ' + data.user;
            blockCount.textContent = `Total Users that block this account: ${data.counts}`;

            blockListData.innerHTML = '';

            data.who_block_list.forEach((item, index) => {
                const timestamp = new Date(data.date[index]);
                const formattedDate = timestamp.toLocaleDateString('en-US', { timeZone: 'UTC' });
                const blockItem = document.createElement('li');

                blockItem.innerHTML = `Handle: ${item}, Date: ${formattedDate}`;
                blockListData.appendChild(blockItem);
            });
            hideLoadingScreen();
            showBlockListContainer();
        }
         else if (data.in_common_users && Array.isArray(data.in_common_users) && Array.isArray(data.percentages)) {
            const blockListData = document.getElementById('block-list-data');
            const userHeading = document.getElementById('user-heading');
//            const blockCount = document.getElementById('block-count');
            const fragment = document.createDocumentFragment();

            userHeading.textContent = 'Blocks in common with: ' + data.user;
//            blockCount.textContent = `Total Users that block this account: ${data.counts}`;

            blockListData.innerHTML = '';

            for (let index = 0; index < data.in_common_users.length; index++) {
                const item = data.in_common_users[index];
                const percent = data.percentages[index];

                const blockItem = document.createElement('li');
                const percentItem = document.createElement('li');
                blockItem.textContent = `Handle: ${item}`;
                percentItem.textContent = `Match Percentage: ${percent}`;
                fragment.appendChild(blockItem);
                fragment.appendChild(percentItem);
            }

            blockListData.appendChild(fragment);
            hideLoadingScreen();
            showBlockListContainer();
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

    // Add event listener to the identifier input field
    identifierInput.addEventListener('input', function (event) {
        // Check if the input field is empty and the selected option is not 4
        const optionSelected = document.getElementById("selection").value;
        if (this.value.trim() === '' && optionSelected !== '4') {
            submitButton.disabled = true; // Disable the submit button
        } else {
            submitButton.disabled = false; // Enable the submit button
        }
    });

    // Add event listener to the form submit button
    selectionForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission

        const formData = new FormData(selectionForm);

        // Check if the input field (identifier) is empty and set its value to "blank"
        if (identifierInput.value.trim() === '') {
            identifierInput.value = 'blank';
        }

        submitButton.disabled = true; // Disable the form submission button
        hideBaseContainer();
        hideIndexContainer();
        showLoadingScreen(); // Show the loading screen

        // Set up the timeout
        const timeoutId = setTimeout(() => {
            // Function to execute if the timeout occurs before the server responds
            handleTimeout(); // You need to implement this function (see Step 3)
        }, TIMEOUT_DURATION);

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
            showResult(data);

            submitButton.disabled = false; // Re-enable the form submission button
        })
        .catch(error => {
            // Handle any errors here
            handleErrors(error); // Call the function to handle errors and show the index container
            hideBaseContainer();
            hideIndexContainer();
            showErrorContainer();
            submitButton.disabled = false;
        });
    });

    // Add event listener to the selection dropdown
    selection.addEventListener('change', function() {
        if (selection.value === '4') {
            // If "Get Total Users Count" is selected, disable the identifier field
            identifier.value = '';
            identifier.readOnly = true;
            submitButton.disabled = false;
        } else {
            // Enable the identifier field
            identifier.readOnly = false;
        }
    });
});