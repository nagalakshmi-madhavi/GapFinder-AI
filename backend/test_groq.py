import os
from dotenv import load_dotenv
from groq import Groq

# Load API key from .env file
load_dotenv()

# Connect to Groq
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# Send a test message
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Hello! Introduce yourself as an AI study assistant."
        }
    ]
)

# Print AI response
print(response.choices[0].message.content)