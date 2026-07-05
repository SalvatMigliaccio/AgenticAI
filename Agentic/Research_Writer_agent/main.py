import sys
from dotenv import load_dotenv
from pipeline import run_pipeline
from agents import check_ollama_running

load_dotenv()


if __name__ == "__main__":
    # Check if Ollama is running
    if not check_ollama_running():
        print(" Ollama is not running!")
        print("Start it with: ollama serve")
        sys.exit(1)
    
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "Post-quantum cryptography and its impact on digital certificates"

    print(f"\n{'═'*60}")
    print(f"  TOPIC: {topic}")
    print(f"{'═'*60}")

    result = run_pipeline(topic)

    # Save both outputs to disk
    with open("research_report.md", "w") as f:
        f.write(result["research"])

    with open("article.md", "w") as f:
        f.write(result["article"])

    print(f"\n{'═'*60}")
    print("  FINAL ARTICLE")
    print(f"{'═'*60}\n")
    print(result["article"])
    print("\nFiles saved:")
    print("  research_report.md — raw research output")
    print("  article.md         — final article")