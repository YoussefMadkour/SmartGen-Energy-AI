# Energy Optimization ROI Dashboard - Frontend

Next.js frontend application for the Energy Optimization ROI Dashboard.

## Tech Stack

- **Next.js 14+** with App Router
- **React 18+**
- **TypeScript**
- **TailwindCSS** for styling
- **Recharts** for data visualization
- **Axios** for API requests
- **WebSocket API** for real-time updates

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with metadata
│   ├── page.tsx           # Main dashboard page
│   └── globals.css        # Global styles with Tailwind
├── components/            # React components
│   ├── OptimizationPanel.tsx
│   └── ROICard.tsx
├── lib/                   # Utility functions and config
│   ├── config.ts          # App configuration
│   └── utils.ts           # Helper functions
├── types/                 # TypeScript type definitions
│   └── index.ts           # Core data types
├── .env.local            # Local environment variables
├── .env.example          # Environment variables template
├── next.config.js        # Next.js configuration
├── tailwind.config.js    # TailwindCSS configuration
├── postcss.config.js     # PostCSS configuration
└── tsconfig.json         # TypeScript configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

The application will be available at http://localhost:3000

### Environment Variables

Create a `.env.local` file with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Development

```bash
# Run development server with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

## Type Definitions

All TypeScript interfaces are defined in `types/index.ts`:

- `TelemetryReading` - Generator telemetry data
- `OptimizationResult` - AI optimization recommendations
- `ShutdownWindow` - Recommended shutdown period
- `Savings` - Projected cost savings
- `OptimizationParams` - Optimization request parameters

## Configuration

- **API URL**: Configured via `NEXT_PUBLIC_API_URL` environment variable
- **WebSocket URL**: Configured via `NEXT_PUBLIC_WS_URL` environment variable
- **Styling**: TailwindCSS with custom color palette in `tailwind.config.js`

## Docker

The frontend can be run in a Docker container:

```bash
docker build -t energy-dashboard-frontend .
docker run -p 3000:3000 energy-dashboard-frontend
```

Or use docker-compose from the root directory:

```bash
docker-compose up frontend
```
