# Project Enhancements & Future Roadmap

This document summarizes the major enhancements discussed and considered during the development of the JanikAI Gutermann Product Q&A RAG system.

It clearly distinguishes between capabilities that are already implemented in the current assessment version and improvements proposed for future versions.

---

# 1. Implemented Enhancements

The following capabilities are already implemented in the current JanikAI Gutermann RAG system.

## 1.1 Local RAG-Based Question Answering

The system implements a Retrieval-Augmented Generation (RAG) pipeline for answering questions from the supplied Gutermann product knowledge base.

The workflow is:

```text
User Query
    ↓
Query Processing
    ↓
Relevant Chunk Retrieval
    ↓
Source Selection
    ↓
LLM
    ↓
Grounded Answer
```

The system does not rely only on the LLM's general knowledge. Relevant information is retrieved from the supplied product documentation before answer generation.

---

## 1.2 Markdown Knowledge-Base Ingestion

The supplied Gutermann product documentation is loaded from a Markdown knowledge base.

The system processes the document during application startup and converts the content into retrievable chunks.

This provides a structured knowledge source for the QA agent.

---

## 1.3 Document Chunking

The product documentation is divided into smaller logical chunks.

The chunking approach separates product-level information and category-level information so that retrieval can identify the most relevant information for a query.

This improves retrieval precision compared with treating the complete Markdown document as a single piece of text.

---

## 1.4 Local Embedding-Based Retrieval

The system uses local sentence embeddings to represent the knowledge-base chunks.

The embeddings allow user queries to be compared against the stored product information using semantic similarity.

This allows the system to retrieve relevant information even when the wording of the question is different from the wording used in the source document.

---

## 1.5 Hybrid Retrieval

The system combines semantic similarity with lexical matching.

The retrieval process uses:

```text
Semantic Similarity
        +
Lexical Matching
        ↓
Hybrid Retrieval Score
```

This provides both:

- semantic understanding of the query
- matching of important product names and technical terms

This is particularly useful for product-specific queries containing terms such as AQUASCAN, ZONESCAN, TSS, hydrophone, plastic pipes, and other technical terminology.

---

## 1.6 Query-Aware Retrieval and Source Selection

The system does not treat every query in exactly the same way.

It identifies different query patterns such as:

- direct product questions
- comparison questions
- recommendation questions
- multi-product questions

The final source selection is adjusted according to the type of question.

This reduces irrelevant product information being passed to the LLM.

---

## 1.7 Product-Specific Source Selection

For queries that explicitly mention a product, the system prioritizes the corresponding product information.

For comparison questions, the relevant named products are selected.

For recommendation-style questions, the system selects the most relevant product source rather than passing a large collection of unrelated products to the LLM.

This improves answer focus and source precision.

---

## 1.8 Grounded Answer Generation

The LLM is instructed to generate answers using the retrieved knowledge-base information.

The prompt explicitly restricts the model from relying on unsupported external information.

The intended pipeline is:

```text
Retrieved Knowledge
        ↓
LLM
        ↓
Grounded Response
```

This helps reduce hallucination and keeps answers connected to the supplied Gutermann documentation.

---

## 1.9 Insufficient-Information Handling

The system is designed to avoid inventing information when the knowledge base does not provide enough evidence.

For unsupported questions, the agent can indicate that the available documentation does not contain sufficient information.

This is important for questions such as product availability when the knowledge base does not explicitly establish current availability.

---

## 1.10 Source Attribution

The current system displays the product/category sources used to generate the answer.

Example:

```text
Sources:
- AQUASCAN TM3
```

This provides the reviewer with an indication of which knowledge-base information contributed to the response.

---

## 1.11 Local LLM Integration

The system uses a locally running Ollama model for answer generation.

This allows the complete QA workflow to run locally without requiring a hosted LLM API for the current implementation.

---

## 1.12 CLI-Based Interaction

The system follows the assessment requirement of providing a command-line interface.

The user can repeatedly enter questions and receive answers without restarting the application for every query.

The workflow is:

```text
Start Agent
    ↓
Load Knowledge Base
    ↓
Build Embeddings
    ↓
Interactive Query Loop
    ↓
Question → Retrieval → Answer
    ↓
Next Question
```

---

## 1.13 One-Time Knowledge-Base Processing at Startup

The knowledge base is processed and embedded when the application starts.

The embeddings are then reused for subsequent queries during the same execution.

This avoids rebuilding the embeddings for every individual question.

---

## 1.14 Retrieval Debugging and Inspection

The implementation includes debugging support that can expose retrieval-related information during development.

This was useful for identifying cases where semantically similar but incorrect product sources were being retrieved.

The retrieval pipeline was refined using this debugging process.

---

## 1.15 Query Testing

The system was tested using the official assessment questions as well as additional rephrased and unsupported queries.

Testing included product questions, comparisons, recommendations, and questions where the knowledge base should not provide an unsupported answer.

