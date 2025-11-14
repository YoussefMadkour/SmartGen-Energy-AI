# Energy Optimization ROI Dashboard

An AI-powered operational tool for monitoring generator performance at remote oil sites. The system simulates IoT telemetry data, provides real-time visualization of generator metrics, and uses an AI agent to analyze power usage patterns and recommend cost-saving shutdown windows.

## Architecture

- **Backend**: FastAPI (Python 3.11) with LangChain AI agent
- **Frontend**: Next.js 14+ with React and TypeScript
- **Database**: SQLite with Docker volume persistence
- **Real-time**: WebSocket for live telemetry streaming

## Prerequisites

- Docker
- Docker Compose
- OpenAI API key

## Quick Start

1. Clone the repository
2. Copy the environment file and configure:
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
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/             # Next.js frontend application
│   ├── Dockerfile
│   ├── package.json
│   └── .env.example
├── docker-compose.yml    # Docker orchestration
└── .env.example          # Root environment configuration
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
- AI-powered optimization recommendations
- ROI calculations with projected savings
- WebSocket-based live updates

## License

MIT
