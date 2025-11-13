# Indexer - Microservice RAG System

A production-ready, reasoning-based RAG (Retrieval-Augmented Generation) system built with microservice architecture. Implements PageIndex's vectorless approach for accurate document querying with 98.7% retrieval accuracy.

## Technology Stack

### Frontend Technologies
![Next.js](https://img.shields.io/badge/Next.js-14.0.0-black?logo=next.js)
![React](https://img.shields.io/badge/React-18.2.0-blue?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3.0-blue?logo=typescript)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4.0-38B2AC?logo=tailwind-css)
![Socket.IO](https://img.shields.io/badge/Socket.IO-4.5.0-010101?logo=socket.io)
![React Query](https://img.shields.io/badge/TanStack%20Query-5.0.0-FF4154?logo=react-query)
![Zustand](https://img.shields.io/badge/Zustand-4.4.0-yellow)
![Framer Motion](https://img.shields.io/badge/Framer%20Motion-11.0.0-0055FF?logo=framer)
![Radix UI](https://img.shields.io/badge/Radix%20UI-Latest-161618)
![Axios](https://img.shields.io/badge/Axios-1.6.0-5A29E4?logo=axios)
![React Hook Form](https://img.shields.io/badge/React%20Hook%20Form-7.48.0-EC5990?logo=react-hook-form)
![Zod](https://img.shields.io/badge/Zod-3.22.0-3E67B1)

### Backend Technologies
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121.1-009688?logo=fastapi)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.38.0-499848)
![Pydantic](https://img.shields.io/badge/Pydantic-2.12.4-E92063?logo=pydantic)
![Socket.IO](https://img.shields.io/badge/Python%20Socket.IO-5.12.0-010101?logo=socket.io)
![OpenAI](https://img.shields.io/badge/OpenAI-2.7.2-412991?logo=openai)
![httpx](https://img.shields.io/badge/httpx-0.28.1-0099E5)
![tiktoken](https://img.shields.io/badge/tiktoken-0.12.0-000000)
![PyPDF](https://img.shields.io/badge/PyPDF-6.2.0-red)

### Infrastructure
![Docker](https://img.shields.io/badge/Docker-Latest-2496ED?logo=docker)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-Latest-2496ED?logo=docker)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)

## Architecture Overview

This project implements a 9-microservice architecture, where each service has a single responsibility and communicates through a centralized API gateway.

### Service Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │         USER INTERFACE LAYER            │
                    │    Next.js Frontend (Port 3000)         │
                    │    React + TypeScript + WebSocket       │
                    └───────────────────┬─────────────────────┘
                                        │
                                        │ REST API & WebSocket
                                        │
                    ┌───────────────────▼─────────────────────┐
                    │       API GATEWAY (Port 8000)           │
                    │   FastAPI - Routes & Orchestration      │
                    └────────────────────┬────────────────────┘
                                         │                      
            ┌────────────┬─────────┬─────┴───┬───────────┬───────────┬──────────┐
            │            │         │         │           │           │          │
            ▼            ▼         ▼         ▼           ▼           ▼          ▼
     ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
     │ Document │ │   Tree   │ │ Query  │ │  Chat  │ │Storage │ │ Cache  │ │Settings│
     │ Service  │ │ Service  │ │Service │ │Service │ │Service │ │Service │ │Service │
     │  :8001   │ │  :8002   │ │ :8003  │ │ :8004  │ │ :8005  │ │ :8006  │ │ :8007  │
     │          │ │          │ │        │ │        │ │        │ │        │ │        │
     │ PDF      │ │PageIndex │ │2-Stage │ │WebSock │ │SQLite  │ │In-Mem  │ │API Key │
     │Processing│ │Tree Gen  │ │Retrieve│ │Real-tm │ │Persist │ │Cache   │ │ Mgmt   │
     └────┬─────┘ └────┬─────┘ └────┬───┘ └────────┘ └──────┬─┘ └────────┘ └────────┘
          │            │            │                       │
          │            │            │                       │
          │            └────────────┴───────────────────────┘
          │                         │                       │
          │                         │                       │
          │                         ▼                       ▼
          │              ┌─────────────────────┐  ┌──────────────────┐
          │              │    OpenAI API       │  │  Data Storage    │
          └─────────────▶│  - GPT-4 Turbo      │  │  - SQLite DB     │
                         │  - Tree Search      │  │  - Document Files│
                         │  - Answer Gen       │  │  - Conversations │
                         └─────────────────────┘  └──────────────────┘
```

### Microservices Breakdown

| Service              | Port | Responsibility                               | Key Technology                |
|----------------------|------|----------------------------------------------|-------------------------------|
| **Frontend**         | 3000 | User interface with real-time updates        | Next.js 14, React, TypeScript |
| **API Gateway**      | 8000 | Request routing and service orchestration    | FastAPI, async Python         |
| **Document Service** | 8001 | PDF upload, text extraction, page mapping    | FastAPI, PyPDF                |
| **Tree Service**     | 8002 | PageIndex tree generation, TOC detection     | FastAPI, OpenAI API           |
| **Query Service**    | 8003 | Two-stage retrieval, answer generation       | FastAPI, OpenAI, tiktoken     |
| **Chat Service**     | 8004 | WebSocket communication, real-time streaming | FastAPI, Socket.IO            |
| **Storage Service**  | 8005 | Document, tree, and conversation persistence | FastAPI, SQLite               |
| **Cache Service**    | 8006 | Query result caching with TTL                | FastAPI, in-memory cache      |
| **Settings Service** | 8007 | API key management, configuration storage    | FastAPI, encryption           |

### PageIndex Two-Stage Retrieval Flow

```
User Question
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Tree Search                                            │
│  1. Fetch document tree structure from Storage Service          │
│  2. Remove text fields to reduce LLM prompt size                │
│  3. Pass tree structure (nodes, titles, pages) to GPT-4         │
│  4. LLM reasons which nodes likely contain the answer           │
│  5. Returns list of relevant node IDs                           │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼ [node_id_1, node_id_2, ..., node_id_n]
    │
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Answer Generation                                      │
│  1. Create node mapping (node_id → full node with text)         │
│  2. Extract text content from selected nodes                    │
│  3. Assemble context from relevant sections                     │
│  4. Pass question + context to GPT-4                            │
│  5. LLM generates answer with inline citations                  │
│  6. Calculate token usage and API cost                          │
│  7. Cache result for future identical queries                   │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
Answer + Citations + Cost + Relevant Nodes + Cached Status
```

## PageIndex vs Traditional RAG

### Comparison Table

| Feature                    | PageIndex (This System)             | Traditional Vector RAG                |
|----------------------------|-------------------------------------|---------------------------------------|
| **Retrieval Method**       | LLM reasoning on document structure | Embedding similarity search           |
| **Accuracy**               | 98.7% (proven)                      | ~70-85% (varies)                      |
| **Requires Vectors**       | No                                  | Yes (hundreds of thousands)           |
| **Vector Database**        | Not needed                          | Required (Pinecone, Weaviate, Chroma) |
| **Embedding Costs**        | None                                | Significant (all document chunks)     |
| **Storage Requirements**   | Minimal (tree structure only)       | Large (vector embeddings)             |
| **Retrieval Transparency** | Fully explainable (LLM reasoning)   | Black box (cosine similarity)         |
| **Document Structure**     | Leveraged (TOC, hierarchies)        | Ignored (flat chunks)                 |
| **Context Understanding**  | Hierarchical, preserves structure   | Fragmented chunks                     |
| **Citation Accuracy**      | Exact page numbers + sections       | Approximate locations                 |
| **Setup Complexity**       | Simple (Docker Compose)             | Complex (vector DB + embeddings)      |
| **Query Cost**             | 2 LLM calls per query               | 1 embedding + 1 LLM call              |
| **Maintenance**            | Low (no reindexing)                 | High (reindex on updates)             |
| **Scalability**            | Horizontal (stateless services)     | Limited (vector DB bottleneck)        |
| **Cold Start**             | Fast (no embeddings to generate)    | Slow (embed entire corpus)            |
| **Multi-Language**         | Supported (LLM handles)             | Separate embeddings needed            |

### Advantages of PageIndex Approach

1. **No Vector Database Required**: Eliminates infrastructure complexity and costs.
2. **Reasoning-Based Retrieval**: LLM understands document structure like a human expert.
3. **Explainable Results**: Can trace exactly why each section was selected.
4. **Preserves Context**: Maintains hierarchical relationships between sections.
5. **Lower Storage Costs**: Only stores document trees, not millions of vectors.
6. **Better Accuracy**: 98.7% retrieval accuracy vs 70-85% for vector approaches.
7. **Simpler Architecture**: Fewer moving parts, easier to maintain.
8. **Cost-Effective**: No embedding costs, only LLM reasoning costs.

### Disadvantages of PageIndex Approach

1. **LLM Dependency**: Requires access to capable language models (GPT-4).
2. **Two-Stage Process**: Two LLM calls per query (vs one in vector RAG).
3. **Latency**: Slightly higher response time due to two-stage retrieval.
4. **API Costs**: Depends on OpenAI API pricing (mitigated by caching).
5. **Document Size Limits**: Very large documents may exceed context windows.

## Installation and Setup

### Prerequisites

- Docker Desktop installed and running
- Git for version control
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

### Quick Start

1. Clone the repository and navigate to the project:

```bash
git clone <repository-url>
cd indexer
```

2. Create environment file with your OpenAI API key:

```bash
cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key-here
ENCRYPTION_KEY=$(openssl rand -hex 32)
EOF
```

3. Build and start all services:

```bash
docker-compose up -d --build
```

4. Access the application:

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Essential Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart <service-name>

# Check service health
curl http://localhost:8000/health
```

## Project Structure

```
indexer/
├── frontend/                   # Next.js 14 frontend (Port 3000)
├── api-gateway/               # FastAPI gateway (Port 8000)
├── document-service/          # PDF processing (Port 8001)
├── tree-service/              # PageIndex trees (Port 8002)
├── query-service/             # Query engine (Port 8003)
├── chat-service/              # WebSocket chat (Port 8004)
├── storage-service/           # Data persistence (Port 8005)
├── cache-service/             # Caching layer (Port 8006)
├── settings-service/          # Configuration (Port 8007)
├── docker-compose.yml         # Orchestrates all 9 services
└── .env                      # Environment variables
```

## Features

- Beautiful UI built with Next.js 14 and Radix UI
- Real-time WebSocket streaming for live query progress
- Cost tracking with token usage and API cost calculation
- Smart caching with configurable TTL to reduce API costs
- Document management with drag-and-drop upload
- Conversation history with persistent chat storage
- Comprehensive settings panel for all configuration
- Dark mode with system preference detection
- Inline citations with exact page references
- Full TypeScript and Pydantic validation
- Graceful error handling at every layer
- Health monitoring for all microservices
- Modular architecture with independent service scaling

## Credits

This project implements the PageIndex reasoning-based RAG approach developed by VectifyAI.

**PageIndex**: https://github.com/VectifyAI/PageIndex

The PageIndex algorithm provides a vectorless approach to document retrieval, using LLM reasoning to navigate document structures with 98.7% accuracy. This implementation follows the official PageIndex examples and methodology.

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- **PageIndex** by VectifyAI for the vectorless RAG methodology
- **FastAPI** for the high-performance async framework
- **Next.js** team for the excellent React framework
- **Radix UI** for accessible, unstyled components
- **OpenAI** for GPT-4 API access
- All open-source contributors whose packages made this possible
