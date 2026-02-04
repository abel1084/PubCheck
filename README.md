# PubCheck

AI-powered PDF design compliance checker for UNEP publications. Upload a PDF and get instant feedback on typography, margins, images, and required elements based on UNEP design guidelines.

## Features

- **PDF Analysis** - Extracts text, images, metadata, and margin measurements from uploaded PDFs
- **AI-Powered Review** - Uses Google Gemini to analyze documents against UNEP compliance rules
- **Document Type Detection** - Automatically identifies Factsheets, Policy Briefs, Working Papers, and Publications
- **Real-time Streaming** - Review results stream in real-time as the AI processes the document
- **Configurable Rules** - Customize compliance rules per document type
- **Report Generation** - Generate annotated PDF reports with findings

## Tech Stack

- **Backend**: Python 3.12, FastAPI, PyMuPDF
- **Frontend**: React 18, TypeScript, Ant Design, Vite
- **AI**: Google Gemini 2.5 Flash

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- Google API key from [AI Studio](https://aistudio.google.com/apikey)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/abel1084/PubCheck.git
   cd PubCheck
   ```

2. Create environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your credentials:
   ```
   GOOGLE_API_KEY=your-gemini-api-key
   PUBCHECK_PASSWORD=your-password
   ```

4. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   cd ..

   # Frontend
   cd frontend
   npm install
   cd ..
   ```

5. Start the application:
   ```bash
   python start.py
   ```

   This launches both the backend (port 8003) and frontend (port 5173), then opens your browser.

## Deployment (Railway)

The app is configured for one-click deployment to [Railway](https://railway.app).

### Deploy

1. Connect your GitHub repo to Railway
2. Railway will automatically detect the Dockerfile and build

### Environment Variables

Set these in Railway's dashboard under **Variables**:

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key from [AI Studio](https://aistudio.google.com/apikey) |
| `PUBCHECK_PASSWORD` | Yes | Password for app access |
| `AI_MODEL` | No | Override AI model (default: `gemini-2.5-flash`) |

Railway automatically provides the `PORT` variable.

## Project Structure

```
PubCheck/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── ai/              # Gemini AI client and review logic
│   │   ├── api/             # Upload endpoints
│   │   ├── auth/            # Session authentication
│   │   ├── config/          # Rules and settings
│   │   ├── services/        # PDF extraction, image processing
│   │   └── output/          # Report generation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks for API calls
│   │   └── types/           # TypeScript definitions
│   ├── package.json
│   └── vite.config.ts
├── Dockerfile               # Multi-stage build for Railway
├── railway.toml             # Railway configuration
├── start.py                 # Local development launcher
└── .env.example             # Environment template
```

## License

MIT
