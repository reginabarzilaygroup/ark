document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault(); // Stop the form from submitting normally
    let files = document.getElementById('fileElem').files;
    let formData = new FormData();

    for (let i = 0; i < files.length; i++) {
        formData.append('dicom', files[i]);
    }

    // Display message right after the data is sent
    const uploadTime = new Date().toLocaleTimeString();
    document.getElementById('predictionResponse').textContent = `Data uploaded at ${uploadTime}, waiting for response...`;

    fetch('/dicom/files', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        const responseTime = new Date().toLocaleTimeString();
        // Pretty-printing the JSON response
        document.getElementById('predictionResponse').innerHTML = `Response received at ${responseTime}:<br><pre>${JSON.stringify(data, null, 2)}</pre>`;
    })
    .catch(error => {
        document.getElementById('predictionResponse').textContent = 'Upload failed: ' + error;
    });
});

function updateFileList() {
    let input = document.getElementById('fileElem');
    let output = document.getElementById('fileList');

    output.innerHTML = ''; // Clear the current list
    let filesToShow = Math.min(input.files.length, 4); // Limit to top 4 files

    for (let i = 0; i < filesToShow; i++) {
        let li = document.createElement('li');
        li.textContent = `File ${i + 1}: ${input.files[i].name}`;
        output.appendChild(li);
    }

    // If there are more than 4 files, show "and X more"
    if (input.files.length > 4) {
        let additionalFiles = input.files.length - 4;
        let li = document.createElement('li');
        li.textContent = `... and ${additionalFiles} more`;
        output.appendChild(li);
    }

    if (input.files.length === 0) {
        output.innerHTML = '<li>No files selected!</li>';
    }
}


document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('loadInfoBtn').addEventListener('click', function() {
        fetch('/info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('infoResponse').innerHTML = `Model information:<br><pre>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(error => {
            console.error('Error fetching info:', error);
            document.getElementById('infoResponse').textContent = 'Failed to load info.';
        });
    });

    // Trigger the button click after defining the click event listener
    document.getElementById('loadInfoBtn').click();
});