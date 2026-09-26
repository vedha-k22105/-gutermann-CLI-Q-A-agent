import os
import re
import sys
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# CONFIGURATION
# ============================================================

MARKDOWN_FILE = "PRODUCT OVERVIEW_EN_int_A4 Web_v1.2.md"

MODEL_NAME = "phi3:latest"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Retrieve a reasonable number of candidates internally.
# Only the best final sources will be sent to the LLM.
STAGE1_TOP_K = 8

# Debug mode can be enabled inside the CLI using:
# debug on
DEBUG_MODE = False


# ============================================================
# MARKDOWN PARSER
# ============================================================

def parse_markdown(filepath):
    """
    Parses the Markdown knowledge base.

    Product chunks and category chunks are kept separate.
    Category descriptions are NOT copied into every product chunk.
    """

    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")

    chunks = []

    current_category = "General"
    category_desc = []

    current_product = None
    product_content = []

    def save_product():
        nonlocal current_product, product_content

        if current_product:
            chunks.append({
                "type": "Product",
                "category": current_category,
                "product": current_product,
                "text": "\n".join(product_content).strip()
            })

    def save_category():
        nonlocal category_desc

        if category_desc:
            chunks.append({
                "type": "Category",
                "category": current_category,
                "text": "\n".join(category_desc).strip()
            })

    for line in lines:

        stripped = line.strip()

        # Category heading
        if stripped.startswith("## "):

            save_product()

            current_product = None
            product_content = []

            save_category()

            current_category = stripped[3:].strip()
            category_desc = []

        # Product heading
        elif stripped.startswith("### "):

            save_product()

            if not current_product:
                save_category()
                category_desc = []

            current_product = stripped[4:].strip()
            product_content = []

        else:

            if (
                stripped
                and not stripped.startswith("![img")
                and not stripped.startswith("<!--")
                and not stripped.startswith("# ")
            ):

                if current_product is not None:
                    product_content.append(stripped)

                else:
                    category_desc.append(stripped)

    # Save final entries
    save_product()

    if not current_product:
        save_category()

    # Map categories to products
    cat_to_prods = {}

    for chunk in chunks:

        if chunk["type"] == "Product":

            cat_to_prods.setdefault(
                chunk["category"],
                []
            ).append(chunk["product"])

    # Build embedding text
    for chunk in chunks:

        if chunk["type"] == "Product":

            chunk["full_text"] = (
                f"Product: {chunk['product']}\n"
                f"Category: {chunk['category']}\n\n"
                f"Product Details:\n"
                f"{chunk['text']}"
            )

        else:

            products = ", ".join(
                cat_to_prods.get(chunk["category"], [])
            )

            chunk["full_text"] = (
                f"Category: {chunk['category']}\n\n"
                f"Category Details:\n"
                f"{chunk['text']}\n\n"
                f"Products in this category: {products}"
            )

    return chunks


# ============================================================
# LEXICAL SCORE
# ============================================================

def lexical_score(query, text):
    """
    Lightweight keyword overlap score.
    """

    query_words = set(
        re.findall(r"\w+", query.lower())
    )

    text_words = set(
        re.findall(r"\w+", text.lower())
    )

    if not query_words:
        return 0.0

    overlap = len(
        query_words.intersection(text_words)
    )

    return overlap / len(query_words)


# ============================================================
# VECTOR STORE
# ============================================================

class VectorStore:

    def __init__(self, chunks):

        print("Loading embedding model (all-MiniLM-L6-v2)...")

        self.chunks = chunks

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print(f"Embedding {len(chunks)} chunks...")

        texts = [
            chunk["full_text"]
            for chunk in chunks
        ]

        self.embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )

        print("Embeddings ready in memory.")

    def retrieve(self, query):

        # Embed only the current query
        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        )

        # Calculate semantic similarity
        cosine_scores = cosine_similarity(
            query_embedding,
            self.embeddings
        )[0]

        candidates = []

        for i, chunk in enumerate(self.chunks):

            lex_score = lexical_score(
                query,
                chunk["full_text"]
            )

            # Hybrid score
            combined_score = (
                cosine_scores[i] * 0.8
                + lex_score * 0.2
            )

            candidates.append({
                "chunk": chunk,
                "cos_sim": float(cosine_scores[i]),
                "lex_sim": float(lex_score),
                "score": float(combined_score)
            })

        # Highest score first
        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return candidates[:STAGE1_TOP_K]


# ============================================================
# QUERY TYPE DETECTION
# ============================================================

def detect_query_type(query):

    query_lower = query.lower()

    # Comparison
    if any(
        keyword in query_lower
        for keyword in [
            "difference",
            "compare",
            "comparison",
            "vs",
            "versus"
        ]
    ):
        return "comparison"

    # Multiple products
    if any(
        keyword in query_lower
        for keyword in [
            "products",
            "which ones",
            "which products",
            "what products"
        ]
    ):
        return "multi_product"

    # Recommendation
    if any(
        keyword in query_lower
        for keyword in [
            "recommend",
            "what fits",
            "i need to",
            "we want",
            "best for",
            "which product",
            "what do you recommend"
        ]
    ):
        return "recommendation"

    return "direct"


