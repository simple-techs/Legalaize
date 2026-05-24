import os
import json
import base64
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SAMBANOVA_API_KEY = os.environ.get("SAMBANOVA_API_KEY", "")

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"
SAMBANOVA_MODEL = "Meta-Llama-3.3-70B-Instruct"

groq_client = None
sambanova_client = None

if GROQ_API_KEY:
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

if SAMBANOVA_API_KEY:
    sambanova_client = OpenAI(api_key=SAMBANOVA_API_KEY, base_url="https://api.sambanova.ai/v1")

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


def _complete(messages, model_override=None, vision=False):
    """Call Groq first; on rate-limit or failure, fall back to SambaNova."""
    last_error = None

    if groq_client:
        try:
            model = model_override or (GROQ_VISION_MODEL if vision else GROQ_MODEL)
            resp = groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_error = e
            error_str = str(e)
            if "429" not in error_str and "rate" not in error_str.lower():
                raise

    if sambanova_client:
        try:
            clean_messages = _strip_images(messages) if vision else messages
            resp = sambanova_client.chat.completions.create(
                model=SAMBANOVA_MODEL,
                messages=clean_messages,
                temperature=0.7,
                max_tokens=4096,
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_error = e
            raise

    if last_error:
        raise last_error
    raise RuntimeError("No AI provider configured. Set GROQ_API_KEY or SAMBANOVA_API_KEY.")


def _strip_images(messages):
    """Remove image content parts for providers that don't support vision."""
    cleaned = []
    for msg in messages:
        if isinstance(msg.get("content"), list):
            text_parts = [p["text"] for p in msg["content"] if p.get("type") == "text"]
            cleaned.append({**msg, "content": "\n".join(text_parts) + "\n[Image document was attached but cannot be processed by fallback model]"})
        else:
            cleaned.append(msg)
    return cleaned


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        message = request.form.get("message", "")
        history_raw = request.form.get("history", "[]")
        history = json.loads(history_raw)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[:-1]:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})

        user_content = message
        files = request.files.getlist("files")
        if files:
            file_descriptions = [f"[Attached file: {f.filename}]" for f in files]
            user_content += "\n\nAttached files: " + ", ".join(file_descriptions)

        messages.append({"role": "user", "content": user_content})

        response_text = _complete(messages)

        return jsonify({
            "response": response_text,
            "legal_brief": None,
        })
    except Exception as e:
        traceback.print_exc()
        if "429" in str(e) or "rate" in str(e).lower():
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
            image_data = base64.b64encode(file.read()).decode("utf-8")
            mime_type = file.content_type or "image/png"
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": ANALYZE_PROMPT.replace("{content}", "[Image document - see attached]")},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                ]},
            ]
            response_text = _complete(messages, vision=True)
            return jsonify({"analysis": response_text})

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

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ANALYZE_PROMPT.format(content=content[:10000])},
        ]
        response_text = _complete(messages)

        return jsonify({"analysis": response_text})
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

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": BRIEF_PROMPT.format(conversation=conversation)},
        ]
        response_text = _complete(messages)

        return jsonify({"brief": response_text})
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

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": MATCH_PROMPT.format(conversation=conversation)},
        ]
        response_text = _complete(messages)

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

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        response_text = _complete(messages)

        return jsonify({"content": response_text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    providers = []
    if groq_client:
        providers.append("groq")
    if sambanova_client:
        providers.append("sambanova")
    return jsonify({
        "status": "ok",
        "service": "legalaize",
        "providers": providers,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
