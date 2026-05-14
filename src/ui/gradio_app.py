"""Gradio UI for resume ranking - production version using modular code."""

import gradio as gr
import pandas as pd
import os
from pathlib import Path

from src.parser.pdf_parser import parse_pdf
from src.parser.docx_parser import parse_docx
from src.ranking.resume_ranker import ResumeRanker
from src.features.resume_analyzer import ResumeAnalyzer
from src.ui.visualizer import RankingVisualizer


# Initialize components
ranker = ResumeRanker()
analyzer = ResumeAnalyzer()
visualizer = RankingVisualizer()


def extract_text(file_path):
    """Extract text from PDF, DOCX, or TXT files."""
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        return ""


def rank_bulk_resumes(resume_files, job_description):
    """Rank multiple resume files against a job description."""
    if not resume_files:
        return pd.DataFrame({"Error": ["Please upload at least one resume."]})

    if not job_description or job_description.strip() == "":
        return pd.DataFrame({"Error": ["Please enter a job description."]})

    resume_texts = []
    resume_names = []

    for file in resume_files:
        file_path = file.name
        resume_text = extract_text(file_path)

        if resume_text.strip() != "":
            resume_texts.append(resume_text)
            resume_names.append(os.path.basename(file_path))

    if len(resume_texts) == 0:
        return pd.DataFrame({"Error": ["No valid resume text found."]})

    # Rank resumes
    ranked = ranker.rank_resumes(resume_texts, job_description)

    # Compile results DataFrame
    results = []
    for rank, (resume_text, score) in enumerate(ranked, 1):
        resume_analysis = analyzer.compare_with_jd(
            analyzer.analyze(resume_text),
            job_description
        )

        results.append({
            "Rank": rank,
            "Resume Name": resume_names[resume_texts.index(resume_text)],
            "Final Score (%)": round(score.final_score * 100, 2),
            "Skill Score (%)": round(score.skill_score * 100, 2),
            "Language Score (%)": round(score.language_score * 100, 2),
            "Semantic Score (%)": round(score.semantic_score * 100, 2),
            "Keyword Score (%)": round(score.keyword_score * 100, 2),
            "Experience Score (%)": round(score.experience_score * 100, 2),
            "Matched Skills": ", ".join(resume_analysis.matched_skills),
            "Missing Skills": ", ".join(resume_analysis.missing_skills),
            "Matched Languages": ", ".join(resume_analysis.matched_languages),
            "Missing Languages": ", ".join(resume_analysis.missing_languages),
            "Recommendation": score.recommendation
        })

    result_df = pd.DataFrame(results)
    return result_df


def analyze_and_visualize(resume_files, job_description):
    """Analyze resumes and generate visualizations."""
    result_df = rank_bulk_resumes(resume_files, job_description)
    
    if isinstance(result_df, pd.DataFrame) and "Error" in result_df.columns:
        return result_df, None, None, None, None

    visualizations = visualizer.generate_all_visualizations(result_df)
    
    return (
        result_df,
        visualizations.get("score_chart"),
        visualizations.get("skills_chart"),
        visualizations.get("recommendation_pie"),
        visualizations.get("experience_chart"),
    )


