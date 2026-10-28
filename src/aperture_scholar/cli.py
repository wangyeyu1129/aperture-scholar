"""Minimal operational CLI; never calls a paid model implicitly."""

import argparse
import json
import sys

from aperture_scholar.bootstrap import build_database, build_pipeline
from aperture_scholar.config import Settings
from aperture_scholar.domain.errors import ApertureError
from aperture_scholar.domain.models import Paper
from aperture_scholar.domain.similarity import cosine_similarity, deduplicate_vectors
from aperture_scholar.infrastructure.sqlite import SQLitePaperRepository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aperture", description="Aperture Scholar skeleton")
    parser.add_argument("command", choices=["check", "init-db", "demo", "run"])
    args = parser.parse_args(argv)
    try:
        settings = Settings()
        if args.command == "check":
            print("Configuration valid. Live research adapters: not implemented.")
        elif args.command == "init-db":
            build_database(settings)
            print(f"Database initialized: {settings.database_path}")
        elif args.command == "demo":
            database = build_database(settings)
            repository = SQLitePaperRepository(database)
            paper = Paper(
                id="synthetic:demo", title="Synthetic infrastructure smoke test", year=2026
            )
            repository.upsert(paper)
            print(
                json.dumps(
                    {
                        "mode": "synthetic infrastructure demo; not research recommendations",
                        "persisted": repository.get(paper.id) == paper,
                        "cosine": cosine_similarity([1.0, 0.0], [1.0, 0.0]),
                        "retained_indices": deduplicate_vectors([[1.0, 0.0], [1.0, 0.0]], 0.85),
                    },
                    indent=2,
                )
            )
        else:
            build_pipeline(settings)
        return 0
    except (ApertureError, ValueError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
