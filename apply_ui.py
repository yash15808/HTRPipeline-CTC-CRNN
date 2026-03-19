import re, pathlib
path = pathlib.Path('scripts/pdf_gradio_demo.py')
text = path.read_text(encoding='utf-8')

# 1. Custom CSS Replace
old_css = r'    custom_css = """[\s\S]*?    """'
new_css = '''    custom_css = """
    /* Dark Theme */
    body, .gradio-container { background-color: #0b0f19 !important; color: #e2e8f0 !important; font-family: 'Inter', sans-serif !important; }
    
    .title-header { display: flex; align-items: center; gap: 15px; margin-bottom: -10px; }
    .logo-icon { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 5px 12px; border-radius: 8px; font-weight: bold; }
    .title-text h1 { color: white !important; font-size: 24px !important; margin: 0 !important; }
    .subtitle { color: #94a3b8; font-size: 14px; margin-top: 5px; margin-bottom: 20px; }
    
    .status-prepare { background-color: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 15px; color: white; font-weight: 600; margin-bottom: 20px; }
    
    .panel-block { background-color: #111827 !important; border: 1px solid #1e293b !important; border-radius: 8px !important; }
    
    .preset-dense { background: linear-gradient(135deg, #f43f5e, #e11d48) !important; border: none !important; color: white !important; }
    .preset-sparse { background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important; border: none !important; color: white !important; }
    .preset-printed { background: linear-gradient(135deg, #d946ef, #c026d3) !important; border: none !important; color: white !important; }
    .preset-hist { background: linear-gradient(135deg, #f59e0b, #d97706) !important; border: none !important; color: white !important; }
    
    .process-btn { background: linear-gradient(135deg, #0ea5e9, #0284c7) !important; border: none !important; color: white !important; }
    .export-btn { background: #10b981 !important; border: none !important; color: white !important; }
    
    .footer-status { background-color: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 20px; margin-top: 20px; font-size: 13px; color: #94a3b8; }
    .status-tag { background-color: #1e293b; color: #6366f1; padding: 2px 10px; border-radius: 12px; }
    
    .tabs { border-bottom: 1px solid #1e293b !important; }
    .tab-nav button { background-color: transparent !important; border: 1px solid #1e293b !important; border-radius: 20px !important; padding: 8px 16px !important; color: #94a3b8 !important; }
    .tab-nav button.selected { background-color: #1e293b !important; color: white !important; }
    
    input, textarea, select { background-color: #0b0f19 !important; border: 1px solid #1e293b !important; color: white !important; }
    """'''

text = re.sub(old_css, new_css, text)
text = text.replace('theme=gr.themes.Soft(primary_hue="teal")', 'theme=gr.themes.Base()')

# 2. Add Compute logic to inputs
text = text.replace('inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider, debug_checkbox]',
                    'inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider, debug_checkbox]') # Not modifying actual inputs yet.

path.write_text(text, encoding='utf-8')
print("CSS patched successfully")
