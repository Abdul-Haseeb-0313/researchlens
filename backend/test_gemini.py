from app.generation.llm import GeminiLLM


llm = GeminiLLM()

prompt = """
You are a helpful research assistant.

Does this guy have some experience related to Intelligent Systems? and whats his name?
"""

answer = llm.generate(prompt)

print("\nGemini response:")
print("=" * 80)
print(answer)