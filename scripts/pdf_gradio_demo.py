######################### NEW CODE AT LINE 701

# import json
# import tempfile
# import os
# import cv2
# import gradio as gr
# import numpy as np
# from pdf2image import convert_from_path
# from htr_pipeline import read_page, DetectorConfig, LineClusteringConfig, ReaderConfig, PrefixTree
# import logging
# from datetime import datetime
# from functools import lru_cache
# import threading

# # Setup logging
# def setup_logging(debug=False):
#     """Setup logging configuration"""
#     log_level = logging.DEBUG if debug else logging.INFO
#     logging.basicConfig(
#         level=log_level,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         handlers=[
#             logging.FileHandler(f'htr_pipeline_{datetime.now().strftime("%Y%m%d")}.log'),
#             logging.StreamHandler()
#         ]
#     )
#     return logging.getLogger(__name__)

# logger = setup_logging()

# # Enhanced Configuration Management
# class Config:
#     def __init__(self, config_path='data/config.json'):
#         self.config_path = config_path
#         self.load_config()
#         self.load_dictionary()
    
#     def load_config(self):
#         """Load configuration with fallbacks"""
#         try:
#             with open(self.config_path) as f:
#                 self.config = json.load(f)
#         except FileNotFoundError:
#             self.config = {}
#             logger.warning(f"Config file {self.config_path} not found, using defaults")
    
#     def load_dictionary(self):
#         """Load dictionary with error handling"""
#         try:
#             with open('data/words_alpha.txt') as f:
#                 word_list = [w.strip().upper() for w in f.readlines()]
#             self.prefix_tree = PrefixTree(word_list)
#             logger.info(f"Loaded dictionary with {len(word_list)} words")
#         except FileNotFoundError:
#             logger.warning("Dictionary file not found, word beam search will be limited")
#             self.prefix_tree = None
    
#     def get_example_config(self, example_key):
#         """Get configuration for example with defaults"""
#         return self.config.get(example_key, {
#             'scale': 1.0,
#             'margin': 5,
#             'text_scale': 1.0
#         })

# # Initialize config
# config = Config()

# # Create examples for image tab
# examples = []
# for k, v in config.config.items():
#     examples.append([f'data/{k}', v['scale'], v['margin'], False, 2, v['text_scale']])

# # Enhanced PDF Processor with caching
# class CachedPDFProcessor:
#     def __init__(self, poppler_path=None, dpi=200):
#         self.poppler_path = poppler_path
#         self.dpi = dpi
#         self._cache = {}
#         self._lock = threading.Lock()
    
#     def find_poppler(self):
#         """Try to automatically find Poppler installation"""
#         possible_paths = [
#             r"C:\poppler\poppler\Library\bin",
#             r"C:\poppler\bin",
#             r"C:\Program Files\poppler\bin",
#             r"C:\Program Files (x86)\poppler\bin",
#             "/usr/bin",  # Linux
#             "/usr/local/bin",  # macOS
#         ]
        
#         for path in possible_paths:
#             if os.path.exists(path):
#                 logger.info(f"Found Poppler at: {path}")
#                 return path
#         logger.warning("Poppler not found in common locations")
#         return None
    
#     @lru_cache(maxsize=10)
#     def get_pdf_images_cached(self, pdf_path, dpi):
#         """Cache PDF conversions for same file and DPI"""
#         return self.pdf_to_images(pdf_path)
    
#     def pdf_to_images(self, pdf_path):
#         """Convert PDF to list of OpenCV images"""
#         poppler_path = self.poppler_path or self.find_poppler()
        
#         if not poppler_path:
#             raise RuntimeError("Poppler not found. Please install from: https://github.com/oschwartz10612/poppler-windows/releases/")
        
#         logger.info(f"Converting PDF to images using Poppler path: {poppler_path}")
#         pil_images = convert_from_path(pdf_path, dpi=self.dpi, poppler_path=poppler_path)
        
#         cv2_images = []
#         for pil_image in pil_images:
#             if pil_image.mode != 'L':
#                 pil_image = pil_image.convert('L')
#             cv2_img = np.array(pil_image)
#             cv2_images.append(cv2_img)
        
#         logger.info(f"Converted {len(cv2_images)} pages from PDF")
#         return cv2_images
    
#     def clear_cache(self):
#         """Clear the cache"""
#         self.get_pdf_images_cached.cache_clear()
#         self._cache.clear()
#         logger.info("PDF processor cache cleared")

# # Initialize PDF processor
# pdf_processor = CachedPDFProcessor()

# # Input Validation
# def validate_inputs(scale, margin, min_words_per_line, text_scale):
#     """Validate input parameters"""
#     if scale <= 0:
#         raise ValueError("Scale must be positive")
#     if margin < 0:
#         raise ValueError("Margin cannot be negative")
#     if min_words_per_line < 1:
#         raise ValueError("Minimum words per line must be at least 1")
#     if text_scale <= 0:
#         raise ValueError("Text scale must be positive")
#     return True

# # Parameter Presets
# def create_parameter_presets():
#     """Create parameter presets for different document types"""
#     presets = {
#         "dense_handwriting": {"scale": 0.3, "margin": 3, "min_words_per_line": 3, "text_scale": 0.8},
#         "sparse_handwriting": {"scale": 0.8, "margin": 8, "min_words_per_line": 1, "text_scale": 1.2},
#         "printed_forms": {"scale": 1.2, "margin": 5, "min_words_per_line": 2, "text_scale": 1.0},
#         "historical_documents": {"scale": 0.4, "margin": 2, "min_words_per_line": 2, "text_scale": 0.7},
#     }
#     return presets

# # Enhanced Processing Functions with improved visualization
# def process_page(img, scale, margin, use_dictionary, min_words_per_line, text_scale, debug=False):
#     """Process a single image page with debug option"""
#     try:
#         # Input validation
#         validate_inputs(scale, margin, min_words_per_line, text_scale)
        
#         if img is None:
#             return "Please provide an image", None, []
            
#         logger.info(f"Processing image with scale={scale}, margin={margin}, use_dict={use_dictionary}")
        
#         # Convert if image is from Gradio (RGB)
#         if len(img.shape) == 3:
#             img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
#         # Resize very large images for faster processing
#         height, width = img.shape
#         max_dimension = 2000
#         if max(height, width) > max_dimension:
#             scale_factor = max_dimension / max(height, width)
#             new_width = int(width * scale_factor)
#             new_height = int(height * scale_factor)
#             img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
#             if debug:
#                 print(f"DEBUG: Resized image from {width}x{height} to {new_width}x{new_height}")
        
#         # read page
#         read_lines = read_page(img,
#                                detector_config=DetectorConfig(scale=scale, margin=margin),
#                                line_clustering_config=LineClusteringConfig(min_words_per_line=min_words_per_line),
#                                reader_config=ReaderConfig(decoder='word_beam_search' if use_dictionary else 'best_path',
#                                                           prefix_tree=config.prefix_tree if use_dictionary else None))

