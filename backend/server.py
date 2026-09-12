import os
import re
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

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_VISION_MODEL = os.environ.get("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")
SAMBANOVA_MODEL = os.environ.get("SAMBANOVA_MODEL", "Meta-Llama-3.3-70B-Instruct")

groq_client = None
sambanova_client = None

if GROQ_API_KEY:
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

if SAMBANOVA_API_KEY:
    sambanova_client = OpenAI(api_key=SAMBANOVA_API_KEY, base_url="https://api.sambanova.ai/v1")

SYSTEM_PROMPT = """You are Legalaize, an AI attorney platform. You give users real legal guidance as though you are their attorney advising them on their case.

MANDATORY FIRST STEP: When a user describes their legal issue, your FIRST response must ask for their location (state/city or country) before providing any legal guidance. Say something like: "To give you accurate legal guidance based on the laws in your area, I need to know — what state and city are you in?" Do NOT give substantive legal advice until you know their location. You may acknowledge their situation briefly, but do not list options or cite laws until location is confirmed.

AFTER LOCATION IS PROVIDED — RESPOND LIKE THEIR ATTORNEY:
1. Give them the exact laws that apply to their situation. Cite statute numbers, code sections, and local ordinances by name. Example: "Under California Labor Code § 1194, your employer is required to pay you the difference between what you were paid and the minimum wage."
2. Tell them exactly what to do. Not "consider consulting an attorney" — instead: "File a wage claim with the California Division of Labor Standards Enforcement (DLSE). Here is how to do it step by step."
3. Give them their legal rights plainly. Example: "Your immigration status does not affect your right to recover unpaid wages. The FLSA protects all workers regardless of immigration status."
4. Do NOT soften, hedge, or qualify your guidance. No "generally", "typically", "in most cases", "you may want to consider", "it's completely understandable." Give the answer directly.
5. Do NOT add disclaimers like "I'm not a lawyer", "consult an attorney", "this is not legal advice", or "I cannot provide legal advice." The platform UI handles disclaimers.
6. Do NOT express sympathy or emotional support. Skip phrases like "I'm so sorry to hear that" or "It's completely understandable." Get straight to the legal guidance.
7. When analyzing documents, name the exact clauses that are problematic, explain why they hurt the user, and provide the exact replacement language they should request.
8. Detect the user's language and respond in the same language.
9. Give deadlines and timelines: statute of limitations, filing deadlines, notice periods, response windows.
10. End every response with a "What to do right now" section — numbered steps with specific agencies, phone numbers, forms, and websites.

You can help with:
- Tenant disputes, employment issues, contract confusion, immigration questions
- Business agreements, family disputes, and more
- Document analysis (leases, contracts, NDAs, etc.)
- Legal brief generation
- Attorney matching recommendations"""

TASK_SYSTEM_PROMPT = """You are Legalaize, an AI attorney platform. Complete the requested legal drafting or analysis task directly and fully.
Do NOT ask the user questions, do NOT ask for their location, and do NOT add disclaimers such as "consult an attorney" or "this is not legal advice".
When analyzing documents, name the exact clauses that are problematic, explain why they hurt the user, and provide the exact replacement language to request.
Cite specific statutes and code sections when a jurisdiction is known. Detect the user's language and respond in the same language. Use Markdown formatting."""

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

YELP_CATEGORY_MAP = {
    "employment": "employmentlaw",
    "labor": "employmentlaw",
    "wage": "employmentlaw",
    "workplace": "employmentlaw",
    "wrongful termination": "employmentlaw",
    "discrimination": "employmentlaw",
    "harassment": "employmentlaw",
    "workers comp": "workerscomp",
    "workers compensation": "workerscomp",
    "immigration": "immigration",
    "visa": "immigration",
    "deportation": "immigration",
    "asylum": "immigration",
    "green card": "immigration",
    "tenant": "realestatelaw",
    "landlord": "realestatelaw",
    "eviction": "realestatelaw",
    "real estate": "realestatelaw",
    "property": "realestatelaw",
    "family": "familylaw",
    "divorce": "familylaw",
    "custody": "familylaw",
    "child support": "familylaw",
    "alimony": "familylaw",
    "personal injury": "personalinjurylaw",
    "accident": "personalinjurylaw",
    "injury": "personalinjurylaw",
    "malpractice": "personalinjurylaw",
    "criminal": "criminaldefense",
    "dui": "dwi",
    "dwi": "dwi",
    "bankruptcy": "bankruptcylaw",
    "debt": "bankruptcylaw",
    "business": "businesslaw",
    "contract": "businesslaw",
    "corporate": "businesslaw",
    "tax": "taxlaw",
    "estate planning": "estateplanning",
    "will": "estateplanning",
    "trust": "estateplanning",
    "probate": "estateplanning",
    "intellectual property": "iplaw",
    "patent": "iplaw",
    "trademark": "iplaw",
    "copyright": "iplaw",
}


