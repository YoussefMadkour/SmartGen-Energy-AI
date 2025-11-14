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

1. Clone the repository
2. Copy environment file and configure:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your OpenAI API key
4. Start the application:
   ```bash
   docker-compose up --build
   ```
5. Access the dashboard at http://localhost:3000
6. API documentation available at http://localhost:8000/docs

## Project Structure

```
.
├── backend/              # FastAPI backend application
│   ├── agent_service.py    # LangGraph AI agent implementation
│   ├── metrics_service.py  # REST API endpoints
│   ├── models.py          # Data models
│   ├── database.py         # Database configuration
│   ├── iot_simulator.py    # IoT data simulation
│   ├── websocket_service.py # WebSocket handling
│   ├── main.py            # Application entry point
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/             # Next.js frontend application
│   ├── components/         # React components
│   │   └── OptimizationPanel.tsx  # AI recommendations display
│   ├── pages/             # Next.js pages
│   │   └── index.tsx      # Main dashboard
│   ├── next.config.js      # Next.js configuration
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile
├── docker-compose.yml    # Docker orchestration
├── .env.example          # Environment configuration template
└── AGENT_ARCHITECTURE.md # AI agent documentation
```

## Environment Variables

See `.env.example` for all available configuration options including:
- Database settings
- IoT simulation parameters
- Optimization parameters
- OpenAI API configuration

## Development

The Docker setup includes hot-reload for both backend and frontend:
- Backend changes are automatically reloaded by uvicorn
- Frontend changes trigger Next.js fast refresh

## Features

- Real-time generator telemetry monitoring
- Historical data visualization with interactive charts
- **AI-powered optimization recommendations** using LangGraph agent
- **Usage pattern analysis** with hourly breakdown
- **Optimal shutdown window calculation** with sliding window algorithm
- **Cost savings estimation** with daily and monthly projections
- **Natural language recommendations** from OpenAI GPT-4
- ROI calculations with projected savings
- WebSocket-based live updates

## AI Agent Implementation

The system uses a custom LangGraph agent with three specialized tools:

1. **Usage Pattern Analysis**: Analyzes historical telemetry data to identify consumption patterns
2. **Shutdown Window Calculation**: Implements sliding window algorithm to find optimal shutdown periods
3. **Savings Estimation**: Calculates projected cost savings based on fuel consumption

The agent follows a sequential workflow:
1. Analyze telemetry data to identify patterns
2. Calculate optimal shutdown windows based on low-usage periods
3. Generate natural language recommendations with cost savings projections

For detailed implementation information, see [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md).

## API Endpoints

### Metrics
- `GET /api/metrics/history` - Retrieve historical telemetry data
- `GET /api/metrics/latest` - Get latest telemetry reading
- `POST /api/metrics/optimize` - Generate AI optimization recommendations

### WebSocket
- `WS /ws/telemetry` - Real-time telemetry streaming

## License

MIT