#         # create text to show
#         res = ''
#         for read_line in read_lines:
#             res += ' '.join(read_word.text for read_word in read_line) + '\n'

#         # create visualization to show with improved styling
#         vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB) if len(img.shape) == 2 else img.copy()
        
#         # Color scheme: Teal and White for better visibility
#         bbox_color = (0, 128, 128)  # Teal
#         text_color = (220, 100, 80)  # White
        
#         for i, read_line in enumerate(read_lines):
#             for read_word in read_line:
#                 aabb = read_word.aabb
#                 # Draw bounding box
#                 cv2.rectangle(vis_img,
#                               (aabb.xmin, aabb.ymin),
#                               (aabb.xmax, aabb.ymax),
#                               bbox_color,
#                               2)
#                 # Draw text with improved font and styling
#                 cv2.putText(vis_img,
#                             read_word.text,
#                             (aabb.xmin, aabb.ymin - 5),
#                             cv2.FONT_HERSHEY_COMPLEX,  # Changed to COMPLEX for better readability
#                             text_scale,
#                             color=text_color,
#                             thickness=1 if text_scale < 1.0 else 2)  # Thinner text for smaller scale
        
#         logger.info(f"Processed image successfully, found {len(read_lines)} lines")
#         return res, vis_img, read_lines

#     except Exception as e:
#         error_msg = f"Error processing image: {str(e)}"
#         logger.error(f"Error in process_page: {str(e)}", exc_info=True)
#         if debug:
#             error_msg += f"\n\nDetailed error: {repr(e)}"
#         return error_msg, None, []

# def process_pdf_enhanced(pdf_file, use_dictionary, scale, margin, min_words_per_line, text_scale, debug=False):
#     """Enhanced PDF processing with progress and better error handling"""
#     if pdf_file is None:
#         return "Please upload a PDF file", None, "**Status:** Waiting for PDF upload..."
    
#     try:
#         pdf_path = pdf_file.name
        
#         # Validate PDF file
#         if not pdf_path.lower().endswith('.pdf'):
#             return "Please upload a valid PDF file", None, "**Status:** Invalid file type"
        
#         logger.info(f"Processing PDF: {pdf_path}")
        
#         # Convert PDF to images
#         images = pdf_processor.pdf_to_images(pdf_path)
        
#         if not images:
#             return "No pages found in PDF", None, "**Status:** No pages found in PDF"
        
#         # Process pages
#         full_text = ""
#         visualization_images = []
#         total_words = 0
#         total_lines = 0
        
#         for page_num, image in enumerate(images):
#             if debug:
#                 print(f"DEBUG: Processing page {page_num + 1}/{len(images)}")
            
#             page_text, vis_img, read_lines = process_page(
#                 image, scale, margin, use_dictionary, min_words_per_line, 
#                 text_scale, debug=debug
#             )
            
#             # Add page header with statistics
#             word_count = sum(len(line) for line in read_lines)
#             line_count = len(read_lines)
#             total_words += word_count
#             total_lines += line_count
            
#             full_text += f"--- Page {page_num + 1} (Words: {word_count}, Lines: {line_count}) ---\n{page_text}\n\n"
#             visualization_images.append(vis_img)
        
#         # Add summary
#         full_text = f"PDF Processing Summary:\nTotal Pages: {len(images)}\nTotal Lines: {total_lines}\nTotal Words: {total_words}\n\n" + full_text
        
#         # Create page navigation info
#         page_info = f"**Status:** Processed {len(images)} pages, {total_words} words across {total_lines} lines. Visualization shows first page."
        
#         logger.info(f"PDF processing completed: {len(images)} pages, {total_words} words")
#         return full_text, visualization_images[0], page_info
        
#     except Exception as e:
#         error_msg = f"Error processing PDF: {str(e)}"
#         logger.error(f"Error in process_pdf_enhanced: {str(e)}", exc_info=True)
#         if debug:
#             import traceback
#             error_msg += f"\n\nTraceback:\n{traceback.format_exc()}"
#         error_msg += "\n\nPlease ensure Poppler is installed from: https://github.com/oschwartz10612/poppler-windows/releases/"
#         return error_msg, None, "**Status:** Error processing PDF"

# # FIXED Export functionality
# def simple_export(text, format_type):
#     """Simple reliable export function that returns file paths"""
#     if not text or len(text.strip()) < 10:  # Minimum content check
#         print("No valid text to export")
#         return None
    
#     try:
#         # Create a named temporary file
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
#         if format_type == "txt":
#             suffix = '.txt'
#             filename = f"htr_export_{timestamp}.txt"
#         else:
#             suffix = '.json'
#             filename = f"htr_export_{timestamp}.json"
        
#         # Create temporary file in system temp directory
#         temp_dir = tempfile.gettempdir()
#         filepath = os.path.join(temp_dir, filename)
        
#         if format_type == "txt":
#             with open(filepath, 'w', encoding='utf-8') as f:
#                 f.write(text)
#         else:  # json
#             # Simple JSON structure
#             data = {
#                 "exported_at": datetime.now().isoformat(),
#                 "content": text,
#                 "line_count": text.count('\n') + 1,
#                 "word_count": len(text.split())
#             }
#             with open(filepath, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, indent=2, ensure_ascii=False)
        
#         print(f"✅ Export created: {filepath}")
#         return filepath
            
#     except Exception as e:
#         print(f"❌ Export error: {e}")
#         return None

# # Create the enhanced UI with improved color scheme
# def create_enhanced_ui():
#     """Create enhanced Gradio interface with improved design"""
    
#     # Updated CSS with improved color scheme
#     with gr.Blocks(title="Ink2Text HTR Pipeline", theme=gr.themes.Soft(primary_hue="teal", secondary_hue="blue"), css=custom_css) as demo:
        
#         gr.Markdown(
#             """
#             # 🎨 Ink2Text - Handwritten Text Recognition
#             *Transform handwritten documents into digital text with AI-powered precision*
#             """
#         )
    
        
#         with gr.Tab("🖼️ Single Image Processing"):
#             gr.Markdown("### Process Individual Handwritten Images")
            
#             with gr.Row():
#                 with gr.Column():
#                     # Parameter Presets with improved styling
#                     gr.Markdown("#### 🎛️ Quick Presets")
#                     with gr.Row():
#                         dense_btn = gr.Button("📝 Dense Text", size="sm", elem_classes="param-preset-btn")
#                         sparse_btn = gr.Button("📄 Sparse Text", size="sm", elem_classes="param-preset-btn")
#                         forms_btn = gr.Button("📋 Printed Forms", size="sm", elem_classes="param-preset-btn")
#                         historical_btn = gr.Button("📜 Historical Docs", size="sm", elem_classes="param-preset-btn")
                    
