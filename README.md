# Legalaize — AI Legal Guidance Platform

AI-powered legal guidance and attorney matching platform that makes legal understanding accessible to anyone.

## Features

- **AI Attorney Chatbot** — Ask legal questions conversationally, get plain-language guidance
- **Document Analysis** — Upload legal documents (PDF, DOCX, JPG, PNG) for AI analysis
- **Legal Brief Generator** — Auto-generate structured legal briefs from conversations
- **Attorney Matching** — Find lawyers matched to your specific legal needs
- **Legal Templates** — Pre-built, customizable legal document templates
- **Multilingual Support** — Interact in any language

## Tech Stack

- **Frontend**: React (CRA + CRACO), Tailwind CSS, Radix UI, Lucide Icons
- **Backend**: Python Flask, Groq API (primary) + SambaNova API (fallback)
- **AI Models**: Llama 3.3 70B (Groq), Llama 3.1 70B (SambaNova)
- **Deployment**: Vercel (serverless)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- Groq API key (free at https://console.groq.com/keys)
- SambaNova API key (free fallback at https://cloud.sambanova.ai/apis)

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
GROQ_API_KEY=your_key SAMBANOVA_API_KEY=your_key python server.py
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key (primary AI provider) | Yes |
| `SAMBANOVA_API_KEY` | SambaNova API key (fallback provider) | Recommended |

The backend uses Groq as the primary AI provider. When Groq rate limits are hit, it automatically falls back to SambaNova. Both offer free tiers.

## Project Structure

```
Legalaize/
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── contexts/    # React contexts
│   │   ├── pages/       # Page components
│   │   └── lib/         # Utilities
│   └── public/
├── backend/           # Flask backend
│   ├── server.py      # API server
│   └── requirements.txt
├── api/               # Vercel serverless functions
│   └── index.py
└── vercel.json        # Vercel configuration
```

## Disclaimer

Legalaize is an AI legal guidance tool, not a licensed lawyer. It does not practice law. Always discuss Legalaize output with a licensed attorney.
