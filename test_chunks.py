from qa_agent import parse_markdown
chunks = parse_markdown('PRODUCT OVERVIEW_EN_int_A4 Web_v1.2.md')
for c in chunks:
    print(f"{c['product']} -> {c['category']}")
