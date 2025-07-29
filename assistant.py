import os
import re
import yaml
import difflib
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Load YAML-based FAQs ===
def load_faq(filepath="faq.yaml"):
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

faq_items = load_faq()

# === Build a normalized flat map: question/variant → answer ===
flat_faq_map = {}

for question, content in faq_items.items():
    answer = content["answer"]
    variants = content.get("variants", [])
    all_phrasings = [question] + variants
    for phrase in all_phrasings:
        norm = re.sub(r"[^\w\s]", "", phrase.lower().strip())
        flat_faq_map[norm] = answer

print("FAQ loaded keys:", list(flat_faq_map.keys()))


# === Core response handler ===
def normalize(text):
    return re.sub(r"[^\w\s]", "", text.lower().strip())

def get_agent_response(user_input):
    user_input_norm = normalize(user_input)

    # 1. Exact/variant match
    if user_input_norm in flat_faq_map:
        return flat_faq_map[user_input_norm]

    # 2. Fuzzy match
    match = difflib.get_close_matches(user_input_norm, flat_faq_map.keys(), n=1, cutoff=0.7)
    if match:
        return flat_faq_map[match[0]]

    # 3. Log unmatched questions
    with open("unmatched_questions.log", "a", encoding="utf-8") as f:
        f.write(user_input + "\n")

    # 4. Optional fallback to GPT (commented out)
    # try:
    #     response = client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {"role": "system", "content": "You are a helpful assistant for Nairobi Chapel."},
    #             {"role": "user", "content": user_input}
    #         ]
    #     )
    #     return response.choices[0].message.content.strip()
    # except Exception as e:
    #     return f"Sorry, something went wrong while using the assistant: {str(e)}"

    # 5. Static fallback
    return "I'm not sure how to answer that yet because I'm still learning. Please try rephrasing or check back soon."

# === For CLI testing only ===
if __name__ == "__main__":
    print("Welcome to Chapel Assistant! (Type 'exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chapel Assistant: Goodbye!")
            break
        print("Chapel Assistant:", get_agent_response(user_input))
