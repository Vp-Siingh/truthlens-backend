import os
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS

from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

# =========================================
# ENV VARIABLES
# =========================================

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY")

# =========================================
# MISLEADING CLAIM DATABASE
# =========================================

misleading_keywords = {

    "100% natural":
    "⚠️ '100% Natural' may be misleading because processed additives may still exist.",

    "clinically proven":
    "⚠️ 'Clinically Proven' detected without visible scientific references.",

    "scientifically proven":
    "⚠️ Scientific proof claims require proper study citations.",

    "doctor recommended":
    "⚠️ 'Doctor Recommended' claims may lack verifiable evidence.",

    "instant":
    "⚠️ Instant-result claims are often scientifically questionable.",

    "boost immunity":
    "⚠️ Immunity boosting claims are frequently vague and difficult to verify.",

    "fat burner":
    "⚠️ Fat burner marketing claims are often exaggerated.",

    "lose weight fast":
    "⚠️ Rapid weight loss claims may be misleading.",

    "limited offer":
    "⚠️ Limited-time urgency tactics detected.",

    "best in india":
    "⚠️ Superiority claims may lack measurable evidence.",

    "no side effects":
    "⚠️ 'No side effects' is a potentially misleading medical claim.",

    "chemical free":
    "⚠️ 'Chemical Free' is scientifically inaccurate marketing language.",

    "miracle":
    "⚠️ Miracle cure claims are highly suspicious.",

    "guaranteed":
    "⚠️ Guaranteed-result claims may be misleading."
}

# =========================================
# TRUST SCORE FUNCTION
# =========================================

def calculate_trust_score(issue_count):

    score = 100 - (issue_count * 10)

    if score < 20:
        score = 20

    return score

# =========================================
# OCR FUNCTION USING OCR.SPACE
# =========================================

def extract_text_from_image(image_path):

    payload = {
        'apikey': OCR_SPACE_API_KEY,
        'language': 'eng'
    }

    with open(image_path, 'rb') as f:

        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename': f},
            data=payload
        )

    result = response.json()

    try:

        extracted_text = result['ParsedResults'][0]['ParsedText']

    except Exception:

        extracted_text = ""

    return extracted_text

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
# WEBSITE IMAGE ANALYSIS API
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze_image():

    try:

        file = request.files["file"]

        image_path = "uploaded_image.jpg"

        file.save(image_path)

        extracted_text = extract_text_from_image(
            image_path
        )

        print("OCR TEXT:")
        print(extracted_text)

        result = analyze_text(
            extracted_text
        )

        return jsonify({
            "result": result,
            "ocr_text": extracted_text
        })

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# WHATSAPP BOT
# =========================================

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():

    response = MessagingResponse()

    msg = response.message()

    try:

        num_media = int(
            request.values.get("NumMedia", 0)
        )

        # =========================================
        # IMAGE MESSAGE
        # =========================================

        if num_media > 0:

            media_url = request.values.get("MediaUrl0")

            content_type = request.values.get(
                "MediaContentType0"
            )

            if "image" in content_type:

                image_response = requests.get(
                    media_url,
                    auth=(
                        TWILIO_ACCOUNT_SID,
                        TWILIO_AUTH_TOKEN
                    )
                )

                image_path = "whatsapp_upload.jpg"

                with open(image_path, "wb") as handler:

                    handler.write(
                        image_response.content
                    )

                extracted_text = extract_text_from_image(
                    image_path
                )

                result = analyze_text(
                    extracted_text
                )

                msg.body(
                    "🔍 TruthLens Analysis\n\n"
                    + result
                )

            else:

                msg.body(
                    "⚠️ Please upload an image."
                )

        # =========================================
        # TEXT MESSAGE
        # =========================================

        else:

            incoming_msg = request.values.get(
                "Body",
                ""
            )

            result = analyze_text(
                incoming_msg
            )

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
# ROOT ROUTE
# =========================================

@app.route("/")
def home():

    return {
        "status": "TruthLens backend is running"
    }

# =========================================
# RUN APP
# =========================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5050)