# ============================================================
# PRODUCT NAME EXTRACTION
# ============================================================

def extract_product_names(query, chunks):

    names = []

    query_lower = query.lower()

    for chunk in chunks:

        if chunk["type"] != "Product":
            continue

        product_name = chunk["product"]

        if product_name.lower() in query_lower:
            names.append(product_name)

    return names


# ============================================================
# FINAL SOURCE SELECTION
# ============================================================

def select_final_sources(query, candidates, all_chunks):

    if not candidates:
        return []

    query_type = detect_query_type(query)

    query_lower = query.lower()

    explicit_products = extract_product_names(
        query,
        all_chunks
    )

    # --------------------------------------------------------
    # Extract meaningful query words
    # --------------------------------------------------------

    words = [
        word
        for word in re.findall(
            r"\b\w+\b",
            query_lower
        )
        if len(word) > 2
    ]

    # --------------------------------------------------------
    # Build phrase list
    # --------------------------------------------------------

    phrases = []

    for i in range(len(words) - 2):

        phrase = (
            f"{words[i]} "
            f"{words[i + 1]} "
            f"{words[i + 2]}"
        )

        phrases.append(phrase)

    # --------------------------------------------------------
    # Rerank candidates
    # --------------------------------------------------------

    reranked = []

    for candidate in candidates:

        chunk = candidate["chunk"]

        text_lower = chunk["full_text"].lower()

        bonus = 0.0

        # ----------------------------------------------------
        # Explicit product name match
        # ----------------------------------------------------

        if (
            chunk["type"] == "Product"
            and chunk["product"] in explicit_products
        ):
            bonus += 1.0

        # ----------------------------------------------------
        # Exact phrase match
        # ----------------------------------------------------

        for phrase in phrases:

            if phrase in text_lower:
                bonus += 0.3

        # ----------------------------------------------------
        # Recommendation evidence
        # ----------------------------------------------------

        if query_type == "recommendation":

            matched_words = sum(
                1
                for word in words
                if word in text_lower
            )

            if words:

                evidence_score = (
                    matched_words / len(words)
                )

                bonus += evidence_score * 0.5

        # Final score
        candidate["final_score"] = (
            candidate["score"] + bonus
        )

        reranked.append(candidate)

    # Sort again
    reranked.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    # ========================================================
    # SELECT SOURCES
    # ========================================================

    final_sources = []

    # --------------------------------------------------------
    # Comparison
    # --------------------------------------------------------

    if query_type == "comparison":

        # Prefer explicitly named products
        for candidate in reranked:

            chunk = candidate["chunk"]

            if (
                chunk["type"] == "Product"
                and chunk["product"] in explicit_products
            ):

                final_sources.append(candidate)

                if len(final_sources) == 2:
                    break

        # Fallback
        if not final_sources:

            final_sources = reranked[:2]

    # --------------------------------------------------------
    # Direct question
    # --------------------------------------------------------

    elif query_type == "direct":

        # Only the strongest source
        final_sources = [
            reranked[0]
        ]

    # --------------------------------------------------------
    # Multi-product question
    # --------------------------------------------------------

    elif query_type == "multi_product":

        best_score = reranked[0]["final_score"]

        for candidate in reranked:

            # Strict relevance margin
            if (
                candidate["final_score"]
                >= best_score * 0.80
            ):

                final_sources.append(candidate)

        # Maximum 4 sources
        final_sources = final_sources[:4]

    # --------------------------------------------------------
    # Recommendation question
    # --------------------------------------------------------

    elif query_type == "recommendation":

        # Always take strongest source
        final_sources.append(
            reranked[0]
        )

        # Only add second source when it is VERY close
        # to the strongest source.
        #
        # This prevents unrelated products from appearing
        # as sources.

        if len(reranked) > 1:

            first_score = (
                reranked[0]["final_score"]
            )

            second_score = (
                reranked[1]["final_score"]
            )

            if (
                second_score
                >= first_score * 0.92
            ):

                final_sources.append(
                    reranked[1]
                )

    return final_sources


# ============================================================
# LLM ANSWER GENERATION
# ============================================================

