# Stigmergic Hospital Swarm OS

A software-only simulation platform that validates whether digital pheromones can coordinate hospital resources without a centralized dispatcher.

## Overview

This project simulates a hospital environment where agents (nurses, doctors, etc.) coordinate through digital pheromones to manage patient flow, resource allocation, and emergency response.

## Features

- Synthetic patient generation with various disease scenarios
- Digital pheromone engine for agent communication
- Swarm agents (Nurse, Doctor, ICU, Lab, Pharmacy, Ambulance) that make autonomous decisions
- Hospital digital twin with real-time graph representation
- Analytics dashboard for monitoring throughput, wait times, and resource utilization
- Stress testing capabilities for up to 10,000+ simulated patients

## Technology Stack

- **Frontend**: Next.js, React, TypeScript, TailwindCSS, React Flow, D3.js
- **Backend**: FastAPI (Python 3.12)
- **Agent Framework**: LangGraph
- **Graph Database**: Neo4j with GraphRAG
- **Event Layer**: Redis Streams
- **AI Integration**: Llama 3.1, Qwen 2.5 Coder via Ollama
- **Data Generation**: Faker, NumPy, Pandas, SMOTE
- **DevOps**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (for frontend development)
- Python 3.12 (for backend development)

### Running the Application

1. Clone the repository
2. Navigate to the project directory
3. Start the services using Docker Compose:

```bash
cd hospital_swarm
docker-compose up --build
```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

- `backend/`: FastAPI application
- `frontend/`: Next.js application
- `infra/`: Infrastructure configurations (Docker, etc.)
- `docs/`: Documentation files
- `scripts/`: Utility scripts

## Implementation Plan

See [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for detailed phased implementation approach.

## Future Work

- Real IoT/wearable device integration (planned for V2)
- FHIR/HL7 integration for EHR connectivity
- Multi-hospital coordination capabilities
- Advanced AI-driven predictive analytics

## License

This project is licensed under the MIT License.# Stigmergic-Hospital
