"""
app.py — Gradio Query Interface (Milestone 5)
Run with:  python app.py
Then open: http://localhost:7860
"""

import gradio as gr
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from query import ask


def handle_query(question: str):
    question = question.strip()
    if not question:
        return "Please enter a question.", "", ""

    result  = ask(question)
    answer  = result["answer"]
    sources = "\n".join(f"• {s}" for s in result["sources"])

    # Build a readable chunk detail view for transparency
    chunk_details = ""
    for i, c in enumerate(result["chunks"], 1):
        chunk_details += (
            f"[{i}] {c['source']}  (distance: {c['distance']:.4f})\n"
            f"{c['text'][:300]}\n\n"
        )

    return answer, sources, chunk_details.strip()


# Example questions (from your evaluation plan)
EXAMPLES = [
    ["Which professor for CSC 2720 is most frequently described as explaining concepts clearly?"],
    ["Which professor requires attendance according to student reviews?"],
    ["Which professor is described as having a heavy workload?"],
    ["Which professor is lenient in grading?"],
    ["Which professor has the best reviews irrespective of the course?"],
    ["Which professor's exams are primarily based on lecture slides?"],
]

# Build UI 
with gr.Blocks(title="GSU CS Professor Reviews — Unofficial Guide") as demo:
    gr.Markdown(
        """
        # GSU CS Department — Unofficial Professor Guide
        Ask a question about GSU Computer Science professors.
        Answers are grounded in real student reviews from Rate My Professors.
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            question_box = gr.Textbox(
                label       = "Your question",
                placeholder = "e.g. Which professor gives the most useful feedback?",
                lines       = 2,
            )
            ask_btn = gr.Button("Ask", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("**Example questions:**")
            gr.Examples(
                examples = EXAMPLES,
                inputs   = question_box,
                label    = "",
            )

    answer_box = gr.Textbox(label="Answer", lines=8, interactive=False)
    sources_box = gr.Textbox(label="Sources", lines=4, interactive=False)

    with gr.Accordion("Retrieved chunks (for inspection)", open=False):
        chunks_box = gr.Textbox(label="Top-5 retrieved chunks", lines=20, interactive=False)

    # Wire up button and Enter key
    ask_btn.click(
        fn      = handle_query,
        inputs  = question_box,
        outputs = [answer_box, sources_box, chunks_box],
    )
    question_box.submit(
        fn      = handle_query,
        inputs  = question_box,
        outputs = [answer_box, sources_box, chunks_box],
    )

if __name__ == "__main__":
    demo.launch()