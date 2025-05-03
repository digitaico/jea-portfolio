'use strict';

document.getElementById('uploadForm')
    .addEventListener('submit', async (event) => {
      event.preventDefault();  // prevent default submission

      const scoreResultDiv = document.getElementById('score_result');
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

        scoreResultDiv.innerHTML = `
        <h2>JEMATS Scores:</h2>
        <p><strong>TF-IDF Similarity:</strong> ${
            scores.tfidf_score * 100: .2f}%</p>
        <p><strong>Skill Match:</strong> ${scores.skill_score * 100: .2f}%</p>
        <p><strong>Combined Score:</strong> ${
            scores.combined_score * 100: .2f}%</p>
        ${
            scores.common_skills && scores.common_skills.length > 0 ?
            '<p><strong>Common Skills Found:</strong>{scores.common_skills.join(',
            ')}</p>' :
            '<p><strong>No specific skills from Job descrition in resume.</p>'}
    `;
      } catch (e) {
        scoreResultDiv.textContent = ` Error getting score: $ {e}`;
        console.error('Fetch error: ', e)
      }
    })
