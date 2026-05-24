import os
import json
import base64
import traceback
import requests as http_requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SAMBANOVA_API_KEY = os.environ.get("SAMBANOVA_API_KEY", "")
YELP_API_KEY = os.environ.get("YELP_API_KEY", "")

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"
SAMBANOVA_MODEL = "Meta-Llama-3.3-70B-Instruct"

groq_client = None
sambanova_client = None

if GROQ_API_KEY:
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

if SAMBANOVA_API_KEY:
    sambanova_client = OpenAI(api_key=SAMBANOVA_API_KEY, base_url="https://api.sambanova.ai/v1")

SYSTEM_PROMPT = """You are Legalaize, an AI legal guidance platform. You give direct, actionable legal guidance.

RESPONSE STYLE:
1. Be straightforward and specific. Give clear answers, not vague generalities.
2. State what the law says, what the user's rights are, and what steps to take. Do not hedge excessively.
3. Use plain language. Skip legal jargon unless explaining a specific term.
4. Do NOT add disclaimers like "I'm not a lawyer", "consult an attorney", or "this is not legal advice" to your responses. The platform UI already displays this disclaimer permanently.
5. Do NOT use phrases like "generally speaking", "it depends", or "in most cases" as a way to avoid giving a direct answer. If something truly varies by jurisdiction, say which jurisdictions differ and how.
6. When analyzing documents, be specific: name the exact clauses that are problematic, explain why, and suggest exact changes.
7. Detect the user's language and respond in the same language.
8. Ask clarifying questions only when genuinely needed (e.g., jurisdiction matters for the answer).
9. Identify the relevant jurisdiction and applicable laws by name and statute number when possible.
10. Give concrete next steps with specific actions, deadlines, and who to contact.

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
2. The likely jurisdiction (city and state)
3. The type of attorney needed

Conversation:
{conversation}

{location_hint}

Respond in this exact JSON format only, no other text:
{{
  "legal_category": "...",
  "jurisdiction": "...",
  "attorney_type": "...",
  "search_term": "...",
  "location": "..."
}}

IMPORTANT location rules:
- search_term: a Yelp search query like "tenant rights attorney" or "employment lawyer"
- location: MUST be a specific city and state like "Los Angeles, CA" or "Houston, TX". NEVER use just a state name.
- If the user mentioned a specific city, use that city.
- If the user only mentioned a state, pick the largest city in that state (e.g., California → Los Angeles, CA; Texas → Houston, TX; New York → New York, NY).
- If no location is mentioned at all but a user_location hint is provided above, use that.
- As a last resort, use "New York, NY"."""

YELP_API_URL = "https://api.yelp.com/v3/businesses/search"


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


US_STATE_ABBREVS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}
US_STATE_ABBREVS_REV = {v: v for v in US_STATE_ABBREVS.values()}


def _extract_state_from_location(location):
    """Extract the state abbreviation from a location string like 'Miami, FL' or 'Florida'."""
    parts = [p.strip() for p in location.split(",")]
    for part in reversed(parts):
        upper = part.upper().strip()
        if upper in US_STATE_ABBREVS_REV:
            return upper
        lower = part.lower().strip()
        if lower in US_STATE_ABBREVS:
            return US_STATE_ABBREVS[lower]
    return ""


def _search_yelp(search_term, location, limit=20):
    """Search Yelp Fusion API for lawyers matching the query, filtered to the correct location."""
    if not YELP_API_KEY:
        return []

    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "term": search_term,
        "location": location,
        "categories": "lawyers",
        "sort_by": "distance",
        "limit": limit,
        "radius": 40000,
    }

    target_state = _extract_state_from_location(location)

    try:
        resp = http_requests.get(YELP_API_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        lawyers = []
        for biz in data.get("businesses", []):
            categories = [c["title"] for c in biz.get("categories", [])]
            location_parts = biz.get("location", {})
            city = location_parts.get("city", "")
            state = location_parts.get("state", "")

            if target_state and state.upper() != target_state.upper():
                continue

            jurisdiction = f"{city}, {state}" if city and state else city or state

            lawyers.append({
                "id": biz.get("id", ""),
                "name": biz.get("name", ""),
                "practice_area": ", ".join(categories),
                "jurisdiction": jurisdiction,
                "rating": biz.get("rating", 0),
                "review_count": biz.get("review_count", 0),
                "phone": biz.get("display_phone", ""),
                "website": biz.get("url", ""),
                "image_url": biz.get("image_url", ""),
                "address": ", ".join(location_parts.get("display_address", [])),
                "description": f"{biz.get('name', '')} — {', '.join(categories)} in {jurisdiction}. Rated {biz.get('rating', 'N/A')}/5 based on {biz.get('review_count', 0)} reviews.",
                "source": "yelp",
            })

        lawyers.sort(key=lambda x: x.get("rating", 0), reverse=True)
        return lawyers[:10]
    except Exception:
        traceback.print_exc()
        return []


@app.route("/api/match", methods=["POST"])
def match_lawyers():
    try:
        data = request.get_json()
        history = data.get("history", [])
        user_location = data.get("location", "")

        conversation = "\n".join(
            f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in history
        )

        location_hint = ""
        if user_location:
            location_hint = f"User's current location: {user_location}. Prefer attorneys near this location."

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": MATCH_PROMPT.format(
                conversation=conversation,
                location_hint=location_hint,
            )},
        ]
        response_text = _complete(messages)

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        ai_result = json.loads(response_text.strip())
        search_term = ai_result.get("search_term", ai_result.get("attorney_type", "lawyer"))
        location = user_location or ai_result.get("location", ai_result.get("jurisdiction", "New York, NY"))

        yelp_lawyers = _search_yelp(search_term, location)

        if yelp_lawyers:
            return jsonify({
                "lawyers": yelp_lawyers,
                "legal_category": ai_result.get("legal_category", ""),
                "jurisdiction": ai_result.get("jurisdiction", ""),
                "search_location": location,
                "source": "yelp",
            })

        return jsonify({
            "lawyers": [],
            "legal_category": ai_result.get("legal_category", ""),
            "jurisdiction": ai_result.get("jurisdiction", ""),
            "search_location": location,
            "source": "none",
        })
    except json.JSONDecodeError:
        return jsonify({"lawyers": [], "source": "none"})
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
        "yelp": bool(YELP_API_KEY),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
