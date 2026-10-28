"""Export model contracts; --check detects uncommitted schema drift."""

import argparse
import json
from pathlib import Path

from aperture_scholar.domain.models import (
    Document,
    Extraction,
    Gap,
    GenerationContext,
    Idea,
    IdeaCard,
    NoveltyReport,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / "schemas"
    destination.mkdir(exist_ok=True)
    for model in (Document, Extraction, Gap, GenerationContext, Idea, IdeaCard, NoveltyReport):
        path = destination / f"{model.__name__}.json"
        expected = json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != expected:
                raise SystemExit(f"Schema drift: {path.name}; run make schemas")
        else:
            path.write_text(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
