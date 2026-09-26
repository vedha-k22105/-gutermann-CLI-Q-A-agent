import requests
import json

def get_embedding(text):
    url = "http://localhost:11434/api/embeddings"
    data = {
        "model": "phi3:latest",
        "prompt": text
    }
    response = requests.post(url, json=data)
    return response.json()

if __name__ == "__main__":
    res = get_embedding("hello world")
    if "embedding" in res:
        print("Success, dimension:", len(res["embedding"]))
    else:
        print("Failed:", res)
