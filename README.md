# Gutermann Product Q&A — Local RAG Agent

## 1. Project Overview

This project implements a local Retrieval-Augmented Generation (RAG) question-answering agent designed specifically for the supplied Gutermann water leak detection product knowledge base.

The system operates entirely locally and follows a clean pipeline:
- Reads the supplied Markdown knowledge base.
- Parses product and category information into distinct chunks.
- Creates semantic embeddings for the chunks.
- Retrieves relevant information for each user question.
- Selects the most relevant evidence through query-aware filtering.
- Sends the selected evidence to a local LLM.
- Generates a grounded answer based strictly on the retrieved context.
- Displays the final sources used to generate the answer.

The application runs through an interactive Python command-line interface (CLI).

---

## 2. Assessment Objective

The primary objective of this project is to build a runnable Python CLI RAG agent that ingests the supplied Markdown knowledge base once at startup, accurately retrieves relevant chunks for each query, and generates natural language answers using a local LLM while strictly avoiding unsupported claims.

The system is specifically designed to handle and answer the seven supplied assessment queries accurately.

---

## 3. Architecture

The agent follows this data flow architecture:

```text
Markdown Knowledge Base
        ↓
Markdown Parsing
        ↓
Product / Category Chunks
        ↓
SentenceTransformer Embeddings
        ↓
Hybrid Retrieval
(Semantic + Lexical)
        ↓
Candidate Ranking
        ↓
Query-aware Source Selection
        ↓
Grounded Prompt
        ↓
Local Ollama LLM
        ↓
Answer + Sources
```

Each stage is clearly separated in the code to ensure that retrieval, ranking, and generation can be debugged and optimized independently.

---

## 4. Technologies Used

- Python
- SentenceTransformers
- all-MiniLM-L6-v2
- NumPy
- scikit-learn
- Requests
- Ollama
- phi3:latest
- Markdown knowledge base

---

## 5. Retrieval Approach

The system uses a **hybrid retrieval approach** to balance conceptual understanding with exact technical keyword matching.

- **Semantic Similarity** is calculated using dense sentence embeddings (`all-MiniLM-L6-v2`).
- **Lexical Overlap** is calculated to help preserve exact technical and product terminology.

The Stage-1 retrieval score dynamically combines these metrics:
- 80% semantic similarity
- 20% lexical similarity

Retrieved candidates then undergo a second **query-aware source selection** stage. This is a rule-based, deterministic reranking step rather than a machine-learning trained reranker.

---

## 6. Query-aware Source Selection

Instead of blindly sending a fixed number of retrieved results (e.g., `top_k=5`) to the LLM, the system dynamically recognizes different query types and filters the final sources accordingly:

- **Direct questions:** Returns only the strongest relevant source (e.g., matching a specific feature to one product).
- **Comparison questions:** Detects explicitly mentioned product names and returns the relevant sources for those compared products.
- **Multi-product questions:** Identifies and returns multiple strongly relevant sources that share the requested feature.
- **Recommendation questions:** Filters for the strongest relevant product evidence that matches the concepts in the user's requirement.

---

## 7. Grounded Answer Generation

The LLM is strictly instructed to answer **only** from the retrieved context. 

The system explicitly instructs the model:
- Not to use outside knowledge.
- Not to hallucinate.
- To provide concise answers.
- To state clearly when the knowledge base does not contain enough information.

Only the highly filtered, final selected sources are passed in the prompt context to the LLM.

---

## 8. Source Attribution

The CLI explicitly displays the specific product or category sources selected for the answer alongside the LLM's response.

This provides:
- Transparency into what evidence the LLM used.
- Easier verification of the answer.
- A direct method for debugging retrieval quality.
- Reduction of irrelevant source attribution.

---

## 9. Hallucination / Insufficient Information Handling

The system is deliberately designed to return a standardized fallback response:

> *"The document does not contain enough information to answer this."*

when the available knowledge-base evidence is insufficient. This is critically important for questions involving information that is not established by the supplied document (e.g., current stock availability or unmentioned technologies), mitigating the risk of the model hallucinating an answer.

---

## 10. Knowledge Base

The system relies exclusively on the supplied Gutermann product overview Markdown document as its single source of truth.

---

## 11. Running the Project

### Requirements

- Python 3.x
- Ollama installed locally
- The `phi3:latest` model must be pulled and available in Ollama.

### Installation & Execution

1. Install the required Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the agent:
```bash
python qa_agent.py
```
