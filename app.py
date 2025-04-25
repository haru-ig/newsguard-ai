import os
import re
import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

def fetch_article_text(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        return ' '.join([p.get_text() for p in paragraphs])
    except:
        return None

def summarize_text_with_openai(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful summarizer."},
            {"role": "user", "content": f"Summarize the following news article in 5 sentences:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content.strip()

def trustworthiness_score_with_openai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a critical media analyst."},
                {"role": "user", "content": f"Rate this news article's trustworthiness (0-100) with reasoning:\n\n{text}"}
            ]
        )
        reply = response.choices[0].message.content
        score_match = re.search(r'(\d{1,3})', reply)
        score = int(score_match.group(1)) if score_match else 50
        return score, reply.strip()
    except Exception as e:
        print("Error in trust scoring:", e)
        return 50, "Could not evaluate trustworthiness."

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form["url"]

        if not re.match(r'https?://', url):
            return render_template("index.html", error="Please enter a valid URL starting with http:// or https://")

        article_text = fetch_article_text(url)
        if not article_text:
            return render_template("index.html", error="Failed to extract article content. Please try another URL.")


        summary = summarize_text_with_openai(article_text)
        score, reasoning = trustworthiness_score_with_openai(article_text)

        return render_template('result.html', summary=summary, score=score, reasoning=reasoning, original=article_text)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