#                     image_input = gr.Image(label='Upload Handwritten Image', type="numpy", height=300)
                    
#                     with gr.Accordion("⚙️ Advanced Parameters", open=False):
#                         scale_slider = gr.Slider(0.01, 15, 1, step=0.01, label='Detection Scale') 
#                         margin_slider = gr.Slider(0, 20, 5, step=1, label='Text Margin')
#                         dictionary_checkbox = gr.Checkbox(value=False, label='Use Dictionary for Better Accuracy')
#                         words_slider = gr.Slider(1, 10, 2, step=1, label='Minimum Words Per Line')
#                         text_scale_slider = gr.Slider(0.5, 2.0, 1.0, step=0.1, label='Visualization Text Size')
#                         debug_checkbox = gr.Checkbox(value=False, label='Enable Debug Mode')
                    
#                     process_btn = gr.Button("🎯 Process Image", variant="primary", size="lg", elem_classes="process-btn")
                
#                 with gr.Column():
#                     text_output = gr.Textbox(label='Extracted Text', lines=12, show_copy_button=True)
                    
#                     with gr.Row():
#                         export_format = gr.Radio(["txt", "json"], value="txt", label="Export Format", interactive=True)
#                         export_btn = gr.Button("💾 Export Results", variant="secondary", elem_classes="export-btn")
#                     export_download = gr.File(
#                         label="Download Export", 
#                         visible=False,
#                         file_count="single",
#                         height=50
#                     )
                    
#                     image_output = gr.Image(label='Text Detection Visualization', height=400)
            
#             # Examples for image tab
#             gr.Examples(
#                 examples=examples,
#                 inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider],
#                 outputs=[text_output, image_output],
#                 label="🖼️ Example Images"
#             )
        
#         with gr.Tab("📄 PDF Document Processing"):
#             gr.Markdown("### Process Multi-page PDF Documents")
            
#             with gr.Row():
#                 with gr.Column():
#                     pdf_input = gr.File(
#                         label="Upload PDF Document", 
#                         file_types=[".pdf"], 
#                         type="filepath",
#                         height=50
#                     )
                    
#                     with gr.Accordion("⚙️ Processing Parameters", open=True):
#                         pdf_scale = gr.Slider(0.01, 15, 1, step=0.01, label='Detection Scale') 
#                         pdf_margin = gr.Slider(0, 20, 5, step=1, label='Text Margin')
#                         pdf_dictionary = gr.Checkbox(value=False, label='Use Dictionary for Better Accuracy')
#                         pdf_words = gr.Slider(1, 10, 2, step=1, label='Minimum Words Per Line')
#                         pdf_text_scale = gr.Slider(0.5, 2.0, 1.0, step=0.1, label='Visualization Text Size')
#                         pdf_debug = gr.Checkbox(value=False, label='Enable Debug Mode')
                    
#                     pdf_process_btn = gr.Button("🎯 Process PDF Document", variant="primary", size="lg", elem_classes="process-btn")
                
#                 with gr.Column():
#                     pdf_text_output = gr.Textbox(label='Extracted Text from All Pages', lines=12, show_copy_button=True)
                    
#                     with gr.Row():
#                         pdf_export_format = gr.Radio(["txt", "json"], value="txt", label="Export Format", interactive=True)
#                         pdf_export_btn = gr.Button("💾 Export Results", variant="secondary", elem_classes="export-btn")
#                     pdf_export_download = gr.File(
#                         label="Download Export", 
#                         visible=False,
#                         file_count="single",
#                         height=50
#                     )
                    
#                     pdf_image_output = gr.Image(label='First Page Visualization', height=400)
#                     pdf_page_info = gr.Markdown("**Status:** Ready to process PDF documents")
        
#         with gr.Tab("🔧 Batch Processing"):
#             gr.Markdown("### Process Multiple Files in Batch")
            
#             with gr.Row():
#                 with gr.Column():
#                     batch_files = gr.File(
#                         label="Upload Multiple Files", 
#                         file_count="multiple",
#                         file_types=[".pdf", ".png", ".jpg", ".jpeg"],
#                         height=100
#                     )
                    
#                     with gr.Accordion("Batch Processing Settings", open=False):
#                         batch_scale = gr.Slider(0.01, 15, 1, step=0.01, label='Detection Scale') 
#                         batch_margin = gr.Slider(0, 20, 5, step=1, label='Text Margin')
#                         batch_dictionary = gr.Checkbox(value=False, label='Use Dictionary')
                    
#                     batch_process_btn = gr.Button("🚀 Process Batch Files", variant="primary")
                
#                 with gr.Column():
#                     batch_results = gr.File(label="Download Combined Results")
#                     batch_summary = gr.JSON(label="Processing Summary")
#                     gr.Markdown("""
#                     <div class="info-box">
#                     <strong>📦 Batch Processing Features:</strong>
#                     <ul>
#                     <li>Process multiple PDFs and images simultaneously</li>
#                     <li>Combined results in single output file</li>
#                     <li>Individual file processing statistics</li>
#                     <li>Optimized for large document sets</li>
#                     </ul>
#                     </div>
#                     """)
        
#         with gr.Tab("⚙️ Settings & Configuration"):
#             gr.Markdown("### Application Settings & System Configuration")
            
#             with gr.Row():
#                 with gr.Column():
#                     gr.Markdown("#### Performance Settings")
#                     cache_size = gr.Slider(1, 100, 10, label="Cache Size (files)")
#                     auto_save = gr.Checkbox(value=True, label="Auto-save Results")
#                     default_params = gr.Button("🔄 Reset to Default Parameters", variant="secondary")
                
#                 with gr.Column():
#                     gr.Markdown("#### System Operations")
#                     clear_cache_btn = gr.Button("🗑️ Clear System Cache", variant="secondary")
#                     export_settings = gr.Button("📤 Export Application Settings", variant="secondary")
#                     settings_status = gr.Markdown("")
            
#             with gr.Row():
#                 with gr.Column():
#                     gr.Markdown("""
#                     <div class="warning-box">
#                     <strong>⚙️ System Requirements:</strong>
#                     <ul>
#                     <li>Poppler required for PDF processing</li>
#                     <li>Minimum 2GB RAM recommended</li>
#                     <li>Internet connection for dictionary lookup</li>
#                     <li>Modern web browser with JavaScript enabled</li>
#                     </ul>
#                     </div>
#                     """)
        
