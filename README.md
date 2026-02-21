# DeepStock - Deep Stock Analysis

**Data First, AI Second** — Quantitative stock analysis across CN/US/HK markets.

DeepStock computes everything quantitatively first (financial ratios, technical indicators, sentiment scoring), then uses AI only for interpretation. Three analysis pillars run independently, each producing a scored result (0-100), before being merged and sent to AI for synthesis.

## Architecture

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Fundamental  │   │  Technical   │   │  Sentiment   │
│  Score: 0-100│   │  Score: 0-100│   │  Score: 0-100│
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                   │
       └──────────────────┼───────────────────┘
                          ▼
              ┌───────────────────────┐
              │  Composite Score      │
              │  = F×0.35 + T×0.35    │
              │    + S×0.30           │
              └───────────┬───────────┘
                          ▼
              ┌───────────────────────┐
              │  AI Synthesis         │
              │  (Interprets, does    │
              │   NOT calculate)      │
              └───────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 + FastAPI + SQLAlchemy |
| Frontend | React 19 + TypeScript + TailwindCSS + Vite |
| Charts | ECharts (K-line, financial, radar) |
| Database | SQLite |
| AI | Gemini / Claude / OpenAI (user selects) |
| Data: A-shares | AkShare |
| Data: US stocks | YFinance |
| Data: HK stocks | AkShare + YFinance fallback |
| News | Tavily API |

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env with your API keys

# Run
cd ..
python -m uvicorn app.main:app --reload --app-dir backend
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — enter a stock code (e.g., `AAPL`, `600519`, `00700`) and hit Analyze.

## API Keys

Set in `.env`:

| Key | Required | Purpose |
|-----|----------|---------|
| `GEMINI_API_KEY` | At least one AI key | Google Gemini for synthesis |
| `ANTHROPIC_API_KEY` | At least one AI key | Claude for synthesis |
| `OPENAI_API_KEY` | At least one AI key | GPT for synthesis |
| `TAVILY_API_KEY` | Optional | News/sentiment analysis |

## Analysis Pillars

### Fundamental (35% weight)
- Valuation: PE, PB, PS, PEG ratios
- Profitability: ROE, ROA, margins
- Growth: Revenue & profit growth YoY/QoQ
- Health: Debt/equity, current ratio, FCF

### Technical (35% weight)
- Trend: MA alignment, price position
- Momentum: RSI, MACD, KDJ signals
- Volume: Volume-price analysis, divergence detection
- Structure: Support/resistance levels, chip distribution
- Patterns: Candlestick pattern recognition

### Sentiment (30% weight)
- News sentiment: Keyword-based scoring (CN + EN)
- Event impact: Earnings, policy, insider activity
- Market attention: Article volume
- Source quality: Tiered source reliability

## Supported Markets

| Market | Code Format | Examples |
|--------|-------------|---------|
| A-shares (CN) | 6-digit number | `600519`, `300750` |
| US stocks | 1-5 letter ticker | `AAPL`, `NVDA`, `TSLA` |
| HK stocks | 5-digit number | `00700`, `09988` |
