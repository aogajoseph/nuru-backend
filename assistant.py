import os
import re
import yaml
import json
import random
import difflib
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Nuru configuration
with open("config/nuru_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

SYSTEM_PROMPT = config["fallback_prompt"]["system_message"]
PREFIXES = config["tone_guide"]["response_tips"]["prefixes"]
SUFFIXES = config["tone_guide"]["response_tips"]["suffixes"]

# Load YAML-based FAQs
def load_faq(filepath="faq.yaml"):
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

faq_items = load_faq()

# Build a normalized flat map: question/variant → answer
flat_faq_map = {}

for question, content in faq_items.items():
    answer = content["answer"]
    variants = content.get("variants", [])
    all_phrasings = [question] + variants
    for phrase in all_phrasings:
        norm = re.sub(r"[^\w\s]", "", phrase.lower().strip())
        flat_faq_map[norm] = answer

print("FAQ loaded keys:", list(flat_faq_map.keys()))

def normalize(text):
    return re.sub(r"[^\w\s]", "", text.lower().strip())

def fallback_with_openai(prompt, model="gpt-3.5-turbo"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=600
        )
        content = response.choices[0].message.content.strip()
        prefix = random.choice(PREFIXES)
        suffix = random.choice(SUFFIXES)
        return f"{prefix} {content} {suffix}"
    except Exception:
        return (
            "Hmm! I’m having trouble connecting to the servers at the moment... "
            "Please try again shortly. Thank you for your patience!"
        )

def get_agent_response(user_input):
    user_input_norm = normalize(user_input)

    # 1. Exact match
    if user_input_norm in flat_faq_map:
        return flat_faq_map[user_input_norm]

    # 2. Fuzzy match
    match = difflib.get_close_matches(user_input_norm, flat_faq_map.keys(), n=1, cutoff=0.7)
    if match:
        return flat_faq_map[match[0]]

    # 3. Log unmatched
    with open("unmatched_questions.log", "a", encoding="utf-8") as f:
        f.write(user_input + "\n")

    # 4. Fallback
    return fallback_with_openai(user_input)

# CLI Testing
if __name__ == "__main__":
    print("Welcome to Chapel Assistant! (Type 'exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chapel Assistant: Goodbye!")
            break
        print("Chapel Assistant:", get_agent_response(user_input))