This helped validate both retrieval behavior and grounded answer generation.

---

# 2. Future Enhancements

The following capabilities were discussed as potential improvements but are **not implemented in the current assessment version**.

## 2.1 Evidence-Aware Source Attribution

The current system identifies the final product/category chunks used for generation.

A future version could provide the exact supporting passage or evidence span within the source document.

Possible workflow:

```text
Answer
    ↓
Supporting Evidence
    ↓
Product + Exact Knowledge-Base Passage
```

This would make answers easier to verify and improve transparency.

---

## 2.2 Incremental Knowledge-Base Updates

The current system processes the knowledge base during application startup.

A future version could detect changes in the knowledge base and update only the affected portions instead of rebuilding the complete embedding index.

Possible workflow:

```text
Knowledge Base Updated
        ↓
Detect Added / Modified / Deleted Chunks
        ↓
Re-embed Affected Chunks
        ↓
Update Index
```

This would reduce unnecessary computation when product documentation changes frequently.

---

## 2.3 Selective Re-Embedding

A future version could assign stable identifiers or content hashes to individual chunks.

When the knowledge base changes:

- unchanged chunks retain their embeddings
- modified chunks are re-embedded
- new chunks are embedded
- deleted chunks are removed from the index

This would improve efficiency as the knowledge base grows.

---

## 2.4 Knowledge-Base Versioning

Future versions could maintain explicit knowledge-base versions.

For example:

```text
KB Version 1.0
KB Version 1.1
KB Version 1.2
```

Each answer could optionally record the knowledge-base version used to generate it.

This would improve reproducibility and make product-information changes easier to audit.

---

## 2.5 Source-Supported Product Status Metadata

Future versions could support structured metadata for:

- product availability
- product status
- product lifecycle
- launch information

However, the system should only report such information when it is explicitly supported by the knowledge source.

It should never infer that a product is active, discontinued, available, or unavailable without supporting source information.

---

## 2.6 Additional Knowledge-Base Formats

The current assessment uses the supplied Markdown knowledge base.

Future versions could support:

- Markdown
- TXT
- PDF
- DOCX
- HTML

These documents could be normalized into a common internal chunk representation before embedding and retrieval.

---

## 2.7 Improved Hybrid Retrieval

The current system already combines semantic similarity and lexical matching.

Future retrieval improvements could incorporate additional signals such as:

- dense vector similarity
- exact keyword matching
- phrase matching
- metadata filtering
- product constraints
- category constraints

This could improve retrieval for highly technical queries containing exact product names and specialized terminology.

---

## 2.8 Advanced Reranking

The current system performs query-aware source selection after initial retrieval.

A future version could introduce a dedicated reranking model or more sophisticated relevance scoring.

This could help distinguish between:

- semantically similar products
- genuinely relevant evidence
- supporting category information
- unrelated products

Possible workflow:

```text
User Query
    ↓
Initial Retrieval
    ↓
Candidate Sources
    ↓
Advanced Reranking
    ↓
Most Relevant Evidence
    ↓
LLM
```

The goal would be to improve source precision before information reaches the LLM.

---

## 2.9 Retrieval Evaluation Framework

A future version could maintain a dedicated evaluation dataset containing representative questions and expected relevant sources.

Possible evaluation metrics include:

- retrieval precision
- source recall
- source attribution accuracy
- grounded answer rate
- hallucination rate
- latency

This would allow retrieval changes to be evaluated systematically rather than relying only on manual testing.

---

# 3. Enhancement Roadmap Summary

| Area | Current Status |
|---|---|
| Local RAG pipeline | Implemented |
| Markdown knowledge-base ingestion | Implemented |
| Document chunking | Implemented |
| Local embeddings | Implemented |
| Hybrid retrieval | Implemented |
| Query-aware source selection | Implemented |
| Product-specific source selection | Implemented |
| Grounded LLM generation | Implemented |
| Insufficient-information handling | Implemented |
| Product/category source attribution | Implemented |
| Local Ollama integration | Implemented |
| Interactive CLI | Implemented |
| One-time startup embedding | Implemented |
| Retrieval debugging | Implemented |
| Query testing | Implemented |
| Exact evidence-span attribution | Future |
| Incremental knowledge-base updates | Future |
| Selective re-embedding | Future |
| Knowledge-base versioning | Future |
| Source-supported product status metadata | Future |
| Additional document formats | Future |
| Improved hybrid retrieval | Future |
| Advanced reranking | Future |
| Retrieval evaluation framework | Future |

---

# 4. Development Direction

The current implementation focuses on satisfying the assessment requirements with a functional, grounded, local RAG pipeline.

Future development can extend the system toward a more maintainable and scalable product-document intelligence platform by improving evidence traceability, knowledge-base lifecycle management, retrieval quality, evaluation, and support for additional document formats.

All features listed under **Future Enhancements** are proposed improvements and are not claimed to be implemented in the current assessment version.
