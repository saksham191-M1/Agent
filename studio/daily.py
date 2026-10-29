"""Idempotent daily-ad entry point for a user-configured local scheduler.

python -m studio.daily --list-products
python -m studio.daily --product PRODUCT_ID --quality final
"""
import argparse
import json
import sys

from .models import StudioError
from .service import StudioService


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate one dated ad from a saved, reviewed product profile.")
    parser.add_argument("--list-products", action="store_true")
    parser.add_argument("--product", help="Product profile ID shown in Studio")
    parser.add_argument("--date", help="YYYY-MM-DD; default is today in UTC")
    parser.add_argument("--goal", default="", help="Creative focus, not new product facts")
    parser.add_argument("--copy-mode", choices=("template", "gemini"), default="template")
    parser.add_argument("--quality", choices=("draft", "final"), default="final")
    parser.add_argument("--narration", action="store_true", help="Explicitly use configured ElevenLabs narration (may incur charges)")
    parser.add_argument("--sfx", action="store_true", help="Add local/generated motion SFX and an optional assets/music bed")
    parser.add_argument("--new-take", action="store_true", help="Create another distinct take for this date (may incur copy/narration charges)")
    parser.add_argument("--plan-only", action="store_true", help="Save the storyboard without rendering")
    args = parser.parse_args(argv)
    service = StudioService()
    if args.list_products:
        for product in service.list_products():
            print(json.dumps({"id": product["id"], "name": product["name"], "ready": product["approved"]}, ensure_ascii=True))
        return 0
    if not args.product:
        parser.error("Provide --product ID or --list-products")
    last = [-1]

    def progress(fraction, message):
        step = int(fraction * 10)
        if step != last[0]:
            last[0] = step
            print(f"{fraction:.0%}: {message}", flush=True)

    try:
        options = {"campaign_date": args.date, "goal": args.goal, "copy_mode": args.copy_mode,
                   "new_take": args.new_take, "progress": progress}
        if args.plan_only:
            project = service.create_daily_project(args.product, **options)
            path = project["project_path"]
        else:
            project = service.generate_daily_ad(args.product, quality=args.quality, narration=args.narration,
                                                include_sfx=args.sfx, **options)
            path = project[f"{args.quality}_path"]
        print(json.dumps({"project_id": project["id"], "status": project["status"], "path": path,
                          "campaign": project["campaign"], "creative": project["creative"]}, ensure_ascii=True))
        return 0
    except StudioError as exc:
        print(f"Daily ad not completed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
