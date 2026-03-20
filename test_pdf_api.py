import sys
import os

from scripts.pdf_gradio_demo import process_pdf_enhanced

def test():
    print("Testing process_pdf_enhanced with use_cloud_ocr=True (Local LLM disguise)")
    pdf_path = "data/sample.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Test skipped: Cannot find {pdf_path}")
        return
        
    text, vis_img, page_info = process_pdf_enhanced(
        pdf_file=pdf_path,
        use_dictionary=False,
        scale=1.0,
        margin=5,
        min_words_per_line=2,
        text_scale=1.0,
        debug=True,
        use_cloud_ocr=True
    )
    
    print("\n--- RESULTS ---")
    print("Page Info:", page_info)
    print("\nExtracted Text Preview:")
    print(text[:800] if text else "None")

    if text and "Error" not in page_info and "Local LLM Error" not in text:
        print("\n>>> SUCCESS! PDF processing with 'Local LLM' API is working perfectly. <<<")
    else:
        print("\n>>> FAILED! Something went wrong. <<<")

if __name__ == "__main__":
    test()
