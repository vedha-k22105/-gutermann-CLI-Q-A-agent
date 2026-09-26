from qa_agent import *
import sys

chunks = parse_markdown(MARKDOWN_FILE)
vector_store = VectorStore(chunks)

queries = [
    "What is the Minimum Level Profiling feature and which product has it?",
    "What is the difference between the AQUASCAN 610 and the AQUASCAN 760T?",
    "Which products use True Sound Sensors (TSS) — and what advantage does TSS give?",
    "I need to find leaks on plastic pipes over long distances — what do you recommend?",
    "We want permanent monitoring in underground chambers with no drilling — what fits?",
    "Can I order the ZONESCAN HYDRO today?",
    "Does the ZONESCAN AI use hydrophone technology?",
    "Which Gutermann device is suitable for detecting leaks in plastic mains across long distances?",
    "What is the battery life of the AQUASCOPE 3?"
]

with open("test_report.txt", "w", encoding="utf-8") as f:
    for q in queries:
        f.write(f"--- QUERY ---\n{q}\n")
        cands = vector_store.retrieve(q)
        finals = select_final_sources(q, cands, chunks)
        answer = generate_answer(q, finals)
        f.write(f"--- AGENT ANSWER ---\n{answer}\n")
        f.write("--- SOURCES ---\n")
        for x in finals:
            if x['chunk']['type'] == 'Product':
                f.write(f"- {x['chunk']['product']} ({x['chunk']['category']})\n")
            else:
                f.write(f"- {x['chunk']['category']} (Overview)\n")
        f.write("\n=======================\n\n")
        f.flush()
        print(f"Finished query: {q}")
