'use strict';

document.getElementById('uploadForm')
    .addEventListener('submit', async (event) => {
      event.preventDefault();  // prevent default submission

      const tfidf_score = document.getElementById('tfidf_score');
      const skill_score = document.getElementById('skill_score');
      const combined_score = document.getElementById('combined_score');
      const common_skills = document.getElementById('common_skills');

      const banner = document.getElementById('result_banner');
      banner.textContent = 'Estimating Scores...';

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
        tfidf_score.innerText = (scores.tfidf_score * 100).toFixed(2);
        skill_score.innerText = (scores.skill_score * 100).toFixed(2);
        combined_score.innerText = (scores.combined_score * 100).toFixed(2);
        common_skills.innerText = scores.common_skills;
      } catch (e) {
        banner.textContent = ` Error getting score: ${e} `;
        console.error('Fetch error: ', e)
      }
    });
