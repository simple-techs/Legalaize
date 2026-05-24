import os
import json
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are Legalaize, an AI legal guidance assistant. You help users understand legal concepts, analyze documents, and provide general legal information.

IMPORTANT RULES:
1. You are NOT a licensed attorney and do not provide legal advice. You provide legal GUIDANCE and INFORMATION.
2. Always recommend consulting with a licensed attorney for specific legal matters.
3. Be clear, concise, and use plain language to explain legal concepts.
4. When analyzing documents, identify key clauses, risks, and missing protections.
5. When generating legal briefs, include: Case Summary, Timeline, Key Legal Issues, Jurisdiction, Important Facts, and Suggested Next Steps.
6. Detect the user's language and respond in the same language.
7. Ask clarifying questions when needed to better understand the user's situation.
8. Identify the relevant jurisdiction and legal category when possible.
9. Provide risk analysis when appropriate.
10. Never make definitive legal conclusions - use phrases like "generally," "typically," "in most jurisdictions."

You can help with:
- Tenant disputes, employment issues, contract confusion, immigration questions
- Business agreements, family disputes, and more
- Document analysis (leases, contracts, NDAs, etc.)
- Legal brief generation
- Attorney matching recommendations"""

BRIEF_PROMPT = """Based on the following conversation, generate a comprehensive legal brief with the following sections:

## Case Summary
A brief overview of the legal situation.

## Timeline
Key dates and events mentioned.

## Key Legal Issues
The main legal questions and concerns.

## Jurisdiction
The relevant jurisdiction(s) if mentioned.

## Important Facts
Critical facts that are relevant to the case.

## Relevant Laws & Regulations
Any applicable laws, statutes, or regulations.

## Risk Analysis
Potential risks and their likelihood.

## Suggested Next Steps
Recommended actions for the user.

## Attorney Recommendation
Type of attorney that would be best suited for this case.

Conversation:
{conversation}

Generate the legal brief now:"""

TEMPLATE_PROMPTS = {
    "nda": "Generate a professional Non-Disclosure Agreement (NDA) template with standard clauses including: parties, definition of confidential information, obligations, term, exclusions, remedies, and governing law. Include placeholder fields marked with [BRACKETS] for customization.",
    "employment": "Generate a professional Employment Agreement template with standard clauses including: position, compensation, benefits, work schedule, confidentiality, non-compete, termination, and governing law. Include placeholder fields marked with [BRACKETS] for customization.",
    "lease": "Generate a professional Residential Lease Agreement template with standard clauses including: parties, property description, term, rent, security deposit, maintenance, rules, termination, and governing law. Include placeholder fields marked with [BRACKETS] for customization.",
    "demand": "Generate a professional Demand Letter template with standard sections including: sender/recipient info, statement of facts, legal basis, specific demands, deadline, and consequences. Include placeholder fields marked with [BRACKETS] for customization.",
    "cease": "Generate a professional Cease and Desist Letter template with standard sections including: identification of the issue, description of harmful activity, legal basis, demand to cease, deadline, and potential legal action. Include placeholder fields marked with [BRACKETS] for customization.",
    "contractor": "Generate a professional Independent Contractor Agreement template with standard clauses including: scope of work, compensation, timeline, intellectual property, confidentiality, termination, and governing law. Include placeholder fields marked with [BRACKETS] for customization.",
    "service": "Generate a professional Service Agreement template with standard clauses including: services description, fees, payment terms, warranties, liability, termination, and governing law. Include placeholder fields marked with [BRACKETS] for customization.",
    "partnership": "Generate a professional Partnership Agreement template with standard clauses including: partners, contributions, profit sharing, management, decision making, dissolution, and governing law. Include placeholder fields marked with [BRACKETS] for customization.",
}

ANALYZE_PROMPT = """Analyze the following legal document and provide:

## Document Summary
A brief overview of what this document is and its purpose.

## Key Clauses
The most important clauses and their implications.

## Potential Risks
Any risks or concerns for the parties involved.

## Missing Protections
Important clauses or protections that may be missing.

