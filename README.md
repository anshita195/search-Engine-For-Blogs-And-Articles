# A Niche Search Engine for Personal Blogs
This project is a complete, end-to-end prototype of a specialized search engine designed to index and search high-quality articles from personal blogs, actively filtering out corporate and marketing content.

The system uses a multi-stage machine learning pipeline for content classification and a hybrid search model combining lexical and semantic search to provide relevant results. The entire application is containerized with Docker for consistent and reproducible environments.

## Key Features
Intelligent Content Curation: Employs a four-stage classification funnel to ensure only high-quality personal blogs are indexed.

Hybrid Search: Combines fast, precise lexical (keyword) search with a powerful semantic (meaning-based) search as a fallback.

Modern Backend: Built with FastAPI for high-performance, asynchronous request handling and automatic API documentation.

Containerized: Fully containerized with Docker, ensuring a consistent and portable environment from development to production.

Offline Data Pipeline: Decouples the data processing and model training from the live serving API, ensuring robustness and resilience.

## System Architecture
The project's architecture is divided into two main components: an offline data pipeline for building the index and an online API for serving live queries.

### 1. Offline Data Pipeline
This is the data engineering core of the project, responsible for creating the search_index.json.

Harvesting: New candidate URLs are discovered by crawling the links on already-approved personal blogs (scripts/full_scale_harvest.py).

Classification Funnel: Each candidate URL is passed through a four-stage classification pipeline to determine its quality:

Domain Filter: A fast, rule-based check on the URL string.

Structural Heuristics: An analysis of the page's HTML structure using BeautifulSoup.

TF-IDF Classifier: A Scikit-learn model that classifies based on keyword statistics.

Embedding Classifier: A Sentence Transformer model that classifies based on semantic meaning.

Index Creation: Documents that pass the funnel are added to the final search index.

### 2. Online Serving API
This is the real-time component that handles user search queries.

Loading: The FastAPI server starts and loads all necessary data into memory, including the search index and all pre-computed ML models and embeddings.

Hybrid Search: User queries are handled by a hybrid search strategy:

First, a fast lexical search is performed using an in-memory inverted index.

If that fails to find sufficient results, the system falls back to a semantic search, which uses cosine similarity to find the most relevant documents by meaning.

Caching: An in-memory LRU Cache stores the results of recent queries to ensure fast responses for popular terms.

## Getting Started
You can run this project using either Docker (recommended for consistency) or a local Python environment.

Prerequisites
Python 3.9+

Docker and Docker Compose (for the Docker method)

### 1. Using Docker (Recommended)
This is the simplest and most reliable way to run the application.

#### 1. Clone the repository
git clone [https://github.com/anshita195/search-Engine-For-Blogs-And-Articles.git](https://github.com/anshita195/search-Engine-For-Blogs-And-Articles.git)
cd search-Engine-For-Blogs-And-Articles

#### 2. Build and run the container
docker-compose up --build

The application will be available at http://localhost:8000.

### 2. Using a Local Python Environment
#### 1. Clone the repository and navigate into it
git clone [https://github.com/anshita195/search-Engine-For-Blogs-And-Articles.git](https://github.com/anshita195/search-Engine-For-Blogs-And-Articles.git)
cd search-Engine-For-Blogs-And-Articles

#### 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate
#### On Windows, use: venv\Scripts\activate

#### 3. Install the dependencies
pip install -r requirements.txt

#### 4. Run the application
#### The server will run on the port specified by the PORT environment variable,
#### or 8000 if not set.
python api/main.py

## Running the Data Pipeline Scripts
The machine learning models are created and managed by scripts in the /scripts directory. The prototype_embeddings.pkl is included, but the TF-IDF models must be generated locally.

### Training the Models
Before running the classifiers for the first time, you must generate the model artifacts from the prototype dataset.

#### Ensure your virtual environment is active and dependencies are installed

#### 1. Train the TF-IDF model and vectorizer
python scripts/train_tfidf.py

#### 2. (Optional) Re-compute the prototype embeddings for the semantic classifier
python scripts/compute_embeddings.py

These commands will generate the necessary .pkl files in the /models directory.

## API Endpoints
Once the server is running, you can access the interactive API documentation at http://localhost:8000/docs. Key endpoints include:

GET /: Serves the main search UI.

GET /api/search: The main hybrid search endpoint.

GET /api/lexical_search: Performs only a keyword search.

GET /api/semantic_search: Performs only a semantic search.