def generate_answer(query, final_sources):

    if not final_sources:

        return (
            "The document does not contain enough "
            "information to answer this."
        )

    # --------------------------------------------------------
    # Build SMALL context
    # --------------------------------------------------------

    context_parts = []

    for index, item in enumerate(final_sources):

        context_parts.append(
            f"--- Context {index + 1} ---\n"
            f"{item['chunk']['full_text']}"
        )

    context = "\n\n".join(
        context_parts
    )

    # --------------------------------------------------------
    # Grounded concise prompt
    # --------------------------------------------------------

    prompt = f"""
You are a precise product assistant for Gutermann water leak detection equipment.

Answer the user's question using ONLY the provided context.

Rules:
- Give a concise answer in 2–4 sentences.
- Mention the relevant product name clearly.
- Use only facts supported by the context.
- Do not use outside knowledge.
- Do not hallucinate.
- Do not repeat the question.
- If the context does not contain enough information, say exactly:
"The document does not contain enough information to answer this."

{context}

Question: {query}

Answer:
"""

    # --------------------------------------------------------
    # Ollama request
    # --------------------------------------------------------

    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,

        "options": {

            # Deterministic answer
            "temperature": 0.0,

            # Limit generated tokens for faster response
            "num_predict": 100,

            "stop": [
                "Question:",
                "--- Context"
            ]
        }
    }

    try:

        response = requests.post(
            OLLAMA_API_URL,
            json=data,
            timeout=60
        )

        response.raise_for_status()

        answer = response.json().get(
            "response",
            ""
        ).strip()

        if not answer:

            return (
                "The document does not contain enough "
                "information to answer this."
            )

        return answer

    except requests.exceptions.Timeout:

        return (
            "The local language model took too long "
            "to respond. Please try again."
        )

    except Exception as e:

        return (
            f"Error communicating with Ollama: {e}"
        )


# ============================================================
# SOURCE DISPLAY
# ============================================================

def show_sources(final_sources):

    if not final_sources:
        return

    print("\nSources:")

    for item in final_sources:

        chunk = item["chunk"]

        if chunk["type"] == "Product":

            print(
                f"- {chunk['product']} "
                f"({chunk['category']})"
            )

        else:

            print(
                f"- {chunk['category']} "
                f"(Category Overview)"
            )

    print()


# ============================================================
# MAIN CLI
# ============================================================

def main():

    global DEBUG_MODE

    print(
        "--- Gutermann Q&A Agent Initialization ---"
    )

    # --------------------------------------------------------
    # Load knowledge base ONCE
    # --------------------------------------------------------

    chunks = parse_markdown(
        MARKDOWN_FILE
    )

    # --------------------------------------------------------
    # Build vector store ONCE
    # --------------------------------------------------------

    vector_store = VectorStore(
        chunks
    )

    print(
        "--- Initialization Complete ---\n"
    )

    print(
        "Type 'exit' or 'quit' to end the session."
    )

    print(
        "Type 'debug on' to inspect retrieval.\n"
    )

    # --------------------------------------------------------
    # Interactive loop
    # --------------------------------------------------------

    while True:

        try:

            query = input("> ").strip()

        except EOFError:

            break

        # Ignore empty input
        if not query:
            continue

        # Exit
        if query.lower() in [
            "exit",
            "quit"
        ]:

            print("Goodbye!")
            break

        # ----------------------------------------------------
        # Debug ON
        # ----------------------------------------------------

        if query.lower() == "debug on":

            DEBUG_MODE = True

            print(
                "Debug mode ON\n"
            )

            continue

        # ----------------------------------------------------
        # Debug OFF
        # ----------------------------------------------------

        if query.lower() == "debug off":

            DEBUG_MODE = False

            print(
                "Debug mode OFF\n"
            )

            continue

        # ----------------------------------------------------
        # Stage 1 retrieval
        # ----------------------------------------------------

        candidates = vector_store.retrieve(
            query
        )

        # ----------------------------------------------------
        # Final source selection
        # ----------------------------------------------------

        final_sources = select_final_sources(
            query,
            candidates,
            chunks
        )

        # ----------------------------------------------------
        # Debug information
        # ----------------------------------------------------

        if DEBUG_MODE:

            print(
                "\n--- STAGE 1 CANDIDATES ---"
            )

            for i, candidate in enumerate(
                candidates
            ):

                chunk = candidate["chunk"]

                name = chunk.get(
                    "product",
                    chunk["category"]
                )

                print(
                    f"{i + 1}. {name}"
                )

                print(
                    f"   semantic score: "
                    f"{candidate['cos_sim']:.3f}"
                )

                print(
                    f"   lexical score: "
                    f"{candidate['lex_sim']:.3f}"
                )

                print(
                    f"   combined score: "
                    f"{candidate['score']:.3f}"
                )

                print(
                    f"   final score: "
                    f"{candidate.get('final_score', 0):.3f}"
                )

            print(
                "\n--- FINAL SOURCES ---"
            )

            for i, source in enumerate(
                final_sources
            ):

                chunk = source["chunk"]

                name = chunk.get(
                    "product",
                    chunk["category"]
                )

                print(
                    f"{i + 1}. {name}"
                )

            print(
                "--------------------------\n"
            )

        # ----------------------------------------------------
        # Generate answer
        # ----------------------------------------------------

        answer = generate_answer(
            query,
            final_sources
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print(
            f"Agent: {answer}"
        )

        show_sources(
            final_sources
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()