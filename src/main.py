"""CLI entry point for Resume Ranking System.

Usage:
    # CLI Mode - rank single resume
    python -m src.main --resume <path> --jd <path>
    
    # CLI Mode - batch ranking
    python -m src.main --resumes-dir data/resumes --jd <path> --top-k 10
    
    # Launch Gradio UI
    python -m src.main --gradio
    
    # Launch FastAPI server
    python -m src.main --api --port 8000
"""

import argparse
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from src.features import extract_features
from src.parser import parse_resume
from src.ranking import rank_candidates
from src.utils.io import read_text, save_json
from src.utils.logger import get_logger

log = get_logger(__name__)


def process_one(resume_path: str, jd_text: str) -> dict:
    log.info(f"Parsing {resume_path}")
    text = parse_resume(resume_path)
    profile = extract_features(text)
    return {"file": resume_path, "profile": asdict(profile)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume parser & candidate ranker")
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--gradio", action="store_true", help="Launch Gradio UI")
    mode_group.add_argument("--api", action="store_true", help="Launch FastAPI server")
    
    # CLI options
    parser.add_argument("--resume", help="Path to a single resume")
    parser.add_argument("--resumes-dir", help="Directory of resumes for batch ranking")
    parser.add_argument("--jd", help="Path to job description text file")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--output", default="data/processed/results.json")
    
    # Server options
    parser.add_argument("--port", type=int, default=8000, help="Port for API/Gradio server")
    parser.add_argument("--host", default="127.0.0.1", help="Host for API/Gradio server")
    
    args = parser.parse_args()
    
    # Gradio mode
    if args.gradio:
        log.info(f"Launching Gradio UI on http://{args.host}:{args.port}")
        from src.ui.gradio_app import create_gradio_interface
        demo = create_gradio_interface()
        demo.launch(server_name=args.host, server_port=args.port, share=False)
        return
    
    # API mode
    if args.api:
        log.info(f"Launching FastAPI server on http://{args.host}:{args.port}")
        log.info("API documentation available at http://{args.host}:{args.port}/docs")
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
            "--reload"
        ]
        subprocess.run(cmd)
        return
    
    # CLI mode - require job description
    if not args.jd:
        parser.error("Provide --jd for CLI mode, or use --gradio or --api for interactive modes")
    
    jd_text = read_text(args.jd)

    if args.resume:
        result = process_one(args.resume, jd_text)
        save_json(result, args.output)
        log.info(f"Wrote {args.output}")
        return

    if args.resumes_dir:
        files = [str(p) for p in Path(args.resumes_dir).glob("*") if p.is_file()]
        log.info(f"Found {len(files)} resumes")
        profiles = [extract_features(parse_resume(f)) for f in files]
        ranked = rank_candidates(profiles, jd_text, top_k=args.top_k)
        out = [
            {"rank": i + 1, "file": files[profiles.index(p)], "score": asdict(s)}
            for i, (p, s) in enumerate(ranked)
        ]
        save_json(out, args.output)
        log.info(f"Wrote ranked results to {args.output}")
        return

    parser.error("Provide either --resume, --resumes-dir, --gradio, or --api")


if __name__ == "__main__":
    main()
