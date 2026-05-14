"""Visualization utilities for resume ranking results."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class RankingVisualizer:
    """Generate visualizations for resume ranking results."""
    
    @staticmethod
    def create_score_chart(results_df: pd.DataFrame) -> plt.Figure:
        """Create a bar chart of final scores."""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        names = results_df["Resume Name"].astype(str)
        scores = results_df["Final Score (%)"].astype(float)
        
        ax.barh(names, scores, color="#3b82f6")
        ax.set_title("Candidate Match Scores", fontsize=14, fontweight="bold")
        ax.set_xlabel("Final Score (%)", fontsize=12)
        ax.set_ylabel("Resume", fontsize=12)
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        
        for i, v in enumerate(scores):
            ax.text(v + 1, i, f"{v:.1f}%", va="center", fontsize=10)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_skills_chart(results_df: pd.DataFrame) -> plt.Figure:
        """Create a bar chart of matched skills count."""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        names = results_df["Resume Name"].astype(str)
        matched_skills = results_df.get("Matched Skills", pd.Series([""] * len(results_df)))
        skill_counts = matched_skills.fillna("").apply(
            lambda x: len([s.strip() for s in x.split(",") if s.strip()])
        )
        
        ax.barh(names, skill_counts, color="#10b981")
        ax.set_title("Matched Skills Count", fontsize=14, fontweight="bold")
        ax.set_xlabel("Number of Matched Skills", fontsize=12)
        ax.set_ylabel("Resume", fontsize=12)
        ax.invert_yaxis()
        
        for i, v in enumerate(skill_counts):
            ax.text(v + 0.1, i, str(int(v)), va="center", fontsize=10)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_recommendation_pie(results_df: pd.DataFrame) -> plt.Figure:
        """Create a pie chart of recommendation distribution."""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        if "Recommendation" in results_df.columns:
            rec_counts = results_df["Recommendation"].value_counts()
            labels = rec_counts.index.tolist()
            values = rec_counts.values.tolist()
        else:
            labels = ["Excellent Match", "Good Match", "Moderate Match", "Low Match"]
            values = [0, 0, 0, 0]
        
        colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"]
        
        ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors[:len(labels)],
            wedgeprops={"edgecolor": "white", "linewidth": 2}
        )
        ax.set_title("Recommendation Distribution", fontsize=14, fontweight="bold")
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_score_components_chart(results_df: pd.DataFrame) -> plt.Figure:
        """Create a grouped bar chart showing score components."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        names = results_df["Resume Name"].astype(str)
        x = np.arange(len(names))
        width = 0.15
        
        skill_scores = results_df.get("Skill Score (%)", pd.Series([0] * len(results_df))).astype(float)
        language_scores = results_df.get("Language Score (%)", pd.Series([0] * len(results_df))).astype(float)
        semantic_scores = results_df.get("Semantic Score (%)", pd.Series([0] * len(results_df))).astype(float)
        keyword_scores = results_df.get("Keyword Score (%)", pd.Series([0] * len(results_df))).astype(float)
        experience_scores = results_df.get("Experience Score (%)", pd.Series([0] * len(results_df))).astype(float)
        
        ax.bar(x - 2*width, skill_scores, width, label="Skill", color="#3b82f6")
        ax.bar(x - width, language_scores, width, label="Language", color="#10b981")
        ax.bar(x, semantic_scores, width, label="Semantic", color="#f59e0b")
        ax.bar(x + width, keyword_scores, width, label="Keyword", color="#8b5cf6")
        ax.bar(x + 2*width, experience_scores, width, label="Experience", color="#ec4899")
        
        ax.set_title("Score Components Breakdown", fontsize=14, fontweight="bold")
        ax.set_ylabel("Score (%)", fontsize=12)
        ax.set_xlabel("Resume", fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha="right")
        ax.legend(loc="upper right")
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_experience_analysis(results_df: pd.DataFrame) -> plt.Figure:
        """Create a scatter plot of experience vs final score."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        experience = results_df.get("Experience Score (%)", pd.Series([0] * len(results_df))).astype(float)
        scores = results_df["Final Score (%)"].astype(float)
        names = results_df["Resume Name"].astype(str)
        
        ax.scatter(experience, scores, s=200, color="#f59e0b", alpha=0.7, edgecolors="black", linewidth=1.5)
        
        for i, txt in enumerate(names):
            ax.annotate(
                txt,
                (experience.iloc[i], scores.iloc[i]),
                textcoords="offset points",
                xytext=(8, 8),
                ha="left",
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3)
            )
        
        ax.set_xlabel("Experience Score (%)", fontsize=12)
        ax.set_ylabel("Final Score (%)", fontsize=12)
        ax.set_title("Experience vs Final Score", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def generate_all_visualizations(results_df: pd.DataFrame) -> dict[str, plt.Figure]:
        """Generate all visualization charts."""
        if results_df is None or len(results_df) == 0:
            return {}
        
        return {
            "score_chart": RankingVisualizer.create_score_chart(results_df),
            "skills_chart": RankingVisualizer.create_skills_chart(results_df),
            "recommendation_pie": RankingVisualizer.create_recommendation_pie(results_df),
            "components_chart": RankingVisualizer.create_score_components_chart(results_df),
            "experience_chart": RankingVisualizer.create_experience_analysis(results_df),
        }