# Custom CSS from notebook
custom_css = """
:root {
    --accent: #3b82f6;
    --accent-dark: #1e40af;
    --accent-light: #dbeafe;
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --border-light: #e2e8f0;
    --border-medium: #cbd5e1;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
    --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.08);
    --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
    min-height: 100vh !important;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #f1f5f9 100%) !important;
    color: var(--text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    padding: 40px 24px !important;
}

.gradio-container * {
    color: var(--text-primary);
}

#hero {
    position: relative;
    padding: 56px 48px;
    border-radius: 20px;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow-xl);
    margin-bottom: 32px;
    overflow: hidden;
}

#hero::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.5;
}

#badge {
    display: inline-block;
    padding: 8px 14px;
    border-radius: 8px;
    background: var(--accent-light);
    border: 1px solid var(--accent);
    color: var(--accent-dark) !important;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 16px;
}

#hero-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 12px;
    color: var(--text-primary) !important;
    line-height: 1.2;
}

#hero-subtitle {
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-secondary) !important;
    max-width: 900px;
    margin: 0;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 32px;
}

.metric-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent);
}

.metric-value {
    font-size: 32px;
    font-weight: 800;
    color: var(--accent) !important;
    margin-bottom: 8px;
}

.metric-label {
    font-size: 13px;
    color: var(--text-secondary) !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.panel {
    position: relative;
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 28px;
    box-shadow: var(--shadow-lg);
}

.panel-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary) !important;
    margin-bottom: 8px;
}

.panel-desc {
    color: var(--text-secondary) !important;
    font-size: 14px;
    margin-bottom: 20px;
    line-height: 1.5;
}

textarea, input[type="text"], input[type="email"], input[type="number"], select {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-light) !important;
    color: var(--text-primary) !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    padding: 12px 14px !important;
    transition: all 0.2s ease !important;
}

textarea:focus, input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    outline: none !important;
}

textarea::placeholder, input::placeholder {
    color: var(--text-muted) !important;
}

label {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

span, p {
    color: var(--text-secondary) !important;
}

[data-testid="file"] {
    background: var(--bg-secondary) !important;
    border: 2px dashed var(--border-medium) !important;
    border-radius: 12px !important;
    padding: 28px !important;
    transition: all 0.3s ease !important;
}

[data-testid="file"]:hover {
    border-color: var(--accent) !important;
    background: var(--accent-light) !important;
}

button.primary {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 12px 24px !important;
    box-shadow: var(--shadow-md) !important;
    transition: all 0.25s ease !important;
    text-transform: none !important;
}

button.primary:hover {
    background: var(--accent-dark) !important;
    box-shadow: var(--shadow-lg) !important;
    transform: translateY(-1px);
}

button.primary:active {
    transform: translateY(0);
}

button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.25s ease !important;
}

button:not(.primary) {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-light) !important;
    color: var(--text-primary) !important;
}

button:not(.primary):hover {
    background: var(--border-light) !important;
}

.dataframe {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border-light) !important;
    box-shadow: var(--shadow-lg) !important;
}

table {
    background: var(--bg-primary) !important;
}

thead tr th {
    background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
    border: none !important;
    padding: 16px 12px !important;
}

tbody tr td {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-light) !important;
    padding: 14px 12px !important;
    font-size: 13px !important;
}

tbody tr:hover td {
    background: var(--bg-secondary) !important;
}

tbody tr:nth-child(even) td {
    background: var(--bg-secondary) !important;
}

tbody tr:nth-child(even):hover td {
    background: var(--bg-tertiary) !important;
}

#info-strip {
    margin-top: 32px;
    padding: 28px;
    border-radius: 16px;
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border: 1px solid var(--border-light);
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px;
    box-shadow: var(--shadow-lg);
}

.info-item {
    text-align: center;
    padding: 20px 16px;
    border-radius: 12px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    transition: all 0.3s ease;
}

.info-item:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent);
}

.info-title {
    font-weight: 700;
    color: var(--accent) !important;
    font-size: 14px !important;
    margin-bottom: 6px;
}

.info-sub {
    font-size: 12px;
    color: var(--text-muted) !important;
    line-height: 1.4;
}

.footer {
    text-align: center;
    color: var(--text-muted) !important;
    font-size: 13px;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid var(--border-light);
}

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--accent);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-dark);
}

@media (max-width: 1024px) {
    .metric-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    #info-strip {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 640px) {
    #hero {
        padding: 32px 24px;
    }
    
    #hero-title {
        font-size: 28px;
    }
    
    .metric-grid, #info-strip {
        grid-template-columns: 1fr;
    }
    
    .gradio-container {
        padding: 20px 16px !important;
    }
}

canvas {
    border-radius: 18px !important;
}

.plot-container {
    background: rgba(255,255,255,0.72) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255,255,255,0.5) !important;
    border-radius: 22px !important;
    padding: 16px !important;
    box-shadow: 0 10px 30px rgba(15,23,42,0.06) !important;
    transition: all 0.35s ease !important;
}

.plot-container:hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 40px rgba(15,23,42,0.10) !important;
}
"""


