# Personal Blog Search Engine 🚀

A sophisticated search engine that discovers and indexes genuine personal blogs, filtering out corporate content to provide authentic, first-hand experiences and insights.

## 🎯 Problem Statement

In today's web, finding authentic personal voices is increasingly difficult. Search results are dominated by SEO-optimized corporate content, making it hard to discover genuine personal experiences, learnings, and stories. This project bridges that gap by building a specialized search engine that identifies and indexes only personal blogs.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Crawler   │───▶│  ML Classifier  │───▶│  Search Index   │
│                 │    │                 │    │                 │
│ • URL Discovery │    │ • Personal vs   │    │ • FastAPI       │
│ • Content       │    │   Corporate     │    │ • Semantic      │
│   Extraction    │    │ • Confidence    │    │   Search        │
└─────────────────┘    │   Scoring       │    │ • Hybrid        │
                       └─────────────────┘    │   Ranking       │
                                              └─────────────────┘
```

## ✨ Key Features

- **🎯 High-Precision Classification**: ML pipeline achieves 85%+ precision in identifying personal blogs
- **🧠 Semantic Search**: Sentence transformers for context-aware search results
- **⚡ Fast Performance**: Sub-200ms search latency with hybrid keyword + semantic ranking
- **💰 Cost Optimized**: Zero LLM API costs using local ML models
- **📊 Quality Metrics**: Comprehensive validation and monitoring
- **🐳 Production Ready**: Dockerized deployment with health checks

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd searchEngine

# Start the search engine
docker-compose up --build

# Access the search interface
open http://localhost:8001
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the search engine
python api/main.py

# Access at http://localhost:8001
```

### Deploy to Cloud (Production)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Railway, Render, or Vercel.

**Live Demo**: [Coming soon - deploy to get your URL!]

## 📊 Current Status

- **📈 Index Size**: 378+ classified personal blogs
- **🎯 Classification Precision**: 85%+ (validated)
- **⚡ Search Latency**: <200ms average
- **🌐 Domains Covered**: 47+ unique personal blog domains

## 🔍 Search API

### Basic Search
```bash
GET /api/search?q=programming
```

### Semantic Search
```bash
GET /api/search?q=programming&use_semantic=true
```

### Response Format
```json
{
  "query": "programming",
  "results": [...],
  "total_results": 23,
  "search_time_ms": 45.2,
  "semantic_used": true
}
```

## 🛠️ Technical Stack

- **Backend**: FastAPI, Python 3.9
- **ML**: Sentence Transformers, Scikit-learn
- **Crawling**: Scrapy, BeautifulSoup
- **Search**: Hybrid keyword + semantic ranking
- **Deployment**: Docker, Docker Compose
- **Monitoring**: Health checks, performance metrics

## 📈 Performance Metrics

### Classification Pipeline
- **Throughput**: 50+ pages/hour
- **Accuracy**: 85%+ precision
- **Cost**: $0 (local models only)

### Search Performance
- **Average Latency**: 45ms
- **Semantic Search**: 120ms
- **Index Size**: 378 documents

## 🔬 Quality Validation

Run quality validation to assess classification accuracy:

```bash
# Generate quality report
python scripts/validate_quality.py report

# Manual validation (sample 50 blogs)
python scripts/validate_quality.py
```

## 🚀 Advanced Features

### Semantic Search
Uses sentence transformers for context-aware search:
- Combines keyword and semantic similarity
- Handles synonyms and related concepts
- Improves relevance for complex queries

### Hybrid Ranking
- Keyword matching for exact results
- Semantic similarity for context
- Confidence scoring for quality

### Production Features
- Docker containerization
- Health check endpoints
- Performance monitoring
- Automated testing

## 📝 API Documentation

### Endpoints

#### `GET /api/search`
Search for personal blogs with optional semantic ranking.

**Parameters:**
- `q` (required): Search query
- `use_semantic` (optional): Enable semantic search (default: false)
- `limit` (optional): Number of results (default: 10)

#### `GET /api/health`
Health check endpoint for monitoring.

#### `GET /`
Web interface for interactive search.

## 🎯 Future Roadmap

- [ ] Scale to 10,000+ blogs
- [ ] Multi-language support
- [ ] User personalization
- [ ] Advanced analytics dashboard
- [ ] Distributed crawling
- [ ] Real-time indexing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🏆 Impact

This project demonstrates:
- **ML Engineering**: Building production ML pipelines
- **System Design**: Scalable search architecture
- **Quality Assurance**: Validation and monitoring
- **Cost Optimization**: Efficient resource usage
- **User Experience**: Intuitive search interface

Perfect for showcasing technical skills in ML, web development, and system design for 2025 job applications! 