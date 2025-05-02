'use strict';

document.getElementById('uploadForm')
    .addeventListener('submit', async (event) => {
      event.preventDefault();  // prevent default submission

      const scoreResultDiv = document.getElementById('score_result');
      scoreResultDiv.textContent = 'Estimating Score...';

      const formData = new FormData(event.target);

      const apiUrl = 'http://127.0.0.1:5000/score'

      try {
        const response = await fetch(apiUrl, {method: 'POST', body: formData});

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`Backend error: ${response.status} - ${
              errorData.error || response.statusText}`)
        }
        const data = await response.json();
        const score = data.score * 100;

        scoreResultDiv.textContent = `Similarity Score: ${score.toFixed(2)}%`;
      } catch (e) {
        scoreResultDiv.textContent = `Error getting score: ${e}`;
        console.error('Fetch error: ', e)
      }
    })
