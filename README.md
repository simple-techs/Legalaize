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
- **Backend**: Python Flask, Google Gemini API
- **Deployment**: Vercel (serverless)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- Google Gemini API key

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
GEMINI_API_KEY=your_key python server.py
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |

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
