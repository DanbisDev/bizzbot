// Function to handle the "Go" button click
function handleGoButtonClick(e) {
    // Prevent any default behavior (like form submission)
    e.preventDefault();

    const userInput = document.getElementById('user-input').value;
    const linkContainer = document.getElementById('link-container');

    // Reset the container to a collapsed state
    linkContainer.classList.remove('show');
    linkContainer.style.height = '0'; // Set height to 0
    linkContainer.style.opacity = '1'; // Make it fully transparent

    // Clear any previous content
    linkContainer.innerHTML = '';

    // Function to create the typewriter effect
    function typeWriter(text, speed, callback) {
        let i = 0;
        function type() {
            if (i < text.length) {
                linkContainer.innerHTML += text.charAt(i);

                // Recalculate height on each new character typed
                const newHeight = linkContainer.scrollHeight;
                linkContainer.style.height = `${newHeight}px`;

                i++;
                setTimeout(type, speed);
            } else {
                if (callback) callback();
            }
        }
        type();
    }

    // Show loading message with typewriter effect
    const loadingMessage = 'Generating your file...';
    typeWriter(loadingMessage, 100, function() {
        // After the loading message finishes, send the request
        fetch('/generate_link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input: userInput }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Replace the loading message with the download message
            linkContainer.innerHTML = ''; // Clear the loading message
            const downloadMessage = `Your file is ready: `;

            // Show download message with typewriter effect (up to the link)
            typeWriter(downloadMessage, 100, function() {
                // After typing the message, append the full link as HTML
                const linkElement = document.createElement('a');
                linkElement.href = data.link;
                linkElement.download = true;
                linkElement.textContent = 'Download';

                linkContainer.appendChild(linkElement); // Append the actual link

                // Recalculate and set height for the new content
                const newContentHeight = linkContainer.scrollHeight;
                linkContainer.style.height = `${newContentHeight}px`;

                // After the transition, set the height to auto for dynamic content adjustment
                setTimeout(() => {
                    linkContainer.style.height = 'auto';
                }, 800);

                // Fade in the container
                linkContainer.style.opacity = '1';
            });
        })
        .catch(error => {
            linkContainer.innerHTML = ''; // Clear the loading message
            const errorMessage = `Error: ${error.message}`;

            // Show error message with typewriter effect
            typeWriter(errorMessage, 100, function() {
                // Recalculate and set height for the error message
                const errorContentHeight = linkContainer.scrollHeight;
                linkContainer.style.height = `${errorContentHeight}px`;

                setTimeout(() => {
                    linkContainer.style.height = 'auto';
                }, 800);

                linkContainer.style.opacity = '1'; // Fade in the container
            });
        });
    });
}

// Attach the click event listener to the "Go" button
document.getElementById('go-button').addEventListener('click', handleGoButtonClick);

// Attach the "Enter" key listener to the text box
document.getElementById('user-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        handleGoButtonClick(e); // Trigger the same behavior as clicking the "Go" button
    }
});