## Recommendations
Suggestions for improving the document.

## Plain Language Explanation
A simple, easy-to-understand explanation of what this document means.

Document content:
{content}

Provide your analysis:"""

MATCH_PROMPT = """Based on the following conversation, identify:
1. The legal category (e.g., Employment Law, Tenant Rights, Contract Law, Immigration, Family Law, etc.)
2. The likely jurisdiction
3. The type of attorney needed

Conversation:
{conversation}

Respond in this exact JSON format:
{{
  "legal_category": "...",
  "jurisdiction": "...",
  "attorney_type": "...",
  "lawyers": [
    {{
      "id": 1,
      "name": "...",
      "practice_area": "...",
      "jurisdiction": "...",
      "rating": 4.8,
      "contact": "...@example.com",
      "website": "https://example.com",
      "description": "..."
    }}
  ]
}}

Generate 5 realistic but fictional attorney profiles that match the user's needs:"""


def get_model():
    return genai.GenerativeModel("gemini-2.0-flash")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        message = request.form.get("message", "")
        history_raw = request.form.get("history", "[]")
        history = json.loads(history_raw)

        model = get_model()

        gemini_history = []
        for msg in history[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        chat_session = model.start_chat(history=gemini_history)

        full_prompt = f"{SYSTEM_PROMPT}\n\nUser message: {message}"

        files = request.files.getlist("files")
        if files:
            file_descriptions = []
            for f in files:
                file_descriptions.append(f"[Attached file: {f.filename}]")
            full_prompt += "\n\nAttached files: " + ", ".join(file_descriptions)

        response = chat_session.send_message(full_prompt)

        return jsonify({
            "response": response.text,
            "legal_brief": None,
        })
    except Exception as e:
        traceback.print_exc()
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return jsonify({"error": "Rate limited. Please try again in a moment."}), 429
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400

        content = ""
        filename = file.filename.lower()

        if filename.endswith((".jpg", ".jpeg", ".png")):
            import base64
            image_data = base64.b64encode(file.read()).decode("utf-8")
            model = get_model()
            response = model.generate_content([
                ANALYZE_PROMPT.replace("{content}", "[Image document - see attached]"),
                {"mime_type": file.content_type, "data": image_data},
            ])
            return jsonify({"analysis": response.text})

        if filename.endswith(".pdf"):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(file)
                content = "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                content = "[PDF file uploaded - PyPDF2 not available for text extraction]"

        elif filename.endswith((".docx", ".doc")):
            try:
                import docx
                doc = docx.Document(file)
                content = "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                content = "[DOCX file uploaded - python-docx not available for text extraction]"
        else:
            content = file.read().decode("utf-8", errors="ignore")

        model = get_model()
        response = model.generate_content(ANALYZE_PROMPT.format(content=content[:10000]))

        return jsonify({"analysis": response.text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/brief", methods=["POST"])
def generate_brief():
    try:
        data = request.get_json()
        history = data.get("history", [])

        conversation = "\n".join(
            f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in history
        )

        model = get_model()
        response = model.generate_content(BRIEF_PROMPT.format(conversation=conversation))

        return jsonify({"brief": response.text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/match", methods=["POST"])
def match_lawyers():
    try:
        data = request.get_json()
        history = data.get("history", [])

        conversation = "\n".join(
            f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in history
        )

        model = get_model()
        response = model.generate_content(MATCH_PROMPT.format(conversation=conversation))

        response_text = response.text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
        return jsonify({"lawyers": result.get("lawyers", [])})
    except json.JSONDecodeError:
        return jsonify({"lawyers": []})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/template", methods=["POST"])
def generate_template():
    try:
        data = request.get_json()
        template_id = data.get("template_id", "")
        template_name = data.get("template_name", "")

        prompt = TEMPLATE_PROMPTS.get(template_id, f"Generate a professional {template_name} template with standard clauses. Include placeholder fields marked with [BRACKETS] for customization.")

        model = get_model()
        response = model.generate_content(prompt)

        return jsonify({"content": response.text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "legalaize"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
