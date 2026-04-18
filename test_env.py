from dotenv import load_dotenv
import os

load_dotenv()
print("DATABASE_URL:", os.environ.get("DATABASE_URL"))