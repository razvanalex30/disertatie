const logContent = document.getElementById('log-content');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const startScriptButton = document.getElementById('start-script-button');
const stopCommandButton = document.getElementById('stop-command-button');
const stopProcessButton = document.getElementById('stop-process-button');
const interfaceSelect = document.getElementById('interface-select');
const startCaptureButton = document.getElementById('start-capture-button');
const stopCaptureButton = document.getElementById('stop-capture-button');
const captureNameInput = document.getElementById('capture-name-input');
const capturesTableBody = document.getElementById('captures-table-body');
const spinnerHTML = document.getElementById('spinner');

let eventSource = null;
let dropdownVisible = false;
let output_path = '';

const captures = [];


// This function adds a new capture to the captures array
function addCapture(name, interface, filepath) {
    captures.push({
        name: name,
        interface: interface,
        date: new Date().toLocaleString(),
        filepath: filepath
    });

}

// This function updates the captures table with the information from the captures array
function updateCapturesTable() {
    //If the table is initially empty remove the default text
    if (capturesTableBody.innerHTML.includes('No captures available for this topology')) {
        capturesTableBody.innerHTML = '';
    }

    //Get the capture the user is trying to input in the table
    const capture = captures[captures.length-1];

    //Prepare to create a new table row
    const row = document.createElement('tr');

    //Populate the table row with the capture info
    row.innerHTML = `
        <td>${capture.name}</td>
        <td>${capture.date}</td>
        <td><a href="/download_capture/${capture.name}" class="btn btn-primary">Download</a></td>
        <td><button  onclick="deleteCapture('${capture.name}')" class="btn btn-primary">Delete</button></td>
    `;

    //Insert the new row at the very top of the table
    capturesTableBody.insertBefore(row, capturesTableBody.firstChild);
}







// This function deletes a capture from the captures array and updates the table
function deleteCapture(fileName) {
    //Get all the table rows
    let rows = capturesTableBody.getElementsByTagName("tr");
    const confirmDelete = confirm(`Are you sure you want to delete "${fileName}"?`);

    if (confirmDelete) {

        //Iterate through the table rows
        for(let index = 0; index < rows.length; index++){

            //Check which rows has the capture name of the one the user is trying to delete via the button and remove the row visually
            if(rows[index].cells[0].innerText.includes(fileName)){
                rows[index].parentNode.removeChild(rows[index]);
            }

            //If the user is trying to remove the last capture row, replace the table content with the default message
            if(rows.length == 0){
                capturesTableBody.innerHTML = `<tr>
                        <td colspan="4">No captures available for this topology.</td>
                    </tr>`
            }
            }
        fetch('/delete_capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `filepath=${encodeURIComponent(fileName)}`
        })
        .then(response => response.text())
        .then(data => {
            console.log(data); // Optional: log the response from the server

        })
        .catch(error => {
            console.error('Error:', error);
        });
}}

//Razvan to add
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

function hidestartCaptureButton() {
    startCaptureButton.style.display = 'none';
}

function showstartCaptureButton() {
    startCaptureButton.style.display = 'inline-block';
}

function hidestopCaptureButton() {
    stopCaptureButton.style.display = 'none';
}

function showstopCaptureButton() {
    stopCaptureButton.style.display = 'inline-block';
}


function hideStopCommandButton() {
    stopCommandButton.style.display = 'none';
}

function showStopCommandButton() {
    stopCommandButton.style.display = 'inline-block';
}

function hidecaptureNameInput() {
    captureNameInput.style.display = 'none';
}

function showcaptureNameInput() {
    captureNameInput.style.display = 'inline-block';
}



function hideCaptureControls() {
    startCaptureButton.style.display = 'none';
//    stopCaptureButton.style.display = 'none';
    interfaceSelect.style.display = 'none';
}

function showCaptureControls() {
    startCaptureButton.style.display = 'inline-block';
//    stopCaptureButton.style.display = 'inline-block';
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
//        console.log('Received message:', event.data); // Debug: Log the received message


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
                showStopCommandButton();
                showcaptureNameInput();
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
        startScriptButton.style.display = 'inline-block';
        hideCaptureControls();
        hideMessageInput();
        hideSendButton();
        hidecaptureNameInput();
        hideStopCommandButton();
        hidestopCaptureButton();
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
        hidestartCaptureButton();
        showstopCaptureButton();
        output_path = data;
        const display_name = selectedInterface + "_" + captureName
        addCapture(display_name, selectedInterface, output_path);

        spinnerHTML.style.display = 'inline-block';

    // Update the captures table to reflect the new capture
//        updateCapturesTable();

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
        showstartCaptureButton();
        hidestopCaptureButton();
        updateCapturesTable();
        spinnerHTML.style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

// Establish the initial EventSource connection
connectToStream();