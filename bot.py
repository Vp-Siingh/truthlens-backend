from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
from PIL import Image
import pytesseract
import requests

app = Flask(__name__)
CORS(app)

# =========================================
# TWILIO CONFIG
# =========================================

TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token

# =========================================
# MISLEADING CLAIM DATABASE
# =========================================

misleading_keywords = {

    "100% natural":
    "⚠️ '100% Natural' may be misleading because processed additives may still exist.",

    "clinically proven":
    "⚠️ 'Clinically Proven' detected without scientific references.",

    "doctor recommended":
    "⚠️ 'Doctor Recommended' claims may lack evidence.",

    "instant":
    "⚠️ Instant-result claims are scientifically questionable.",

    "boost immunity":
    "⚠️ Immunity boosting claims are often vague.",

    "fat burner":
    "⚠️ Fat burner claims are frequently exaggerated.",

    "miracle":
    "⚠️ Miracle cure claims are suspicious.",

    "guaranteed":
    "⚠️ Guaranteed-result claims may be misleading."
}

# =========================================
# TRUST SCORE
# =========================================

def calculate_trust_score(issue_count):

    score = 100 - (issue_count * 10)

    if score < 20:
        score = 20

    return score

# =========================================
# ANALYSIS ENGINE
# =========================================

def analyze_text(text):

    analysis = []

    text_lower = text.lower()

    for keyword, warning in misleading_keywords.items():

        if keyword in text_lower:
            analysis.append(warning)

    if len(analysis) == 0:
        analysis.append(
            "✅ No major misleading patterns detected."
        )

    trust_score = calculate_trust_score(
        len(analysis)
    )

    result = (
        f"📊 Trust Score: {trust_score}/100\n\n"
        + "\n\n".join(analysis)
    )

    return result

# =========================================
# WEBSITE API
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze_image():

    file = request.files["file"]

    image_path = "images/web_upload.jpg"

    file.save(image_path)

    extracted_text = pytesseract.image_to_string(
        Image.open(image_path)
    )

    result = analyze_text(extracted_text)

    return jsonify({
        "result": result
    })

# =========================================
# WHATSAPP BOT
# =========================================

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():

    response = MessagingResponse()
    msg = response.message()

    try:

        num_media = int(request.values.get("NumMedia", 0))

        if num_media > 0:

            media_url = request.values.get("MediaUrl0")
            content_type = request.values.get("MediaContentType0")

            if "image" in content_type:

                image_response = requests.get(
                    media_url,
                    auth=(account_sid, auth_token)
                )

                image_path = "images/uploaded_image.jpg"

                with open(image_path, "wb") as handler:
                    handler.write(image_response.content)

                extracted_text = pytesseract.image_to_string(
                    Image.open(image_path)
                )

                result = analyze_text(extracted_text)

                msg.body(
                    "🔍 TruthLens Analysis\n\n"
                    + result
                )

            else:

                msg.body(
                    "⚠️ Please upload image."
                )

        else:

            incoming_msg = request.values.get("Body", "")

            result = analyze_text(incoming_msg)

            msg.body(
                "🔍 TruthLens Analysis\n\n"
                + result
            )

    except Exception as e:

        print("ERROR:", str(e))

        msg.body(
            f"TruthLens error:\n{str(e)}"
        )

    return str(response)

# =========================================
# RUN SERVER
# =========================================

import os

port = int(os.environ.get("PORT", 5050))

app.run(host="0.0.0.0", port=port)