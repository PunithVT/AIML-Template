# Quick Start

This repository includes a local Gradio UI, CLI entry point, and FastAPI server for resume ranking.

## 1. Create and activate a Python virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Launch the Gradio UI

```bash
python -m src.main --gradio
```

Open the URL shown in the terminal, usually `http://127.0.0.1:7860`.

## 4. Launch the FastAPI server

```bash
python -m src.main --api --port 8000
```

Then open `http://127.0.0.1:8000/docs` for API docs.

## 5. Run CLI resume ranking

```bash
python -m src.main --resume data/resumes/sample.txt --jd data/job_descriptions/sample_jd.txt
```

## 6. Troubleshooting

- If Python reports missing modules, ensure the virtual environment is activated.
- If port `7860` is busy, use `--port <port>` with the `--gradio` command.
- For Windows path issues, use double quotes around paths.

## Notes

- Use `python -m src.main --help` to see available options.
- If you want to run the app without typing commands every time, keep this file open and follow the commands here.
