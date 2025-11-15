# Energy Optimization ROI Dashboard

An AI-powered operational tool for monitoring generator performance at remote oil sites. The system simulates IoT telemetry data, provides real-time visualization of generator metrics, and uses an AI agent to analyze power usage patterns and recommend cost-saving shutdown windows.

![ROI Dashboard](ROI%20Dashboard.png)
![Optimization Recommendation](Optimization%20Recommendation.png)

## Architecture

- **Backend**: FastAPI (Python 3.11) with LangGraph AI agent
- **Frontend**: Next.js 14+ with React and TypeScript
- **Database**: SQLite with Docker volume persistence
- **Real-time**: WebSocket for live telemetry streaming
- **AI Agent**: Custom LangGraph agent for optimization analysis

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- OpenAI API key (optional for AI features)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/YoussefMadkour/SmartGen-Energy-AI.git
cd oil-rig-energy-optimization
```

### 2. Environment Configuration

Copy the environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
# OpenAI Configuration (Required for AI optimization features)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5

# Application Configuration
FUEL_PRICE=1.50
IOT_SIMULATOR_INTERVAL=2
```

**Note**: The application will run without an OpenAI API key, but AI optimization features will not work.

### 3. Start Application

```bash
docker-compose up -d
```

This will build and start all services in the background:
- Backend API (FastAPI)
- Frontend Dashboard (Next.js)
- Database (SQLite with volume persistence)

**First time setup**: The backend will automatically seed 24 hours of historical telemetry data.

To view logs:
```bash
docker-compose logs -f
```

To stop the application:
```bash
docker-compose down
```

### 4. Access the Application

Once running, access the application at:

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Project Structure

```
oil-rig-energy-optimization/
├── backend/                      # FastAPI backend application
│   ├── agent_service.py          # LangGraph AI agent with 5 tools
│   ├── insights_service.py       # AI optimization endpoints
│   ├── metrics_service.py        # Telemetry data endpoints
│   ├── websocket_service.py      # WebSocket real-time streaming
│   ├── iot_simulator.py          # Mock IoT data generator
│   ├── database.py               # Database configuration & seeding
│   ├── models.py                 # SQLModel data models
│   ├── main.py                   # FastAPI application entry point
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Backend container configuration
├── frontend/                     # Next.js frontend application
│   ├── app/                      # Next.js 14 app directory
│   │   ├── page.tsx              # Main dashboard page
│   │   ├── layout.tsx            # Root layout
│   │   └── globals.css           # Global styles
│   ├── components/               # React components
│   │   ├── OptimizationPanel.tsx # AI recommendations panel
│   │   ├── PowerLoadChart.tsx    # Power load visualization
│   │   ├── FuelConsumptionChart.tsx # Fuel consumption chart
│   │   └── ROICard.tsx           # ROI metrics display
│   ├── lib/                      # Utility libraries
│   │   ├── api-client.ts         # REST API client
│   │   ├── websocket-client.ts   # WebSocket client
│   │   ├── config.ts             # Configuration
│   │   └── utils.ts              # Helper functions
│   ├── types/                    # TypeScript type definitions
│   │   └── index.ts              # Shared types
│   ├── package.json              # Node.js dependencies
│   ├── tsconfig.json             # TypeScript configuration
│   ├── tailwind.config.js        # Tailwind CSS configuration
│   ├── next.config.js            # Next.js configuration
│   └── Dockerfile                # Frontend container configuration
├── data/                         # Database volume (auto-created)
├── docker-compose.yml            # Multi-container orchestration
├── .env                          # Environment variables (create from .env.example)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── AGENT_ARCHITECTURE.md         # AI agent technical documentation
├── AGENT_IMPROVEMENTS.md         # Agent enhancement details
├── LANGCHAIN_FIX.md              # LangChain implementation notes
└── FINAL_STATUS.md               # Complete feature documentation
```

## Features

### 🚀 Real-time Monitoring
- Live telemetry data streaming via WebSocket (updates every 2 seconds)
- Current generator status (power load, fuel consumption, operational status)
- Historical data visualization with interactive charts
- Time range selection (6h, 12h, 24h, 7d)
- Automatic data persistence with SQLite

### 🤖 AI-Powered Optimization
- **LangGraph Agent** with 5 specialized tools:
  - Usage pattern analysis
  - Efficiency trend detection
  - Predictive usage forecasting (24-hour ahead)
  - Optimal shutdown window calculation
  - Cost savings estimation
- Natural language recommendations powered by GPT-5
- Memory persistence for conversation context
- Comprehensive error handling with retries

### 📊 Data Visualization
- Interactive power load charts (Recharts)
- Fuel consumption trends with time-series analysis
- Efficiency metrics and performance indicators
- Real-time updates without page refresh
- Responsive design with Tailwind CSS

### 🔧 Technical Implementation

- **Backend**: FastAPI with async/await patterns, WebSocket support
- **Frontend**: Next.js 14 with App Router, TypeScript, Tailwind CSS
- **Database**: SQLite with automatic seeding (24+ hours of data)
- **Real-time Communication**: WebSocket for live telemetry streaming
- **AI Integration**: LangGraph + LangChain with OpenAI GPT-5
- **Containerization**: Docker Compose for easy deployment

## API Documentation

- **REST API**: http://localhost:8000/docs (Swagger UI)
- **WebSocket**: `ws://localhost:8000/ws/telemetry` (real-time updates)
- **Key Endpoints**:
  - `POST /api/insights/optimize` - AI-powered optimization
  - `GET /api/metrics/history` - Historical telemetry data

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required for AI features |
| `OPENAI_MODEL` | OpenAI model | `gpt-5` |
| `FUEL_PRICE` | Diesel price per liter | `1.50` |

## Development Commands

```bash
# Start application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Troubleshooting

**Issue**: Docker daemon not running  
**Solution**: Start Docker Desktop

**Issue**: Port already in use  
**Solution**: Stop other services using ports 3000 or 8000

**Issue**: AI optimization not working  
**Solution**: Add your OpenAI API key to `.env` file

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

## Documentation & Testing

- **Architecture**: See [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md)
- **Testing**: 
  1. Open http://localhost:3000 and observe live metrics
  2. Click "Optimize Energy Usage" to test AI features
  3. Use API docs at http://localhost:8000/docs

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Ready to optimize your generator operations! 🚀**