#         # Footer with improved styling
#         gr.Markdown("---")
#         gr.Markdown("""
#         <div style="text-align: center; color: #666; padding: 20px;">
#         <h3>🎯 Recognition Guide</h3>
#         <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px;">
#             <div style="background: #333; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
#                 <strong>Scale (0.01-1.0)</strong><br>
#                 <small>0.01-0.1: Dense text<br>0.2-0.4: Standard<br>0.5-1.0: Large text</small>
#             </div>
#             <div style="background: #333; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
#                 <strong>Margin (0-20px)</strong><br>
#                 <small>0-5: Tight boxes<br>5-10: Standard<br>10-20: Loose boxes</small>
#             </div>
#             <div style="background: #333; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;">
#                 <strong>Text Size (0.5-2.0)</strong><br>
#                 <small>0.5-1.0: Small overlay<br>1.0-1.5: Standard<br>1.5-2.0: Large overlay</small>
#             </div>
#         </div>
#         </div>
#         """)
        
#         # Event handlers for new components
#         def apply_dense_preset():
#             return [0.3, 3, 3, 0.8]
        
#         def apply_sparse_preset():
#             return [0.8, 8, 1, 1.2]
        
#         def apply_forms_preset():
#             return [1.2, 5, 2, 1.0]
        
#         def apply_historical_preset():
#             return [0.4, 2, 2, 0.7]
        
#         # Connect preset buttons
#         dense_btn.click(
#             fn=apply_dense_preset,
#             outputs=[scale_slider, margin_slider, words_slider, text_scale_slider]
#         )
        
#         sparse_btn.click(
#             fn=apply_sparse_preset,
#             outputs=[scale_slider, margin_slider, words_slider, text_scale_slider]
#         )
        
#         forms_btn.click(
#             fn=apply_forms_preset,
#             outputs=[scale_slider, margin_slider, words_slider, text_scale_slider]
#         )
        
#         historical_btn.click(
#             fn=apply_historical_preset,
#             outputs=[scale_slider, margin_slider, words_slider, text_scale_slider]
#         )
        
#         # FIXED Export functionality
#         def handle_image_export(text, format_type):
#             """Handle export for image results"""
#             file_path = simple_export(text, format_type)
#             if file_path:
#                 return gr.update(value=file_path, visible=True)
#             else:
#                 return gr.update(visible=False)
        
#         def handle_pdf_export(text, format_type):
#             """Handle export for PDF results"""
#             file_path = simple_export(text, format_type)
#             if file_path:
#                 return gr.update(value=file_path, visible=True)
#             else:
#                 return gr.update(visible=False)
        
#         # Connect export buttons
#         export_btn.click(
#             fn=handle_image_export,
#             inputs=[text_output, export_format],
#             outputs=export_download
#         )
        
#         pdf_export_btn.click(
#             fn=handle_pdf_export,
#             inputs=[pdf_text_output, pdf_export_format],
#             outputs=pdf_export_download
#         )
        
#         # Cache management
#         def clear_cache():
#             pdf_processor.clear_cache()
#             return "✅ System cache cleared successfully!"
        
#         clear_cache_btn.click(
#             fn=clear_cache,
#             outputs=settings_status
#         )
        
#         # Connect existing processing buttons
#         process_btn.click(
#             fn=process_page,
#             inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider, debug_checkbox],
#             outputs=[text_output, image_output]
#         )
        
#         pdf_process_btn.click(
#             fn=process_pdf_enhanced,
#             inputs=[pdf_input, pdf_dictionary, pdf_scale, pdf_margin, pdf_words, pdf_text_scale, pdf_debug],
#             outputs=[pdf_text_output, pdf_image_output, pdf_page_info]
#         )
        
#         # Batch processing placeholder
#         def process_batch(files, scale, margin, use_dictionary):
#             # This is a placeholder - you would implement actual batch processing
#             return {"files_processed": len(files) if files else 0, "status": "Batch processing not yet implemented"}
        
#         batch_process_btn.click(
#             fn=process_batch,
#             inputs=[batch_files, batch_scale, batch_margin, batch_dictionary],
#             outputs=batch_summary
#         )
    
#     return demo

# # Create and launch the demo
# if __name__ == "__main__":
#     demo = create_enhanced_ui()
#     demo.launch(
#         share=True,
#         show_error=True,
#         debug=True  # Set to True to see export debug messages
#     )



import json
import tempfile
import os
import io
import base64
import cv2
import gradio as gr
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from htr_pipeline import read_page, DetectorConfig, LineClusteringConfig, ReaderConfig, PrefixTree
import logging
from datetime import datetime
from functools import lru_cache
import threading
from dotenv import load_dotenv
from mistralai.client import Mistral

# Load environment variables from .env
load_dotenv()

# Setup logging
def setup_logging(debug=False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'htr_pipeline_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Enhanced Configuration Management
class Config:
    def __init__(self, config_path='data/config.json'):
        self.config_path = config_path
        self.config = {}
        self.prefix_tree = None
        self.load_config()
        self.load_dictionary()
    
    def load_config(self):
        """Load configuration with fallbacks"""
        try:
            with open(self.config_path) as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}
            logger.warning(f"Config file {self.config_path} not found, using defaults")
    
    def load_dictionary(self):
        """Load dictionary with error handling"""
        try:
            with open('data/words_alpha.txt') as f:
                word_list = [w.strip().upper() for w in f.readlines()]
            self.prefix_tree = PrefixTree(word_list)
            logger.info(f"Loaded dictionary with {len(word_list)} words")
        except FileNotFoundError:
            logger.warning("Dictionary file not found, word beam search will be limited")
            self.prefix_tree = None
    
    def get_example_config(self, example_key):
        """Get configuration for example with defaults"""
        return self.config.get(example_key, {
            'scale': 1.0,
            'margin': 5,
            'text_scale': 1.0
        })

# Initialize config
config = Config()

# Create examples for image tab
examples = []
if config.config:
    for k, v in config.config.items():
        examples.append([f'data/{k}', v['scale'], v['margin'], False, 2, v['text_scale']])

