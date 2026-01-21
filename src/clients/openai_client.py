import os
from openai import OpenAI

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
