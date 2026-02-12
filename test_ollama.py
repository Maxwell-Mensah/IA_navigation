from llm_handler import LLMHandler
import time

print("Testing Ollama integration...")
llm = LLMHandler()
start = time.time()
response = llm.predict_intent("ouvre firefox")
end = time.time()

print(f"Response: {response}")
print(f"Time taken: {end - start:.2f}s")

if response.get("action") == "open" and "firefox" in str(response.get("target")).lower():
    print("SUCCESS: Intent correctly identified.")
else:
    print("FAILURE: Intent not identified correctly.")