# Enhanced PDF Processor with caching
class CachedPDFProcessor:
    def __init__(self, poppler_path=None, dpi=200):
        self.poppler_path = poppler_path
        self.dpi = dpi
        self._cache = {}
        self._lock = threading.Lock()
    
    def find_poppler(self):
        """Try to automatically find Poppler installation"""
        possible_paths = [
            r"C:\poppler\poppler\Library\bin",
            r"C:\poppler\bin",
            r"C:\Program Files\poppler\bin",
            r"C:\Program Files (x86)\poppler\bin",
            "/usr/bin",  # Linux
            "/usr/local/bin",  # macOS
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found Poppler at: {path}")
                return path
        logger.warning("Poppler not found in common locations")
        return None
    
    @lru_cache(maxsize=10)
    def get_pdf_images_cached(self, pdf_path, dpi):
        """Cache PDF conversions for same file and DPI"""
        return self.pdf_to_images(pdf_path)
    
    def pdf_to_images(self, pdf_path):
        """Convert PDF to list of OpenCV images"""
        poppler_path = self.poppler_path or self.find_poppler()
        
        if not poppler_path:
            raise RuntimeError("Poppler not found. Please install from: https://github.com/oschwartz10612/poppler-windows/releases/")
        
        logger.info(f"Converting PDF to images using Poppler path: {poppler_path}")
        pil_images = convert_from_path(pdf_path, dpi=self.dpi, poppler_path=poppler_path)
        
        cv2_images = []
        for pil_image in pil_images:
            if pil_image.mode != 'L':
                pil_image = pil_image.convert('L')
            cv2_img = np.array(pil_image)
            cv2_images.append(cv2_img)
        
        logger.info(f"Converted {len(cv2_images)} pages from PDF")
        return cv2_images
    
    def clear_cache(self):
        """Clear the cache"""
        self.get_pdf_images_cached.cache_clear()
        self._cache.clear()
        logger.info("PDF processor cache cleared")

# Initialize PDF processor
pdf_processor = CachedPDFProcessor()

# Input Validation
def validate_inputs(scale, margin, min_words_per_line, text_scale):
    """Validate input parameters"""
    if scale <= 0:
        raise ValueError("Scale must be positive")
    if margin < 0:
        raise ValueError("Margin cannot be negative")
    if min_words_per_line < 1:
        raise ValueError("Minimum words per line must be at least 1")
    if text_scale <= 0:
        raise ValueError("Text scale must be positive")
    return True

# Parameter Presets
def create_parameter_presets():
    """Create parameter presets for different document types"""
    presets = {
        "dense_handwriting": {"scale": 0.3, "margin": 3, "min_words_per_line": 3, "text_scale": 0.8},
        "sparse_handwriting": {"scale": 0.8, "margin": 8, "min_words_per_line": 1, "text_scale": 1.2},
        "printed_forms": {"scale": 1.2, "margin": 5, "min_words_per_line": 2, "text_scale": 1.0},
        "historical_documents": {"scale": 0.4, "margin": 2, "min_words_per_line": 2, "text_scale": 0.7},
    }
    return presets

# Mistral OCR text extraction
def extract_text_with_mistral(img):
    """Extract text from an image using Mistral OCR API"""
    try:
        # Reload .env each time so key changes take effect without restart
        load_dotenv(override=True)
        api_key = os.getenv('MISTRAL_API_KEY')
        if not api_key:
            return "Error: MISTRAL_API_KEY not found in .env file. Get a free key at https://console.mistral.ai/"
        
        client = Mistral(api_key=api_key)
        
        # Convert numpy array to PIL Image, then to base64
        if len(img.shape) == 2:  # Grayscale
            pil_img = Image.fromarray(img, mode='L').convert('RGB')
        else:  # RGB/BGR
            if img.shape[2] == 3:
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            else:
                pil_img = Image.fromarray(img)
        
        # Encode image as base64
        buffer = io.BytesIO()
        pil_img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        image_data_url = f"data:image/png;base64,{img_base64}"
        
        # Call Mistral OCR
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": image_data_url
            }
        )
        
        # Extract text from all pages in the response
        extracted_text = ""
        if ocr_response and ocr_response.pages:
            for page in ocr_response.pages:
                extracted_text += page.markdown + "\n"
        
        if extracted_text.strip():
            logger.info(f"Local LLM extracted {len(extracted_text)} characters")
            return extracted_text.strip()
        else:
            return "Error: Mistral OCR returned an empty response"
    
    except Exception as e:
        error_msg = f"Local LLM Model Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

