import gradio as gr
from orchestrator import Orchestrator

def chat(message, history, game):
    history = history or []
    response = Orchestrator(game, message)
    history.append((message, response))
    return history, ""

with gr.Blocks(title="Multi-Agent Game Trainer AI") as demo:
    gr.Markdown("# Beginner Competitive Game Trainer (Multi-Agent)")
    game_dropdown = gr.Dropdown(choices=["Valorant", "CS2", "League of Legends"], label="Game", value="League of Legends")
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Ask for tips, meta, routines...", label="Message")
    clear = gr.Button("Clear")
    msg.submit(chat, [msg, chatbot, game_dropdown], [chatbot, msg])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(share=False)