def create_gradio_interface():
    """Create and return the Gradio interface."""
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:

        gr.HTML("""
        <div id="hero">
            <div id="badge">AI-Powered Recruitment</div>
            <div id="hero-title">Resume Screening & Ranking</div>
            <div id="hero-subtitle">
                Upload multiple resumes and automatically rank candidates against a job description.
                Our intelligent system analyzes skills, experience, and relevance to find the best matches.
            </div>

            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">25%</div>
                    <div class="metric-label">Skill Match</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">35%</div>
                    <div class="metric-label">Languages</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">20%</div>
                    <div class="metric-label">Semantic Match</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">20%</div>
                    <div class="metric-label">Keywords & Experience</div>
                </div>
            </div>
        </div>
        """)

        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                with gr.Group(elem_classes="panel"):
                    gr.HTML("""
                    <div class="panel-title">📄 Upload Resumes</div>
                    <div class="panel-desc">
                        Select PDF, DOCX, or TXT files. Multiple uploads supported.
                    </div>
                    """)

                    resume_files = gr.File(
                        label="Student Resumes",
                        file_count="multiple",
                        file_types=[".pdf", ".docx", ".txt"]
                    )

                    gr.HTML("""
                    <div class="panel-title" style="margin-top: 24px;">📋 Job Description</div>
                    <div class="panel-desc">
                        Paste or type the target job description.
                    </div>
                    """)

                    job_description = gr.Textbox(
                        label="Job Description",
                        lines=14,
                        placeholder="Example: We are looking for a Python developer with experience in FastAPI, Docker, and AWS..."
                    )

                    with gr.Row():
                        submit_btn = gr.Button(
                            "🚀 Analyze & Rank",
                            variant="primary",
                            scale=2
                        )
                        clear_btn = gr.ClearButton(
                            components=[resume_files, job_description],
                            value="↻ Reset",
                            scale=1
                        )

            with gr.Column(scale=2):
                with gr.Group(elem_classes="panel"):
                    gr.HTML("""
                    <div class="panel-title">🏆 Results</div>
                    <div class="panel-desc">
                        Candidates ranked by relevance score. Higher scores indicate better matches.
                    </div>
                    """)

                    output_table = gr.Dataframe(
                        label="Ranking Results",
                        wrap=True,
                        interactive=False
                    )

                with gr.Group(elem_classes="panel"):
                    gr.HTML("""
                    <div class="panel-title">📈 Visual Insights</div>
                    <div class="panel-desc">
                        View match scores, skill coverage, recommendation distribution, and experience impact.
                    </div>
                    """)

                    with gr.Row():
                        score_chart = gr.Plot(label="Candidate Match Scores")
                        skills_chart = gr.Plot(label="Matched Skills Count")

                    with gr.Row():
                        pie_chart = gr.Plot(label="Recommendation Distribution")
                        exp_chart = gr.Plot(label="Experience vs Final Score")

        gr.HTML("""
        <div id="info-strip">
            <div class="info-item">
                <div class="info-title">Skills</div>
                <div class="info-sub">Technical & soft skills match</div>
            </div>
            <div class="info-item">
                <div class="info-title">Languages</div>
                <div class="info-sub">Programming language match</div>
            </div>
            <div class="info-item">
                <div class="info-title">Semantics</div>
                <div class="info-sub">AI-powered similarity</div>
            </div>
            <div class="info-item">
                <div class="info-title">Keywords</div>
                <div class="info-sub">Keyword relevance scoring</div>
            </div>
            <div class="info-item">
                <div class="info-title">Experience</div>
                <div class="info-sub">Years & roles analysis</div>
            </div>
        </div>

        <div class="footer">
            Built for intelligent resume screening and candidate evaluation
        </div>
        """)

        submit_btn.click(
            fn=analyze_and_visualize,
            inputs=[resume_files, job_description],
            outputs=[output_table, score_chart, skills_chart, pie_chart, exp_chart]
        )

        return demo


if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(share=True)

