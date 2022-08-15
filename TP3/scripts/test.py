import random
import time
import subprocess

ENTITIES = [("filter_posts", True, 3),
            ("filter_comments", True, 3),
            ("filter_post_max_avg_sentiment", False, 1),
            ("calculator_post_avg_score", False, 1),
            ("calculator_avg_sentiment_by_post", True, 4),
            ("filter_student_liked_posts", True, 5),
            ("joiner", True, 6),
            ("monitor", True, 5)]


def simulate_failure():
    failing_service, is_multiple, replica_count = random.choice(ENTITIES)

    if is_multiple:
        failing_service = f"{failing_service}_{random.randint(0, replica_count - 1)}"

    subprocess.run([f"docker kill {failing_service}"], shell=True)


def main():
    while True:
        simulate_failure()
        time.sleep(random.randint(15, 20))


if __name__ == "__main__":
    main()
