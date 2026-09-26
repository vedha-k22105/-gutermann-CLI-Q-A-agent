import subprocess

queries = [
    "What is the Minimum Level Profiling feature and which product has it?",
    "What is the difference between the AQUASCAN 610 and the AQUASCAN 760T?",
    "Which products use True Sound Sensors (TSS) — and what advantage does TSS give?",
    "I need to find leaks on plastic pipes over long distances — what do you recommend?",
    "We want permanent monitoring in underground chambers with no drilling — what fits?",
    "Can I order the ZONESCAN HYDRO today?",
    "Does the ZONESCAN AI use hydrophone technology?",
    "exit"
]

proc = subprocess.Popen(
    ["python", "-u", "qa_agent.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

for q in queries:
    print(f"Sending: {q}")
    proc.stdin.write(q + "\n")
    proc.stdin.flush()

for line in proc.stdout:
    print(line, end="")
