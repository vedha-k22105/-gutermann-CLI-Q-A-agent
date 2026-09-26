from qa_agent import *
chunks = parse_markdown(MARKDOWN_FILE)
vector_store = VectorStore(chunks)

queries = [
    'What is the Minimum Level Profiling feature and which product has it?',
    'What is the difference between the AQUASCAN 610 and the AQUASCAN 760T?',
    'Which products use True Sound Sensors (TSS) — and what advantage does TSS give?',
    'I need to find leaks on plastic pipes over long distances — what do you recommend?',
    'We want permanent monitoring in underground chambers with no drilling — what fits?',
    'Can I order the ZONESCAN HYDRO today?',
    'Does the ZONESCAN AI use hydrophone technology?'
]

for q in queries:
    print(f'\nQ: {q}')
    cands = vector_store.retrieve(q)
    finals = select_final_sources(q, cands, chunks)
    print('Sources:')
    for f in finals:
        if f['chunk']['type'] == 'Product':
            print(f"- {f['chunk']['product']}")
        else:
            print(f"- {f['chunk']['category']} (Overview)")
