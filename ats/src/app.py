from flask import Flask, request, jsonify
from flask_cors import CORS

# import methods from class ResumeScorrer
from ResumeScorer import TextProcessor, ResumeScorer 

app = Flask(__name__)
CORS(app)

@app.route('/score', methods=['POST'])
def get_score():
    """
    API Endpoint to receive both texts: job description and resume and return score
    """
    data = request.json
    if not data or 'job_description' not in data or 'resume_text' not in data:
        return jsonify({"error":"Invalid input. Provide both job description and resume"}), 400

    job_description = data['job_description']
    resume_text = data['resume_text']
    language = data.get('language', 'english')

    try:
        # Instantiate TextProcessor and ResumeScorer
        text_processor_instance = TextProcessor(language=language)
        scorer_instance = ResumeScorer(text_processor=text_processor, language = text_processor_instance.stop_words_lang)
        
        score = scorer_instance.calculate_score(job_description, resume_text)

        return jsonify({"score": score})

    except Exception as e:
        print(f"An error occurred during score calculation: {e}")
        # error message for Node server - UI
        return jsonify({"error": "An error occurred. Check server logs"}), 500

if __name__ == "__main__":
    app.run(debug=True)
