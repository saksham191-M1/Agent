import gradio as gr
from agent.orchestrator import Orchestrator
from voice.output_engine import speak
from voice.input_engine import listen_once
from config.settings import VOICE_OUTPUT_ENABLED
import threading

orchestrator = Orchestrator()

def handle_chat(message, history, use_voice):
    if not message:
        return "", history
        
    # Process with orchestrator
    reply = orchestrator.process_message(message)
    
    # Append to Gradio history format
    history.append((message, reply))
    
    # Handle voice output in a separate thread to not block UI
    if use_voice:
        threading.Thread(target=speak, args=(reply,), daemon=True).start()
        
    return "", history

def handle_voice_input():
    text = listen_once()
    return text

def launch_ui():
    with gr.Blocks(theme=gr.themes.Monochrome(), title="JARVIS") as interface:
        gr.Markdown("# 🤖 J A R V I S")
        
        with gr.Row():
            voice_toggle = gr.Checkbox(label="🔊 JARVIS Voice Output", value=VOICE_OUTPUT_ENABLED)
            
        chatbot = gr.Chatbot(height=500, label="Conversation")
        
        with gr.Row():
            msg_input = gr.Textbox(show_label=False, placeholder="Type your command or use mic...", scale=8)
            mic_btn = gr.Button("🎤 Mic", scale=1)
            send_btn = gr.Button("▶ Send", scale=1)

        # Event listeners
        msg_input.submit(handle_chat, inputs=[msg_input, chatbot, voice_toggle], outputs=[msg_input, chatbot])
        send_btn.click(handle_chat, inputs=[msg_input, chatbot, voice_toggle], outputs=[msg_input, chatbot])
        
        # Mic behavior: click mic -> listens -> puts text in input box -> auto submits
        mic_btn.click(handle_voice_input, inputs=[], outputs=[msg_input]).then(
            handle_chat, inputs=[msg_input, chatbot, voice_toggle], outputs=[msg_input, chatbot]
        )

        gr.Markdown("*(Type 'clear' to reset memory)*")

    print("Launching JARVIS UI...")
    # Open in browser automatically
    interface.launch(inbrowser=True, prevent_thread_lock=False)