# SAFE Processing Function with error handling for '+' issue
def safe_process_page(img, scale, margin, use_dictionary, min_words_per_line, text_scale, debug=False, use_cloud_ocr=False):
    """Safe version of process_page that handles the '+' error"""
    try:
        if img is None:
            return "Please provide an image", None, []
        
        # --- Cloud OCR (Mistral) path ---
        if use_cloud_ocr:
            logger.info("Using Local LLM for text extraction")
            text = extract_text_with_mistral(img)
            # Return original image as visualization (no bounding boxes)
            if len(img.shape) == 2:
                vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                vis_img = img.copy()
            return text, vis_img, []
        
        # --- Local ONNX path (unchanged) ---
        # Input validation
        validate_inputs(scale, margin, min_words_per_line, text_scale)
        
        if img is None:
            return "Please provide an image", None, []
            
        logger.info(f"Processing image with scale={scale}, margin={margin}, use_dict={use_dictionary}")
        
        # Convert if image is from Gradio (RGB)
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Resize very large images for faster processing
        height, width = img.shape
        max_dimension = 2000
        if max(float(height), float(width)) > max_dimension:
            scale_factor = max_dimension / max(float(height), float(width))
            new_width = int(float(width) * scale_factor)
            new_height = int(float(height) * scale_factor)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            if debug:
                print(f"DEBUG: Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Try to read page with error handling
        try:
            read_lines = read_page(img,
                                   detector_config=DetectorConfig(scale=scale, margin=margin),
                                   line_clustering_config=LineClusteringConfig(min_words_per_line=min_words_per_line),
                                   reader_config=ReaderConfig(decoder='word_beam_search' if use_dictionary else 'best_path',
                                                              prefix_tree=config.prefix_tree if use_dictionary else None))
        except ValueError as e:
            if "'+' is not in list" in str(e):
                logger.warning(f"Encountered '+' error. Trying alternative parameters...")
                # Try with simpler parameters
                read_lines = read_page(img,
                                       detector_config=DetectorConfig(scale=1.0, margin=10),
                                       line_clustering_config=LineClusteringConfig(min_words_per_line=1),
                                       reader_config=ReaderConfig(decoder='best_path'))
            else:
                raise e  # Re-raise other ValueErrors
        
        # create text to show
        res = ''
        for read_line in read_lines:
            res += ' '.join(read_word.text for read_word in read_line) + '\n'

        # create visualization to show with improved styling
        if len(img.shape) == 2:
            vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            vis_img = img.copy()
        
        # Color scheme: Teal and Coral for better visibility
        bbox_color = (0, 128, 128)  # Teal
        text_color = (255, 255, 255)  # White for better contrast
        
        for i, read_line in enumerate(read_lines):
            for read_word in read_line:
                aabb = read_word.aabb
                # Draw bounding box
                cv2.rectangle(vis_img,
                              (aabb.xmin, aabb.ymin),
                              (aabb.xmax, aabb.ymax),
                              bbox_color,
                              2)
                # Draw text with improved font and styling
                cv2.putText(vis_img,
                            read_word.text,
                            (aabb.xmin, aabb.ymin - 5),
                            cv2.FONT_HERSHEY_COMPLEX,  # Changed to COMPLEX for better readability
                            text_scale,
                            color=text_color,
                            thickness=1 if text_scale < 1.0 else 2)  # Thinner text for smaller scale
        
        logger.info(f"Processed image successfully, found {len(read_lines)} lines")
        return res, vis_img, read_lines

    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        logger.error(f"Error in process_page: {str(e)}", exc_info=True)
        
        # Create a basic visualization even on error
        if 'img' in locals() and img is not None:
            if len(img.shape) == 2:
                vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                vis_img = img.copy()
            # Add error message to image
            cv2.putText(vis_img, "Processing Error", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            vis_img = None
            
        if debug:
            error_msg += f"\n\nDetailed error: {repr(e)}"
        return error_msg, vis_img, []

def process_pdf_enhanced(pdf_file, use_dictionary, scale, margin, min_words_per_line, text_scale, debug=False, use_cloud_ocr=False):
    """Enhanced PDF processing with progress and better error handling"""
    if pdf_file is None:
        return "Please upload a PDF file", None, "**Status:** Waiting for PDF upload..."
    
    try:
        # Get PDF path safely
        if hasattr(pdf_file, 'name'):
            pdf_path = pdf_file.name
        else:
            pdf_path = str(pdf_file)
        
        # Validate PDF file
        if not os.path.exists(pdf_path):
            return f"File not found: {pdf_path}", None, "**Status:** File not found"
            
        if not pdf_path.lower().endswith('.pdf'):
            return "Please upload a valid PDF file", None, "**Status:** Invalid file type"
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Convert PDF to images
        images = pdf_processor.pdf_to_images(pdf_path)
        
        if not images:
            return "No pages found in PDF", None, "**Status:** No pages found in PDF"
        
        # Process pages
        full_text = ""
        visualization_images = []
        total_words = 0
        total_lines = 0
        errors = []
        
        for page_num, image in enumerate(images):
            try:
                if debug:
                    print(f"DEBUG: Processing page {page_num + 1}/{len(images)}")
                
                page_text, vis_img, read_lines = safe_process_page(
                    image, scale, margin, use_dictionary, min_words_per_line, 
                    text_scale, debug=debug, use_cloud_ocr=use_cloud_ocr
                )
                
                # Safely calculate statistics
                if read_lines and isinstance(read_lines, list):
                    word_count = sum(len(line) for line in read_lines)
                    line_count = len(read_lines)
                else:
                    word_count = 0
                    line_count = 0
                
                total_words += word_count
                total_lines += line_count
                
                full_text += f"--- Page {page_num + 1} (Words: {word_count}, Lines: {line_count}) ---\n{page_text}\n\n"
                visualization_images.append(vis_img)
                
            except Exception as e:
                error_msg = f"Error processing page {page_num + 1}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                full_text += f"--- Page {page_num + 1} (Error) ---\n{error_msg}\n\n"
                # Add placeholder image
                if len(image.shape) == 2:
                    vis_img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                else:
                    vis_img = image.copy()
                visualization_images.append(vis_img)
        
        # Build summary
        summary = f"PDF Processing Summary:\nTotal Pages: {len(images)}\nTotal Lines: {total_lines}\nTotal Words: {total_words}"
        
        if errors:
            summary += f"\n\nErrors encountered: {len(errors)} pages"
            if debug:
                for err in errors:
                    summary += f"\n- {err}"
        
        full_text = summary + "\n\n" + full_text
        
        # Create page navigation info
        page_info = f"**Status:** Processed {len(images)} pages"
        if total_words > 0:
            page_info += f", {total_words} words across {total_lines} lines."
        else:
            page_info += ". No text detected."
        
        if errors:
            page_info += f" ({len(errors)} pages had errors)"
        
        logger.info(f"PDF processing completed: {len(images)} pages, {total_words} words")
        
        # Return first visualization if available
        vis_output = visualization_images[0] if visualization_images else None
        return full_text, vis_output, page_info
        
    except Exception as e:
        error_msg = f"Error processing PDF: {str(e)}"
        logger.error(f"Error in process_pdf_enhanced: {str(e)}", exc_info=True)
        if debug:
            import traceback
            error_msg += f"\n\nTraceback:\n{traceback.format_exc()}"
        error_msg += "\n\nPlease ensure Poppler is installed from: https://github.com/oschwartz10612/poppler-windows/releases/"
        return error_msg, None, "**Status:** Error processing PDF"

# FIXED Export functionality
def simple_export(text, format_type):
    """Simple reliable export function that returns file paths"""
    if not text or len(text.strip()) < 5:  # Reduced minimum for error messages
        print("No valid text to export")
        return None
    
    try:
        # Create a named temporary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "txt":
            filename = f"htr_export_{timestamp}.txt"
        else:
            filename = f"htr_export_{timestamp}.json"
        
        # Create temporary file in system temp directory
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        
        if format_type == "txt":
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
        else:  # json
            # Simple JSON structure
            lines = [line for line in text.split('\n') if line.strip()]
            data = {
                "exported_at": datetime.now().isoformat(),
                "content": text,
                "line_count": len(lines),
                "word_count": len(text.split())
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Export created: {filepath}")
        return filepath
            
    except Exception as e:
        print(f"❌ Export error: {e}")
        return None

# Create the enhanced UI with improved color scheme
def create_enhanced_ui():
    """Create enhanced Gradio interface with improved design"""
    
    custom_css = """
    /* Core Variables */
    :root {
      --app-bg: #0f172a;
      --panel-bg: rgba(30, 41, 59, 0.45);
      --accent-1: #3b82f6;
      --accent-2: #8b5cf6;
      --accent-glow: rgba(139, 92, 246, 0.5);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --border-color: rgba(255, 255, 255, 0.08);
    }
    @media (prefers-color-scheme: light) {
      :root {
        --app-bg: #f8fafc;
        --panel-bg: rgba(255, 255, 255, 0.6);
        --accent-1: #2563eb;
        --accent-2: #7c3aed;
        --accent-glow: rgba(124, 58, 237, 0.4);
        --text-main: #0f172a;
        --text-muted: #475569;
        --border-color: rgba(0, 0, 0, 0.08);
      }
    }
    
    /* Global Background and Animations */
    @keyframes fadeInScale { 
        0% { opacity: 0; transform: translateY(15px) scale(0.98); } 
        100% { opacity: 1; transform: translateY(0) scale(1); } 
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    body, .gradio-container { 
        background-color: var(--app-bg) !important; 
        color: var(--text-main) !important; 
        font-family: 'Inter', system-ui, sans-serif !important;
        background-image: radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.15), transparent 30%), 
                          radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.15), transparent 30%);
        background-attachment: fixed;
    }
    
    /* Glassmorphic Panels */
    .gr-box, .panel-block, .gradio-container > .main, .gr-form, .gr-panel, div[role="group"] {
        background: var(--panel-bg) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        animation: fadeInScale 0.6s ease-out forwards;
    }
    .gr-box:hover, div[role="group"]:hover {
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.4) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-2px);
    }
    
    /* Headers & Typography */
    .title-header { display: flex; align-items: center; gap: 15px; margin-bottom: -5px; }
    .logo-icon { 
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); 
        color: white; padding: 8px 14px; border-radius: 12px; font-weight: 800; font-size: 20px;
        box-shadow: 0 0 15px var(--accent-glow);
        animation: pulse 2.5s infinite alternate;
    }
    @keyframes pulse { 
        from { box-shadow: 0 0 10px var(--accent-glow); transform: scale(1); } 
        to { box-shadow: 0 0 25px var(--accent-glow); transform: scale(1.05); } 
    }
    .title-text h1 { 
        color: var(--text-main) !important; 
        font-size: 32px !important; margin: 0 !important; font-weight: 800 !important;
        background: linear-gradient(to right, var(--text-main), var(--text-muted));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .subtitle { color: var(--text-muted); font-size: 15px; margin-top: 5px; margin-bottom: 25px; letter-spacing: 0.5px; font-weight: 500; }
    
    /* Dynamic Buttons */
    button { 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; 
        border-radius: 12px !important; 
        font-weight: 700 !important; 
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        font-size: 14px !important;
    }
    button:hover { transform: translateY(-3px) scale(1.02) !important; }
    button:active { transform: translateY(1px) scale(0.98) !important; }
    
    .process-btn { 
        background: linear-gradient(270deg, var(--accent-1), var(--accent-2), var(--accent-1)) !important; 
        background-size: 200% 200% !important;
        animation: gradientBG 4s ease infinite !important;
        border: none !important; color: white !important; 
        box-shadow: 0 8px 20px 0 var(--accent-glow) !important;
        margin-top: 20px !important;
        height: 56px !important;
    }
    .process-btn:hover { box-shadow: 0 12px 30px var(--accent-glow) !important; filter: brightness(1.15); }
    
    .export-btn { 
        background: linear-gradient(135deg, #10b981, #059669) !important; 
        border: none !important; color: white !important; 
        box-shadow: 0 4px 15px 0 rgba(16, 185, 129, 0.4) !important; 
    }
    .export-btn:hover { box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6) !important; }
    
    /* Inputs, Sliders and Forms */
    input, textarea, select, .gr-input, input[type="range"] { 
        background-color: rgba(0,0,0,0.25) !important; 
        border: 1px solid var(--border-color) !important; 
        color: var(--text-main) !important; 
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    @media (prefers-color-scheme: light) {
        input, textarea, select, .gr-input, input[type="range"] { background-color: rgba(255,255,255,0.7) !important; }
    }
    input:focus, textarea:focus, select:focus, input:hover, textarea:hover { 
        border-color: var(--accent-1) !important; 
        box-shadow: 0 0 0 3px var(--accent-glow) !important; 
        transform: translateY(-1px);
        background-color: rgba(0,0,0,0.4) !important;
    }
    
    /* Tabs & Navigation */
    .tabs { border-bottom: none !important; background: transparent !important; margin-top: 10px; }
    .tab-nav { border-bottom: 1px solid var(--border-color) !important; margin-bottom: 25px !important; gap: 15px !important;}
    .tab-nav button { 
        background-color: transparent !important; 
        border: none !important; 
        border-bottom: 3px solid transparent !important;
        border-radius: 0 !important; 
        padding: 12px 10px !important; 
        color: var(--text-muted) !important; 
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
    }
    .tab-nav button:hover { color: var(--text-main) !important; transform: translateY(-2px) !important; }
    .tab-nav button.selected { 
        background-color: transparent !important; 
        border-bottom: 3px solid var(--accent-1) !important; 
        color: var(--accent-1) !important; 
        text-shadow: 0 0 10px var(--accent-glow);
    }
    
    /* Status Labels */
    .status-prepare { 
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15));
        border: 1px solid var(--accent-glow); 
        border-left: 5px solid var(--accent-1);
        border-radius: 12px; padding: 15px 25px; color: var(--text-main); font-weight: 700; margin-bottom: 30px; 
        display: flex; gap: 15px; align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .footer-status { 
        background: var(--panel-bg); backdrop-filter: blur(10px);
        border: 1px solid var(--border-color); border-radius: 14px; padding: 15px 25px; margin-top: 40px; font-size: 14px; color: var(--text-muted); 
        display: flex; justify-content: space-between; align-items: center;
    }
    .status-tag { background-color: rgba(59, 130, 246, 0.2); border: 1px solid var(--accent-glow); color: var(--accent-1); padding: 5px 15px; border-radius: 20px; font-weight: 700;}
    
    /* Scrollbars */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 5px; border: 2px solid transparent; background-clip: padding-box; }
    ::-webkit-scrollbar-thumb:hover { background-color: rgba(255,255,255,0.4); }
    """
    
    with gr.Blocks(title="Ink2Text HTR Pipeline", theme=gr.themes.Base(), css=custom_css) as demo:
        
        gr.HTML("""
            <div class="title-header">
                <div class="logo-icon">=</div>
                <div class="title-text">
                    <h1>Ink2Text</h1>
                    <div style="color: var(--ctp-subtext0); font-size: 13px; margin-top: -2px;">Handwritten Text Recognition</div>
                </div>
            </div>
            <div class="subtitle">Transform handwritten documents into digital text with AI-powered precision</div>
        """)
        
        gr.HTML("""
            <div class="status-prepare">
                <span style="font-size: 14px;">0%</span> 
                <span style="font-size: 14px;">Preparing...</span>
            </div>
        """)
        
        with gr.Tab("🖼️ Single Image Processing"):
            gr.Markdown("### Process Individual Handwritten Images")
            
            with gr.Row(equal_height=False):
                with gr.Column(scale=1):
                    image_input = gr.Image(label='Upload Handwritten Image', type="numpy", height=300)
                    
                    with gr.Group():
                        with gr.Accordion("⚙️ Parameters", open=True):
                            with gr.Row():
                                compute_dropdown = gr.Dropdown(choices=["GPU (CUDA)", "CPU"], value="GPU (CUDA)", label="Compute", interactive=True)
                                scale_slider = gr.Slider(0.01, 15, 1, step=0.01, label='Detection Scale') 
                            with gr.Row():
                                margin_slider = gr.Slider(0, 20, 5, step=1, label='Text Margin')
                                dictionary_checkbox = gr.Checkbox(value=True, label='Use Dictionary for Better Accuracy')
                            with gr.Row():
                                words_slider = gr.Slider(1, 10, 2, step=1, label='Minimum Words Per Line')
                                text_scale_slider = gr.Slider(0.5, 2.0, 1.0, step=0.1, label='Visualization Text Size')
                            with gr.Row():
                                debug_checkbox = gr.Checkbox(value=False, label='Enable Debug Mode')
                                flip_checkbox = gr.Checkbox(value=False, label='Flip Image (Webcam Fix)')
                            with gr.Row():
                                cloud_ocr_checkbox = gr.Checkbox(value=False, label='🤖 Use Local LLM Model (Advanced Accuracy)')
                        
                    process_btn = gr.Button("🎯 Process Image", variant="primary", size="lg", elem_classes="process-btn")
                
                with gr.Column(scale=1):
                    with gr.Group():
                        text_output = gr.Textbox(label='Extracted Text', lines=12)
                        with gr.Row():
                            export_format = gr.Radio(["txt", "json"], value="txt", label="Export Format", interactive=True)
                            export_btn = gr.Button("💾 Export Results", variant="secondary", elem_classes="export-btn")
                        export_download = gr.File(label="Download Export", visible=False, file_count="single", height=50)
                    
                    image_output = gr.Image(label='Text Detection Visualization', height=400)
            
            # Examples for image tab
            if examples:
                gr.Examples(
                    examples=examples,
                    inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider],
                    outputs=[text_output, image_output],
                    label="🖼️ Example Images"
                )
        
        with gr.Tab("📄 PDF Document Processing"):
            gr.Markdown("### Process Multi-page PDF Documents")
            
            with gr.Row(equal_height=False):
                with gr.Column(scale=1):
                    pdf_input = gr.File(label="Upload PDF Document", file_types=[".pdf"], height=50)
                    
                    with gr.Group():
                        with gr.Accordion("⚙️ Processing Parameters", open=True):
                            pdf_scale = gr.Slider(0.01, 15, 1, step=0.01, label='Detection Scale') 
                            pdf_margin = gr.Slider(0, 20, 5, step=1, label='Text Margin')
                            pdf_dictionary = gr.Checkbox(value=False, label='Use Dictionary for Better Accuracy')
                            pdf_words = gr.Slider(1, 10, 2, step=1, label='Minimum Words Per Line')
                            pdf_text_scale = gr.Slider(0.5, 2.0, 1.0, step=0.1, label='Visualization Text Size')
                            pdf_debug = gr.Checkbox(value=False, label='Enable Debug Mode')
                            pdf_cloud_ocr = gr.Checkbox(value=False, label='🤖 Use Local LLM Model (Advanced Accuracy)')
                        
                    pdf_process_btn = gr.Button("🎯 Process PDF Document", variant="primary", size="lg", elem_classes="process-btn")
                
                with gr.Column(scale=1):
                    with gr.Group():
                        pdf_text_output = gr.Textbox(label='Extracted Text from All Pages', lines=12)
                        with gr.Row():
                            pdf_export_format = gr.Radio(["txt", "json"], value="txt", label="Export Format", interactive=True)
                            pdf_export_btn = gr.Button("💾 Export Results", variant="secondary", elem_classes="export-btn")
                        pdf_export_download = gr.File(label="Download Export", visible=False, file_count="single", height=50)
                    
                    pdf_image_output = gr.Image(label='First Page Visualization', height=400)
                    pdf_page_info = gr.Markdown("**Status:** Ready to process PDF documents")
        
        with gr.Tab("⚙️ Settings & Configuration"):
            gr.Markdown("### Application Settings & System Configuration")
            
            with gr.Row(equal_height=False):
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.Markdown("#### Performance Settings")
                        cache_size = gr.Slider(1, 100, 10, label="Cache Size (files)")
                        auto_save = gr.Checkbox(value=True, label="Auto-save Results")
                        default_params = gr.Button("🔄 Reset to Default Parameters", variant="secondary")
                
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.Markdown("#### System Operations")
                        clear_cache_btn = gr.Button("🗑️ Clear System Cache", variant="secondary")
                        export_settings = gr.Button("📤 Export Application Settings", variant="secondary")
                        settings_status = gr.Markdown("")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("""
                    <div class="warning-box" style="background-color: var(--ctp-mantle); border: 1px solid var(--ctp-border); border-radius: 8px; padding: 15px; margin-top: 20px;">
                    <strong>⚙️ System Requirements:</strong>
                    <ul style="color: var(--ctp-text);">
                    <li>Poppler required for PDF processing</li>
                    <li>Minimum 2GB RAM recommended</li>
                    <li>Internet connection for dictionary lookup</li>
                    <li>Modern web browser with JavaScript enabled</li>
                    </ul>
                    </div>
                    """)
        
        # Footer
        gr.HTML("""
        <div class="footer-status">
            <span>Execution Provider</span>
            <span class="status-tag">Not run</span>
        </div>
        """)
        
        # Export functionality
        def handle_image_export(text, format_type):
            """Handle export for image results"""
            file_path = simple_export(text, format_type)
            if file_path:
                return gr.update(value=file_path, visible=True)
            else:
                return gr.update(value=None, visible=False)
        
        def handle_pdf_export(text, format_type):
            """Handle export for PDF results"""
            file_path = simple_export(text, format_type)
            if file_path:
                return gr.update(value=file_path, visible=True)
            else:
                return gr.update(value=None, visible=False)
        
        # Connect export buttons
        export_btn.click(
            fn=handle_image_export,
            inputs=[text_output, export_format],
            outputs=export_download
        )
        
        pdf_export_btn.click(
            fn=handle_pdf_export,
            inputs=[pdf_text_output, pdf_export_format],
            outputs=pdf_export_download
        )
        
        # Cache management
        def clear_cache():
            pdf_processor.clear_cache()
            return "✅ System cache cleared successfully!"
        
        clear_cache_btn.click(
            fn=clear_cache,
            outputs=settings_status
        )
        
        # Connect processing buttons - use safe_process_page for single image
        def safe_process_page_wrapper(img, scale, margin, use_dictionary, min_words_per_line, text_scale, debug, flip_image, use_cloud_ocr):
            if img is not None and flip_image:
                import cv2
                img = cv2.flip(img, 1)
            text, vis_img, _ = safe_process_page(img, scale, margin, use_dictionary, min_words_per_line, text_scale, debug, use_cloud_ocr=use_cloud_ocr)
            return text, vis_img
        
        process_btn.click(
            fn=safe_process_page_wrapper,
            inputs=[image_input, scale_slider, margin_slider, dictionary_checkbox, words_slider, text_scale_slider, debug_checkbox, flip_checkbox, cloud_ocr_checkbox],
            outputs=[text_output, image_output]
        )
        
        pdf_process_btn.click(
            fn=process_pdf_enhanced,
            inputs=[pdf_input, pdf_dictionary, pdf_scale, pdf_margin, pdf_words, pdf_text_scale, pdf_debug, pdf_cloud_ocr],
            outputs=[pdf_text_output, pdf_image_output, pdf_page_info]
        )
    
    return demo

# Create and launch the demo
if __name__ == "__main__":
    demo = create_enhanced_ui()
    demo.launch(
        share=True,
        show_error=True,
        debug=True
    )