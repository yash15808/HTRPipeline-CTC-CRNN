import json
import tempfile
import os
import cv2
import gradio as gr
import numpy as np
from pdf2image import convert_from_path
from htr_pipeline import read_page, DetectorConfig, LineClusteringConfig, ReaderConfig, PrefixTree

# Load dictionary for word beam search
with open('data/words_alpha.txt') as f:
    word_list = [w.strip().upper() for w in f.readlines()]
prefix_tree = PrefixTree(word_list)

# Load configuration
with open('data/config.json') as f:
    config = json.load(f)

# Create examples for image tab
examples = []
for k, v in config.items():
    examples.append([f'data/{k}', v['scale'], v['margin'], False, 2, v['text_scale']])

class PDFProcessor:
    def __init__(self, poppler_path=None, dpi=200):
        self.poppler_path = poppler_path
        self.dpi = dpi
        
    def find_poppler(self):
        """Try to automatically find Poppler installation"""
        possible_paths = [
            r"C:\poppler\poppler\Library\bin",
            r"C:\poppler\bin",
            r"C:\Program Files\poppler\bin",
            r"C:\Program Files (x86)\poppler\bin",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def pdf_to_images(self, pdf_path):
        """Convert PDF to list of OpenCV images"""
        poppler_path = self.poppler_path or self.find_poppler()
        
        if not poppler_path:
            raise RuntimeError("Poppler not found. Please install from: https://github.com/oschwartz10612/poppler-windows/releases/")
        
        print(f"Converting PDF to images using Poppler path: {poppler_path}")
        pil_images = convert_from_path(pdf_path, dpi=self.dpi, poppler_path=poppler_path)
        
        cv2_images = []
        for pil_image in pil_images:
            if pil_image.mode != 'L':
                pil_image = pil_image.convert('L')
            cv2_img = np.array(pil_image)
            cv2_images.append(cv2_img)
        
        return cv2_images

def process_page(img, scale, margin, use_dictionary, min_words_per_line, text_scale, debug=False):
    """Process a single image page with debug option"""
    # Convert if image is from Gradio (RGB)
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    if debug:
        print(f"DEBUG: Scale={scale}, Margin={margin}, UseDict={use_dictionary}")
    
    # read page
    read_lines = read_page(img,
                           detector_config=DetectorConfig(scale=scale, margin=margin),
                           line_clustering_config=LineClusteringConfig(min_words_per_line=min_words_per_line),
                           reader_config=ReaderConfig(decoder='word_beam_search' if use_dictionary else 'best_path',
                                                      prefix_tree=prefix_tree if use_dictionary else None))

    # create text to show
    res = ''
    for read_line in read_lines:
        res += ' '.join(read_word.text for read_word in read_line) + '\n'

    # create visualization to show
    vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB) if len(img.shape) == 2 else img.copy()
    
    for i, read_line in enumerate(read_lines):
        for read_word in read_line:
            aabb = read_word.aabb
            cv2.rectangle(vis_img,
                          (aabb.xmin, aabb.ymin),
                          (aabb.xmax, aabb.ymax),
                          (255, 0, 0),
                          2)
            cv2.putText(vis_img,
                        read_word.text,
                        (aabb.xmin, aabb.ymin - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        text_scale,
                        color=(255, 0, 0),
                        thickness=2)
    
    if debug and len(read_lines) == 0:
        print("DEBUG: No text detected! Try adjusting scale/margin parameters.")

    return res, vis_img, read_lines

def process_pdf_with_htr(pdf_file, use_dictionary, scale, margin, min_words_per_line, text_scale, debug=False):
    """Process uploaded PDF with HTR and return both text and visualization"""
    if pdf_file is None:
        return "Please upload a PDF file", None
    
    try:
        # Get the file path from Gradio's file object
        pdf_path = pdf_file.name
        
        # Initialize PDF processor
        pdf_processor = PDFProcessor()
        
        # Convert PDF to images
        images = pdf_processor.pdf_to_images(pdf_path)
        
        if debug:
            print(f"DEBUG: Processing {len(images)} pages with scale={scale}, margin={margin}")
        
        # Process each page
        full_text = ""
        visualization_images = []
        
        for page_num, image in enumerate(images):
            page_text, vis_img, _ = process_page(
                image, scale, margin, use_dictionary, min_words_per_line, 
                text_scale, debug=debug
            )
            full_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            visualization_images.append(vis_img)
            
            if debug:
                print(f"DEBUG: Page {page_num + 1} completed")
        
        # For demo, return the first page visualization
        if visualization_images:
            return full_text, visualization_images[0]  # Return first page visualization
        else:
            return full_text, None
        
    except Exception as e:
        error_msg = f"Error processing PDF: {str(e)}"
        if debug:
            error_msg += f"\n\nDetailed error: {repr(e)}"
        error_msg += "\n\nPlease ensure Poppler is installed from: https://github.com/oschwartz10612/poppler-windows/releases/"
        return error_msg, None

# Create tabs for different functionalities
with gr.Blocks(title="Handwritten Text Recognition Pipeline", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📝 Handwritten Text Recognition Pipeline")
    gr.Markdown("Upload images or PDFs containing handwritten text for recognition")
    
    with gr.Tab("🖼️ Single Image"):
        gr.Markdown("### Process a single handwritten text image")
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(label='Input image', type="numpy")
                scale_slider = gr.Slider(0.01, 15, 1, step=0.01, label='Scale') 
                margin_slider = gr.Slider(0, 20, 5, step=1, label='Margin')
                dictionary_checkbox = gr.Checkbox(value=False, label='Use dictionary')
                words_slider = gr.Slider(1, 10, 2, step=1, label='Minimum words per line')
                text_scale_slider = gr.Slider(0.5, 2.0, 1.0, step=0.1, label='Text size in visualization')
                debug_checkbox = gr.Checkbox(value=False, label='Debug mode')
                
                process_btn = gr.Button("Process Image", variant="primary")
            
            with gr.Column():
                text_output = gr.Textbox(label='Recognized Text', lines=10)
                image_output = gr.Image(label='Visualization')
        
        # Examples for image tab
        gr.Examples(
            examples=examples,
            inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider],
            outputs=[text_output, image_output],
            label="Example Images"
        )
    
    with gr.Tab("📄 PDF Document"):
        gr.Markdown("### Process a PDF containing handwritten text")
        
        with gr.Row():
            with gr.Column():
                pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
                scale_slider = gr.Slider(0.01, 15, 1, step=0.01, label='Scale') 
                pdf_margin = gr.Slider(0, 20, 5, step=1, label='Margin')
                pdf_dictionary = gr.Checkbox(value=False, label='Use dictionary')
                pdf_words = gr.Slider(1, 10, 2, step=1, label='Minimum words per line')
                pdf_text_scale = gr.Slider(0.5, 2.0, 1.0, step=0.1, label='Text size in visualization')
                pdf_debug = gr.Checkbox(value=False, label='Debug mode')
                
                pdf_process_btn = gr.Button("Process PDF", variant="primary")
            
            with gr.Column():
                # VISUALIZATION SECTION (IDENTICAL TO SINGLE IMAGE TAB)
                with gr.Row():
                    pdf_text_output = gr.Textbox(label='Extracted Text', lines=10)
                with gr.Row():
                    pdf_image_output = gr.Image(label='First Page Visualization')
        
        # Page navigation for multi-page PDFs
        with gr.Row():
            page_info = gr.Markdown("**Visualization:** First page shown. Download PDF for full results.")
    
    # Connect buttons to functions
    process_btn.click(
        fn=process_page,
        inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider, debug_checkbox],
        outputs=[text_output, image_output]
    )
    
    pdf_process_btn.click(
        fn=process_pdf_with_htr,
        inputs=[pdf_input, pdf_dictionary, pdf_scale, pdf_margin, pdf_words, pdf_text_scale, pdf_debug],
        outputs=[pdf_text_output, pdf_image_output]
    )
    
    gr.Markdown("---")
    gr.Markdown("""
    ### 🎯 Fine-Tuning Guide:
    
    **Scale (0.01-1.0):** 
    - **0.01-0.1**: For very small text/dense handwriting
    - **0.2-0.4**: Standard handwriting (default: 0.4)
    - **0.5-1.0**: For large text/sparse handwriting
    
    **Margin (0-20 pixels):**
    - **0-5**: Tight bounding boxes
    - **5-10**: Standard spacing (default: 5)
    - **10-20**: Loose bounding boxes
    
    **Text Size (0.5-2.0):**
    - **0.5-1.0**: Small text overlay
    - **1.0-1.5**: Standard text (default: 1.0)
    - **1.5-2.0**: Large text overlay
    
    **Debug Mode:** Check this to see parameter values in console
    """)
    
    gr.Markdown("""
    ### 📋 PDF Processing Notes:
    - Visualization shows the **first page** with bounding boxes
    - Text output includes **all pages** of the PDF
    - For multi-page PDFs, all pages are processed but only first page is visualized
    - Adjust parameters to optimize detection for your specific document
    """)

if __name__ == "__main__":
    demo.launch(share=True)