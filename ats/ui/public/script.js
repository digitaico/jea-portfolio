'use strict';

document.getElementById('uploadForm')
    .addEventListener('submit', async (event) => {
      event.preventDefault();  // prevent default submission

      const scoreResultDiv = document.getElementById('score_result_div');

      scoreResultDiv.textContent = 'Estimating Scores...';

      const formData = new FormData(event.target);

      const apiUrl = 'http://127.0.0.1:5000/score'

      try {
        const response = await fetch(apiUrl, {method: 'POST', body: formData});

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`Backend error: ${response.status} - ${
              errorData.error || response.statusText}`)
        }
        const scores = await response.json();
        console.log(`@@ ${JSON.stringify(scores, null, 2)}`)

        let resultHtml = `
            <h2>JEMATS Scores:</h2>
            <p><strong>TF-IDF Similarity:</strong> ${scores.tfidf_score * 100} </p>
            <p><strong>Prioritized Skill Score:</strong> ${scores.skill_score * 100} </p>
            <p><strong>Combined Score:</strong> ${scores.combined_score * 100}</p>
        `;
       
        if (scores.matched_items && Object.keys(scores.matched_items).length > 0) {
          resultHtml += `<h3>Matched JD Items:</h3>`;
          for (const label in scores.matched_items) {
              if (scores.matched_items[label].length > 0) {
                  resultHtml += `<p><strong>${label}:</strong> ${scores.matched_items[label].join(', ')}</p>`;
              }
          }
     } else {
          resultHtml += `<p>No specific JD requirements matched in Resume.</p>`;
     }        

     // Display Missing Items
     if (scores.missing_items && Object.keys(scores.missing_items).length > 0) {
      resultHtml += `<h3>Missing JD Items:</h3>`;
      for (const label in scores.missing_items) {
          if (scores.missing_items[label].length > 0) {
              resultHtml += `<p><strong>${label}:</strong> ${scores.missing_items[label].join(', ')}</p>`;
          }
      }
 } else {
      resultHtml += `<p>All extracted JD items found in Resume.</p>`;
 }

      scoreResultDiv.innerHTML = resultHtml;

      } catch (e) {
        scoreResultDiv.textContent = ` Error getting score: ${e} `;
        console.error('Fetch error: ', e)
      }
    });