def _get_yelp_category(search_term, legal_category):
    """Map search term and legal category to a specific Yelp law subcategory."""
    text = f"{search_term} {legal_category}".lower()
    for keyword, category in YELP_CATEGORY_MAP.items():
        if keyword in text:
            return category
    return "lawyers"


def _complete(messages, model_override=None, vision=False):
    """Call Groq first; on any failure (rate limit, retired model, outage), fall back to SambaNova."""
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
            content = _strip_thinking(resp.choices[0].message.content)
            if content:
                return content
            last_error = RuntimeError(f"Groq returned an empty response from {model}")
        except Exception as e:
            last_error = e
            traceback.print_exc()

    if sambanova_client:
        clean_messages = _strip_images(messages) if vision else messages
        resp = sambanova_client.chat.completions.create(
            model=SAMBANOVA_MODEL,
            messages=clean_messages,
            temperature=0.7,
            max_tokens=4096,
        )
        return _strip_thinking(resp.choices[0].message.content)

    if last_error:
        raise last_error
    raise RuntimeError("No AI provider configured. Set GROQ_API_KEY or SAMBANOVA_API_KEY.")


THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def _strip_thinking(text):
    """Remove reasoning-model <think>...</think> blocks from a completion."""
    if not text:
        return text
    cleaned = THINK_BLOCK_RE.sub("", text)
    if "<think>" in cleaned.lower() and "</think>" not in cleaned.lower():
        cleaned = re.split(r"<think>", cleaned, flags=re.IGNORECASE)[0]
    return cleaned.strip()


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


def _extract_text(file):
    """Extract plain text from an uploaded PDF, DOCX, or text file. Returns '' for images."""
    filename = (file.filename or "").lower()

    if filename.endswith((".jpg", ".jpeg", ".png")):
        return ""

    if filename.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            return "[PDF file uploaded - PyPDF2 not available for text extraction]"

    if filename.endswith((".docx", ".doc")):
        try:
            import docx
            doc = docx.Document(file)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return "[DOCX file uploaded - python-docx not available for text extraction]"

    return file.read().decode("utf-8", errors="ignore")


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
        for f in request.files.getlist("files"):
            text = _extract_text(f).strip()
            if text:
                user_content += f"\n\n--- Attached file: {f.filename} ---\n{text[:10000]}"
            else:
                user_content += f"\n\n[Attached file: {f.filename} (contents could not be read as text)]"

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

        filename = (file.filename or "").lower()

        if filename.endswith((".jpg", ".jpeg", ".png")):
            image_data = base64.b64encode(file.read()).decode("utf-8")
            mime_type = file.content_type or "image/png"
            messages = [
                {"role": "system", "content": TASK_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": ANALYZE_PROMPT.replace("{content}", "[Image document - see attached]")},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                ]},
            ]
            response_text = _complete(messages, vision=True)
            return jsonify({"analysis": response_text})

        content = _extract_text(file)
        if not content.strip():
            return jsonify({"error": "No readable text found in the document"}), 400

        messages = [
            {"role": "system", "content": TASK_SYSTEM_PROMPT},
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
        data = request.get_json(silent=True) or {}
        history = data.get("history", [])
        if not any(m.get("role") == "user" for m in history):
            return jsonify({"error": "Start a chat about your legal issue before generating a brief"}), 400

        conversation = "\n".join(
            f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in history
        )

        messages = [
            {"role": "system", "content": TASK_SYSTEM_PROMPT},
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


def _search_yelp(search_term, location, legal_category="", limit=20):
    """Search Yelp Fusion API for lawyers matching the query, filtered to the correct location."""
    if not YELP_API_KEY:
        return []

    yelp_category = _get_yelp_category(search_term, legal_category)

    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "term": search_term,
        "location": location,
        "categories": yelp_category,
        "sort_by": "best_match",
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
        data = request.get_json(silent=True) or {}
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
            {"role": "system", "content": TASK_SYSTEM_PROMPT},
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

        legal_category = ai_result.get("legal_category", "")
        yelp_lawyers = _search_yelp(search_term, location, legal_category)

        if not yelp_lawyers:
            yelp_lawyers = _search_yelp(search_term, location, "")

        if yelp_lawyers:
            return jsonify({
                "lawyers": yelp_lawyers,
                "legal_category": legal_category,
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
        data = request.get_json(silent=True) or {}
        template_id = data.get("template_id", "")
        template_name = data.get("template_name", "")

        prompt = TEMPLATE_PROMPTS.get(template_id, f"Generate a professional {template_name} template with standard clauses. Include placeholder fields marked with [BRACKETS] for customization.")

        messages = [
            {"role": "system", "content": TASK_SYSTEM_PROMPT},
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
