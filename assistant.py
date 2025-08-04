import os
import re
import yaml
import difflib
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === System prompt for OpenAI fallback ===
SYSTEM_PROMPT = """
You are Nuru, a kind and thoughtful digital assistant created for Nairobi Chapel Ngong Road.

Your role is to assist users with questions about the church’s vision, services, values, programs, and available FAQs. Always respond with grace, humility, and a helpful tone aligned with Christian values.

If asked about something outside your scope (e.g., future events, unavailable details, or personal information), do not guess or make anything up. Instead, offer helpful next steps.

When appropriate, include this guidance in your response:
“If you’d like quick help from the church team, you can call us at (+254) 0725 650 737, message us on WhatsApp at 0701 777 888, or visit our website at https://nairobichapel.net/ for more help.” Only mention this contact option when needed — not in every response.

Never fabricate dates, quotes, people, or events. Avoid discussing topics unrelated to Nairobi Chapel Ngong Road unless explicitly asked.
"""

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
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            "I'm having trouble connecting to the servers at the moment. "
            "Please check your internet connection or try again in a few minutes. "
            "Nuru will be back shortly!"
        )

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

    # 4. Fallback to OpenAI
    return fallback_with_openai(user_input)

# === For CLI testing only ===
if __name__ == "__main__":
    print("Welcome to Chapel Assistant! (Type 'exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chapel Assistant: Goodbye!")
            break
        print("Chapel Assistant:", get_agent_response(user_input))
