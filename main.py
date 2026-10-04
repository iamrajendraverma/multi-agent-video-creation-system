import argparse
import sys

import config
from coordinator.coordinator import run_pipeline


def parse_args():

    parser = argparse.ArgumentParser(
        description="Create an animated short video from a prompt and publish it to YouTube."
    )
    parser.add_argument(
        "--prompt",
        help="What the video should be about (asked interactively if omitted)",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="Create and review the video, but don't upload it",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Upload without asking for confirmation",
    )
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default=config.YOUTUBE_PRIVACY,
        help="YouTube privacy status (default: %(default)s)",
    )
    parser.add_argument(
        "--resume",
        metavar="RUN_DIR",
        help="Continue an earlier run from its output folder",
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    user_prompt = args.prompt

    if not args.resume and not user_prompt:
        user_prompt = input("What video do you want to create?\n> ").strip()

        if not user_prompt:
            print("No prompt given.")
            return 1

    result = run_pipeline(
        user_prompt,
        publish=not args.no_publish,
        auto_confirm=args.yes,
        privacy=args.privacy,
        resume_dir=args.resume,
    )

    print("\n========== RESULT ==========")
    print("Output folder:", result.run_dir)
    print("Video:        ", result.video_path)
    print("Iterations:   ", result.iteration)

    if result.review:
        print(f"Review:        {'approved' if result.approved else 'rejected'} "
              f"(score {result.review.score}/10)")
    if result.youtube_metadata:
        print("Title:        ", result.youtube_metadata.title)
    if result.youtube_url:
        print("YouTube:      ", result.youtube_url)

    if result.needs_human_review:
        print("\nNot approved after the maximum number of revisions; "
              "needs human review. Reviewer feedback:")
        print(result.review_feedback)

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(" -", error)
        print(f"\nFix the problem and continue with: python main.py --resume {result.run_dir}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
