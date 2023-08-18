const logContent = document.getElementById('log-content');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const startScriptButton = document.getElementById('start-script-button');
const stopCommandButton = document.getElementById('stop-command-button');
const stopProcessButton = document.getElementById('stop-process-button');
const interfaceSelect = document.getElementById('interface-select');
const startCaptureButton = document.getElementById('start-capture-button');
const stopCaptureButton = document.getElementById('stop-capture-button');
const captureNameInput = document.getElementById('capture-name-input')
let eventSource = null;
let dropdownVisible = false;

function sendMessage() {
    const message = messageInput.value;

    // Send the message to the server
    fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `message=${encodeURIComponent(message)}`
    })
    .then(response => response.text())
    .then(data => {
        console.log(data); // Optional: log the response from the server
    })
    .catch(error => {
        console.error('Error:', error);
    });

    // Clear the input field
    messageInput.value = '';
}

sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent the default form submission
        sendMessage();
    }
});

function hideMessageInput() {
    messageInput.style.display = 'none';
}

function showMessageInput() {
    messageInput.style.display = 'block';
}

function hideSendButton() {
    sendButton.style.display = 'none';
}

function showSendButton() {
    sendButton.style.display = 'block';
}


function hideCaptureControls() {
    startCaptureButton.style.display = 'none';
    stopCaptureButton.style.display = 'none';
    interfaceSelect.style.display = 'none';
}

function showCaptureControls() {
    startCaptureButton.style.display = 'inline-block';
    stopCaptureButton.style.display = 'inline-block';
    interfaceSelect.style.display = 'inline-block';
}

function isValidCaptureName(name) {
    // Define a regular expression pattern for valid names (letters and numbers only)
    const pattern = /^[a-zA-Z0-9_]+$/;
    return pattern.test(name);
}


function populateInterfaceDropdown() {
    // Fetch the list of available interfaces from the server
    fetch('/get_interfaces')
        .then(response => response.json())
        .then(data => {
            console.log(data); // Debug: Check fetched data

            const interfaceSelect = document.getElementById('interface-select');

            // Clear existing options
            interfaceSelect.innerHTML = '';

            // Populate the dropdown with interface options
            data.forEach(interfaceName => {
                const option = document.createElement('option');
                option.value = interfaceName;
                option.textContent = interfaceName;
                interfaceSelect.appendChild(option);
            });

            // Display the dropdown and buttons
            showCaptureControls();
            dropdownVisible = true;
        })
        .catch(error => {
            console.error('Error:', error);
        });
}



function connectToStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }

    eventSource = new EventSource('/stream');

    eventSource.addEventListener('message', function(event) {
        console.log('Received message:', event.data); // Debug: Log the received message


        const line = document.createElement('p');
        line.textContent = event.data;
        logContent.appendChild(line);

        // Scroll to the newly added line
        line.scrollIntoView();

         // Check if the script is starting
        if (event.data.includes('*** Starting CLI')) {

            if (!dropdownVisible) {
                console.log('Dropdown and buttons should appear now.'); // Debug: Check if this line is reached
                // Populate the dropdown and show the capture controls after the script starts
                populateInterfaceDropdown();
                const captureContainer = document.querySelector('.capture-container');
                captureContainer.style.display = 'block'; // Display the container
                showCaptureControls();
                showMessageInput();
                showSendButton();
            }
            stopProcessButton.style.display = 'inline-block';
        }

    });
}

startScriptButton.addEventListener('click', function () {
    // Start the script
    fetch('/start_script', {
        method: 'GET'
    })
    .then(response => response.text())
    .then(data => {
        console.log(data); // Optional: log the response from the server
        startScriptButton.style.display = 'none';

        hideCaptureControls();
        stopProcessButton.style.display = 'none'

        connectToStream(); // Establish a new EventSource connection
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

stopCommandButton.addEventListener('click', function() {
    // Stop the command
    fetch('/stop_script', {
        method: 'GET'
    })
    .then(response => response.text())
    .then(data => {
        console.log(data); // Optional: log the response from the server
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

stopProcessButton.addEventListener('click', function() {
    // Stop the process
    fetch('/stop_process', {
        method: 'GET'
    })
    .then(response => response.text())
    .then(data => {
        console.log(data); // Optional: log the response from the server
        startScriptButton.style.display = 'block';
        hideCaptureControls();
        hideMessageInput();
        hideSendButton();
        stopProcessButton.style.display = 'none';
        dropdownVisible=false;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

startCaptureButton.addEventListener('click', function() {
    const selectedInterface = interfaceSelect.value;
    const captureName = captureNameInput.value.trim();

    if (captureName === '') {
        alert('Please enter a capture name.');
        return;
    }

    if (!isValidCaptureName(captureName)) {
        alert('Capture name should only contain letters, numbers, and underscores.');
        return;
    }

    // Start the capture
    fetch('/start_capture', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `interface=${encodeURIComponent(selectedInterface)}&name=${encodeURIComponent(captureName)}`
    })
    .then(response => response.text())
    .then(data => {
        console.log(data); // Optional: log the response from the server
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

stopCaptureButton.addEventListener('click', function() {
    // Stop the capture
    fetch('/stop_capture', {
        method: 'GET'
    })
    .then(response => response.text())
    .then(data => {
        console.log(data); // Optional: log the response from the server
        captureNameInput.value = '';
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

// Establish the initial EventSource connection
connectToStream();