'use strict';
// public/script.js
// public/script.js

document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const scoreResultDiv = document.getElementById('scoreResult');
    // Clear previous results and show loading message
    scoreResultDiv.innerHTML = '<p>Calculating scores...</p>';
    scoreResultDiv.style.color = 'black'; // Reset text color

    const formData = new FormData(event.target);

    // Make sure this URL matches your Flask backend address and port
    const backendUrl = 'http://127.0.0.1:5000/score';

    try {
        const response = await fetch(backendUrl, {
            method: 'POST',
            body: formData,
            // Note: Browsers automatically set Content-Type: multipart/form-data
            // when using FormData, so you don't need to set it manually.
        });

        // Check if the response status indicates an error (e.g., 400, 500)
        if (!response.ok) {
            // Attempt to read the error message from the backend JSON response
            const errorData = await response.json();
            const errorMessage = errorData.error || `HTTP error! status: ${response.status}`;
            throw new Error(`Backend error: ${response.status} - ${errorMessage}`);
        }

        // If the response is OK, parse the JSON body
        const scores = await response.json(); // Expects the scores dictionary

        // --- Display the Results ---
        let resultHtml = `
            <h2>JEMATS Scores:</h2>
            <p><strong>TF-IDF Similarity:</strong> ${scores.tfidf_score * 100}%</p>
            <p><strong>Prioritized Skill Match:</strong> ${scores.prioritized_skill_score * 100}%</p>
            <p><strong>Combined Score:</strong> ${scores.combined_score * 100}%</p>
        `;

        // Display Matched Items (categorized, with section info)
        if (scores.matched_items && Object.keys(scores.matched_items).length > 0) {
             resultHtml += `<h3>Matched JD Items:</h3>`;
             // Iterate through the categories (labels)
             for (const label in scores.matched_items) {
                 if (scores.matched_items[label].length > 0) {
                     resultHtml += `<p><strong>${label}:</strong></p><ul>`;
                     // Iterate through the list of matched items for this category
                     scores.matched_items[label].forEach(item_info => {
                          // item_info is a dict like {'text': '...', 'matched_in_sections': [...], 'achieved_weight': ...}
                          resultHtml += `<li>'${item_info.text}' (in sections: ${item_info.matched_in_sections.join(', ')})</li>`;
                     });
                     resultHtml += `</ul>`;
                 }
             }
        } else {
             resultHtml += `<p>No specific JD requirements matched in Resume.</p>`;
        }

        // Display Missing Items (categorized)
        if (scores.missing_items && Object.keys(scores.missing_items).length > 0) {
             resultHtml += `<h3>Missing JD Items:</h3>`;
              // Iterate through the categories (labels)
             for (const label in scores.missing_items) {
                 if (scores.missing_items[label].length > 0) {
                     resultHtml += `<p><strong>${label}:</strong></p><ul>`;
                      // missing_items[label] is a list of strings (original JD text)
                     scores.missing_items[label].forEach(missing_item_text => {
                          resultHtml += `<li>'${missing_item_text}'</li>`;
                     });
                     resultHtml += `</ul>`;
                 }
             }
        } else {
             resultHtml += `<p>All extracted JD items found in Resume.</p>`;
        }

        scoreResultDiv.innerHTML = resultHtml; // Update the div with the results
        scoreResultDiv.style.color = 'green'; // Indicate success

    } catch (error) {
        // Handle errors during the fetch or processing
        scoreResultDiv.innerHTML = `Error getting scores: ${error}`;
        scoreResultDiv.style.color = 'red'; // Indicate error
        console.error('Fetch error:', error); // Log the error to the browser console
    }
});