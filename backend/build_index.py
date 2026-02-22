import os
import sys
from dotenv import load_dotenv

# Add current directory to path so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from rag_engine import RagEngine

# Load env vars
load_dotenv(os.path.join(os.path.dirname(current_dir), '.env'))

def build():
    print("Starting Index Build Process...")

    try:
        # Initializing RagEngine triggers the _load_or_create_index logic
        # We can force a rebuild if we want, but default logic builds if missing.
        # To force rebuild for this script, we can check arguments or just rely on manual deletion.
        # simpler: just init.
        engine = RagEngine()
        print("✅ Index built and saved successfully!")
    except Exception as e:
        print(f"❌ Error building index: {e}")

if __name__ == "__main__":
    build()
