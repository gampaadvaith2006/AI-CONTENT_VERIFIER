import os
import re
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# ---------------------------------------------------------
# VERITAS AI - FREE LIVE WEB VERIFICATION
# ---------------------------------------------------------

load_dotenv()

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

# Optional AI model.
# The live-web system below does NOT completely depend on it.
OPENROUTER_MODEL = "openrouter/free"

MAX_TOKENS = 350


# ---------------------------------------------------------
# TRUSTED SOURCES
# ---------------------------------------------------------

TRUSTED_DOMAINS = [
    "nasa.gov",
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "who.int",
    "un.org",
    "noaa.gov",
    "npr.org",
    "nytimes.com",
    "theguardian.com",
    "gov.uk",
    "whitehouse.gov",
    "europa.eu",
    "isro.gov.in",
]


# ---------------------------------------------------------
# TEXT HELPERS
# ---------------------------------------------------------

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def words(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    stop_words = {
        "the", "a", "an", "and", "or", "of", "to",
        "in", "on", "for", "with", "is", "are",
        "was", "were", "has", "have", "had", "that",
        "this", "it", "as", "by", "from", "at",
        "be", "been", "after", "before", "into",
        "about", "according", "says", "said"
    }

    return {
        word for word in text.split()
        if len(word) >= 3 and word not in stop_words
    }


def similarity(text1, text2):
    a = words(text1)
    b = words(text2)

    if not a or not b:
        return 0

    common = a.intersection(b)

    return len(common) / max(1, min(len(a), len(b)))


def get_domain(url):
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return ""


def is_trusted(url):
    domain = get_domain(url)

    for trusted in TRUSTED_DOMAINS:
        if domain == trusted or domain.endswith("." + trusted):
            return True

    return False


# ---------------------------------------------------------
# GOOGLE NEWS LIVE SEARCH
# ---------------------------------------------------------

def search_google_news(query):
    """
    Free live web search using Google News RSS.

    No Google API key is required.
    """

    encoded_query = urllib.parse.quote(query)

    rss_url = (
        "https://news.google.com/rss/search?"
        + "q="
        + encoded_query
        + "&hl=en-IN&gl=IN&ceid=IN:en"
    )

    try:
        request = urllib.request.Request(
            rss_url,
            headers={
                "User-Agent": "Mozilla/5.0 VERITAS-AI"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read()

        root = ET.fromstring(data)

        results = []

        for item in root.findall(".//item")[:10]:

            title_element = item.find("title")
            link_element = item.find("link")
            pub_element = item.find("pubDate")
            source_element = item.find("source")

            title = (
                title_element.text.strip()
                if title_element is not None and title_element.text
                else ""
            )

            link = (
                link_element.text.strip()
                if link_element is not None and link_element.text
                else ""
            )

            published = (
                pub_element.text.strip()
                if pub_element is not None and pub_element.text
                else ""
            )

            source_name = (
                source_element.text.strip()
                if source_element is not None and source_element.text
                else ""
            )

            if title and link:
                results.append({
                    "title": title,
                    "url": link,
                    "published": published,
                    "source": source_name
                })

        return results

    except Exception as error:
        print("Google News search error:", error)
        return []


# ---------------------------------------------------------
# CREATE SEARCH QUERIES
# ---------------------------------------------------------

def create_search_queries(news):

    cleaned = clean_text(news)

    queries = []

    # Full claim
    queries.append(cleaned[:250])

    # Remove common filler
    simplified = re.sub(
        r"\b(according to|reportedly|breaking|exclusive|claims|claim)\b",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    simplified = re.sub(r"\s+", " ", simplified).strip()

    if simplified and simplified != cleaned:
        queries.append(simplified[:250])

    return queries


# ---------------------------------------------------------
# LIVE VERIFICATION
# ---------------------------------------------------------

def verify_with_web(news):

    print("----------------------------------------")
    print("VERITAS AI")
    print("Free live web verification started...")
    print("----------------------------------------")

    all_results = []

    queries = create_search_queries(news)

    for query in queries:

        results = search_google_news(query)

        for result in results:

            duplicate = False

            for existing in all_results:
                if existing["url"] == result["url"]:
                    duplicate = True
                    break

            if not duplicate:
                all_results.append(result)

    if not all_results:

        return {
            "prediction": "UNCERTAIN",
            "confidence": 50,
            "explanation": (
                "No recent matching news sources were found "
                "through the live web search. The claim could "
                "not be independently verified."
            ),
            "source_name": "",
            "source_url": "",
            "source_status": "not_found"
        }

    # -----------------------------------------------------
    # Score search results
    # -----------------------------------------------------

    scored = []

    for result in all_results:

        score = similarity(news, result["title"])

        if is_trusted(result["url"]):
            score += 0.20

        scored.append({
            **result,
            "score": score
        })

    scored.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    best = scored[0]

    trusted_matches = [
        result
        for result in scored
        if is_trusted(result["url"]) and result["score"] >= 0.20
    ]

    strong_matches = [
        result
        for result in scored
        if result["score"] >= 0.35
    ]

    # -----------------------------------------------------
    # LIKELY REAL
    # -----------------------------------------------------

    if trusted_matches and best["score"] >= 0.45:

        confidence = 85

        if len(trusted_matches) >= 2:
            confidence = 92

        explanation = (
            "Live web verification found matching reporting from "
            "a recognized news or official source. The claim appears "
            "consistent with currently available reporting."
        )

        return {
            "prediction": "LIKELY REAL",
            "confidence": confidence,
            "explanation": explanation,
            "source_name": (
                best["source"]
                if best["source"]
                else get_domain(best["url"])
            ),
            "source_url": best["url"],
            "source_status": "verified",
            "verified_results": scored[:5]
        }

    # -----------------------------------------------------
    # POSSIBLY REAL
    # -----------------------------------------------------

    if strong_matches:

        return {
            "prediction": "LIKELY REAL",
            "confidence": 75,
            "explanation": (
                "Live web search found reporting that appears to "
                "match the claim. However, the available evidence "
                "is not strong enough for high-confidence verification."
            ),
            "source_name": (
                best["source"]
                if best["source"]
                else get_domain(best["url"])
            ),
            "source_url": best["url"],
            "source_status": "matched",
            "verified_results": scored[:5]
        }

    # -----------------------------------------------------
    # NO STRONG MATCH
    # -----------------------------------------------------

    return {
        "prediction": "UNCERTAIN",
        "confidence": 50,
        "explanation": (
            "Live web search found news results, but they did not "
            "closely match the claim enough to verify it. Treat the "
            "claim cautiously and check the source directly."
        ),
        "source_name": (
            best["source"]
            if best["source"]
            else get_domain(best["url"])
        ),
        "source_url": best["url"],
        "source_status": "weak_match",
        "verified_results": scored[:5]
    }


# ---------------------------------------------------------
# OPTIONAL OPENROUTER AI
# ---------------------------------------------------------

def ask_openrouter(news, web_results):

    if not OPENROUTER_API_KEY:
        return None

    prompt = f"""
You are a media-literacy assistant.

Analyze this news claim:

{news}

Live web search results:

{json.dumps(web_results[:5], ensure_ascii=False)}

Return ONLY valid JSON:

{{
  "prediction": "LIKELY REAL",
  "confidence": 80,
  "explanation": "short explanation"
}}

Allowed prediction values:
LIKELY REAL
LIKELY FAKE
UNCERTAIN

Do not invent sources.
Do not invent URLs.
"""

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.1
    }

    try:

        body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + OPENROUTER_API_KEY,
                "HTTP-Referer": "http://127.0.0.1:5000",
                "X-Title": "VERITAS AI"
            },
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            response_data = response.read().decode("utf-8")

        data = json.loads(response_data)

        choices = data.get("choices", [])

        if not choices:
            return None

        message = choices[0].get("message", {})

        content = message.get("content")

        if not content:
            return None

        # Sometimes models wrap JSON in ```json
        content = content.strip()

        content = re.sub(
            r"^```json\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        parsed = json.loads(content)

        return parsed

    except Exception as error:

        print("Optional OpenRouter error:", error)

        return None


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------
# PREDICT
# ---------------------------------------------------------

@app.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json(silent=True) or {}

        news = data.get("news", "")

        if not isinstance(news, str):
            news = str(news)

        news = news.strip()

        if not news:

            return jsonify({
                "error": "Please enter some news text."
            }), 400

        if len(news) > 5000:
            news = news[:5000]

        # -------------------------------------------------
        # LIVE WEB VERIFICATION
        # -------------------------------------------------

        web_result = verify_with_web(news)

        # -------------------------------------------------
        # OPTIONAL AI
        # -------------------------------------------------

        ai_result = ask_openrouter(
            news,
            web_result.get("verified_results", [])
        )

        # If AI worked, use it only when it gives a valid result.
        if ai_result:

            prediction = ai_result.get(
                "prediction",
                web_result["prediction"]
            )

            confidence = ai_result.get(
                "confidence",
                web_result["confidence"]
            )

            explanation = ai_result.get(
                "explanation",
                web_result["explanation"]
            )

            # Never allow AI to invent the source.
            source_name = web_result.get(
                "source_name",
                ""
            )

            source_url = web_result.get(
                "source_url",
                ""
            )

        else:

            prediction = web_result["prediction"]
            confidence = web_result["confidence"]
            explanation = web_result["explanation"]

            source_name = web_result.get(
                "source_name",
                ""
            )

            source_url = web_result.get(
                "source_url",
                ""
            )

        result = {
            "prediction": str(prediction).upper(),
            "confidence": int(confidence),
            "explanation": str(explanation),
            "source_name": source_name,
            "source_url": source_url,
            "source_status": web_result.get(
                "source_status",
                "unknown"
            ),
            "verification_method": "Live Web Search"
        }

        print("----------------------------------------")
        print("Prediction:", result["prediction"])
        print("Confidence:", result["confidence"])
        print("Source:", result["source_name"])
        print("URL:", result["source_url"])
        print("----------------------------------------")

        return jsonify(result), 200

    except Exception as error:

        print("SERVER ERROR:", error)

        return jsonify({
            "error": (
                "The verification system encountered an error. "
                "Please try again."
            )
        }), 500


# ---------------------------------------------------------
# STATUS
# ---------------------------------------------------------

@app.route("/status")
def status():

    return jsonify({
        "status": "online",
        "app": "VERITAS AI",
        "verification": "Live Web Search",
        "openrouter_available": bool(OPENROUTER_API_KEY),
        "time": datetime.now().isoformat()
    })


# ---------------------------------------------------------
# START SERVER
# ---------------------------------------------------------

if __name__ == "__main__":

    print("----------------------------------------")
    print(" VERITAS AI - Fake News Detector")
    print("----------------------------------------")

    if OPENROUTER_API_KEY:
        print("OpenRouter API key: FOUND")
        print("AI model: OPTIONAL - openrouter/free")
    else:
        print("OpenRouter API key: NOT FOUND")
        print("Running with FREE LIVE WEB VERIFICATION")

    print("Live Web Search: ENABLED")
    print("Server: http://127.0.0.1:5000")
    print("----------------------------------------")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )