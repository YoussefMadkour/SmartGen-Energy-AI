# Energy Optimization ROI Dashboard

An AI-powered operational tool for monitoring generator performance at remote oil sites. The system simulates IoT telemetry data, provides real-time visualization of generator metrics, and uses an AI agent to analyze power usage patterns and recommend cost-saving shutdown windows.

## Architecture

- **Backend**: FastAPI (Python 3.11) with LangGraph AI agent
- **Frontend**: Next.js 14+ with React and TypeScript
- **Database**: SQLite with Docker volume persistence
- **Real-time**: WebSocket for live telemetry streaming
- **AI Agent**: Custom LangGraph agent for optimization analysis

## Prerequisites

- Docker
- Docker Compose
- OpenAI API key

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-username/oil-rig-energy-optimization.git
cd oil-rig-energy-optimization
```

### 2. Environment Configuration

Copy the environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
# Database Configuration
DATABASE_URL=sqlite:///data/telemetry.db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5

# Application Configuration
DIESEL_PRICE_PER_LITER=1.50
```

### 3. Start Application

```bash
docker-compose up --build
```

This will build and start all services (backend, frontend, database).

### 4. Access the Application

Once running, access the application at:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Project Structure

```
oil-rig-energy-optimization/
├── backend/                    # FastAPI backend application
│   ├── agent_service.py         # LangGraph AI agent implementation
│   ├── metrics_service.py       # REST API endpoints
│   ├── models.py             # Data models
│   ├── database.py          # Database configuration
│   ├── iot_simulator.py      # IoT data simulation
│   ├── websocket_service.py   # WebSocket handling
│   ├── main.py             # Application entry point
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile
├── frontend/                   # Next.js frontend application
│   ├── components/           # React components
│   │   ├── OptimizationPanel.tsx  # AI recommendations display
│   │   ├── PowerLoadChart.tsx    # Power load visualization
│   │   ├── FuelConsumptionChart.tsx # Fuel consumption visualization
│   │   └── ROICard.tsx          # ROI calculations
│   ├── pages/               # Next.js pages
│   │   └── index.tsx         # Main dashboard
│   ├── lib/                 # Utility libraries
│   │   ├── api-client.ts       # API client
│   │   └── websocket-client.ts # WebSocket client
│   ├── types/               # TypeScript type definitions
│   ├── next.config.js       # Next.js configuration
│   ├── package.json         # Node.js dependencies
│   ├── tsconfig.json        # TypeScript configuration
│   ├── Dockerfile
│   └── .env.local
├── docker-compose.yml           # Docker orchestration
├── .env.example               # Environment configuration template
├── .gitignore                 # Git ignore rules
├── AGENT_ARCHITECTURE.md    # AI agent documentation
├── AGENT_IMPROVEMENTS.md     # Agent enhancement documentation
└── README.md                   # This file
```

## Features

### 🚀 Real-time Monitoring
- Live telemetry data streaming via WebSocket
- Current generator status and metrics
- Historical data visualization with interactive charts
- Automatic data refresh every 5 seconds

### 🤖 AI-Powered Optimization
- Custom LangGraph agent analyzes usage patterns
- Identifies optimal shutdown windows for cost savings
- Provides natural language recommendations
- Calculates projected ROI and cost savings

### 📊 Data Visualization
- Interactive power load charts with time range selection
- Fuel consumption trends analysis
- Efficiency metrics and performance indicators
- Historical data export capabilities

### 🔧 Technical Implementation

- **Backend**: FastAPI with async/await patterns
- **Frontend**: React with TypeScript for type safety
- **Database**: SQLite with proper indexing for time-series data
- **Real-time Communication**: WebSocket for live updates
- **AI Integration**: LangGraph with OpenAI GPT-5 for intelligent analysis

## API Endpoints

### Metrics API
- `GET /api/metrics/history` - Retrieve historical telemetry data
- `GET /api/metrics/latest` - Get latest telemetry reading
- `POST /api/metrics/optimize` - Generate AI optimization recommendations

### WebSocket Endpoint
- `WS /ws/telemetry` - Real-time telemetry streaming

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///data/telemetry.db` |
| `OPENAI_API_KEY` | OpenAI API key | Required for AI features |
| `OPENAI_MODEL` | OpenAI model | `gpt-5` |
| `DIESEL_PRICE_PER_LITER` | Fuel cost per liter | `1.50` |

## Development

### Local Development

```bash
# Backend development
cd backend
python -m venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend development
cd frontend
npm install
npm run dev
```

### Production Deployment

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

## Getting Started

1. **Clone the repository**
2. **Configure your environment** (add OpenAI API key)
3. **Run `docker-compose up --build`**
4. **Access the dashboard** at http://localhost:3000
5. **Explore the API** at http://localhost:8000/docs

## Support

For issues, questions, or contributions:
- 📧 Create an issue in the GitHub repository
- 📧 Check the [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) for technical details
- 💬 Review the [AGENT_IMPROVEMENTS.md](AGENT_IMPROVEMENTS.md) for enhancement history

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Ready to optimize your generator operations! 🚀**
