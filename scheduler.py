import schedule
import time
from src.parser import parse_and_enrich

def run_parser():
    try:
        print("Running parser:", __name__)
        summary = parse_and_enrich()
        print("Parser summary:", summary)
    except Exception as e:
        print("Parser error:", e)

def main():
    # Run once at start
    run_parser()
    # Schedule every 10 minutes
    schedule.every(10).minutes.do(run_parser)
    print("Scheduler started: parser will run every 10 minutes. Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped.")

if __name__ == "__main__":
    main()
