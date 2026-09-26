from qa_agent import VectorStore, parse_markdown, generate_answer
chunks = parse_markdown('PRODUCT OVERVIEW_EN_int_A4 Web_v1.2.md')
vs = VectorStore(chunks)
query = 'I need to find leaks on plastic pipes over long distances — what do you recommend?'
results = vs.retrieve(query)
print('\nSources:')
for item in results:
    print(f"- {item['chunk']['product']} ({item['chunk']['category']})")
