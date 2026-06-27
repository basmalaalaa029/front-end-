"""CLI entry point for CV generation and API server."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cv_agent.app.config import PipelineConfig, _FASTAPI_AVAILABLE
from cv_generator.api.schemas import GenerateRequest
from cv_generator.models.cv_schema import CVData
from cv_generator.services.cv_generator import run_enhancement_sync
from analysis.parsing.file_parsing import parse_resume_file


def _build_cli():
    p = argparse.ArgumentParser(prog="cv_agent", description="Agentic CV Builder v8.0")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="Generate a CV")
    for a, kw in [
        ("--name", {"required": True}), ("--role", {"required": True}),
        ("--email", {"required": True}), ("--phone", {"default": ""}),
        ("--linkedin", {"default": ""}), ("--skills", {"required": True}),
        ("--experience", {"required": True}), ("--jd", {"default": ""}),
        ("--resume", {"default": ""}),
    ]:
        r.add_argument(a, **kw)
    sub.add_parser("serve", help="Start API server")
    return p


def main():
    args = _build_cli().parse_args()
    if args.command == "serve":
        if not _FASTAPI_AVAILABLE:
            raise SystemExit("FastAPI not installed")
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
        return
    cfg = PipelineConfig()
    req = GenerateRequest(
        full_name=args.name,
        target_role=args.role,
        email=args.email,
        phone=args.phone,
        linkedin=args.linkedin,
        skills=[s.strip() for s in args.skills.split(",")],
        experiences=[e.strip() for e in args.experience.split(";")],
        job_description=args.jd,
        parsed_resume=parse_resume_file(args.resume) if args.resume else "",
    )
    cv_data = CVData.from_generate_request(req)
    result = run_enhancement_sync(cv_data, "cli", cfg)
    print(json.dumps(result.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    main()
