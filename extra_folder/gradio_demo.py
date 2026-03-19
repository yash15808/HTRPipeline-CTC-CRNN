import json
import os
import tempfile
import cv2
import numpy as np
from pdf2image import convert_from_path
from htr_pipeline import read_page, DetectorConfig, LineClusteringConfig, ReaderConfig, PrefixTree

# ==================== SIMPLE PDF PROCESSOR ====================
class SimplePDFProcessor:
    def __init__(self, poppler_path=None, dpi=200):
        self.poppler_path = poppler_path
        self.dpi = dpi
        
    def find_poppler(self):
        """Find Poppler installation"""
        paths_to_try = [
            r"C:\poppler\poppler\Library\bin",
            r"C:\poppler\bin",
            r"C:\Program Files\poppler\bin",
        ]
        for path in paths_to_try:
            if os.path.exists(path):
                return path
        return None

    def convert_pdf_to_images(self, pdf_path, output_dir=None):
        """Convert PDF to OpenCV images with optional saving"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        poppler_path = self.poppler_path or self.find_poppler()
        if not poppler_path:
            raise RuntimeError("Poppler not found. Please install from: https://github.com/oschwartz10612/poppler-windows/releases/")

        print(f"Converting PDF '{os.path.basename(pdf_path)}' to images...")
        
        # Convert PDF to PIL images
        pil_images = convert_from_path(
            pdf_path, 
            dpi=self.dpi, 
            poppler_path=poppler_path
        )
        
        # Create output directory if needed
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        cv2_images = []
        for i, pil_image in enumerate(pil_images, 1):
            # Convert to grayscale if needed
            if pil_image.mode != 'L':
                pil_image = pil_image.convert('L')
            
            # Convert to OpenCV format
            cv2_img = np.array(pil_image)
            cv2_images.append(cv2_img)
            
            # Save image if output directory specified
            if output_dir:
                image_path = os.path.join(output_dir, f"page_{i:03d}.png")
                pil_image.save(image_path, 'PNG')
                print(f"Saved: {image_path}")
        
        print(f"Converted {len(cv2_images)} pages")
        return cv2_images

# ==================== CORE HTR FUNCTIONS ====================
def load_dictionary():
    """Load dictionary for word beam search"""
    try:
        with open('data/words_alpha.txt') as f:
            word_list = [w.strip().upper() for w in f.readlines()]
        return PrefixTree(word_list)
    except:
        print("⚠️  Dictionary not found, using basic decoder")
        return None

def process_image_with_htr(image, scale=0.4, margin=5, use_dictionary=False):
    """Process single image with HTR"""
    # Ensure image is grayscale
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Choose decoder
    decoder = 'word_beam_search' if use_dictionary else 'best_path'
    prefix_tree = load_dictionary() if use_dictionary else None
    
    # Process with HTR
    read_lines = read_page(
        image,
        detector_config=DetectorConfig(scale=scale, margin=margin),
        line_clustering_config=LineClusteringConfig(min_words_per_line=2),
        reader_config=ReaderConfig(decoder=decoder, prefix_tree=prefix_tree)
    )
    
    # Extract text
    text_result = ""
    for read_line in read_lines:
        text_result += ' '.join(read_word.text for read_word in read_line) + '\n'
    
    return text_result.strip()

# ==================== MAIN PDF PROCESSING ====================
def process_pdf_file(pdf_path, output_dir=None, use_dictionary=False):
    """Main function to process PDF file"""
    processor = SimplePDFProcessor()
    
    try:
        # Convert PDF to images
        images = processor.convert_pdf_to_images(pdf_path, output_dir)
        
        results = []
        for i, image in enumerate(images, 1):
            print(f"Processing page {i}/{len(images)}...")
            
            # Process each page with HTR
            text = process_image_with_htr(image, use_dictionary=use_dictionary)
            
            results.append({
                'page': i,
                'text': text,
                'image_shape': image.shape
            })
            
            print(f"Page {i} completed")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def save_results(results, output_dir):
    """Save processing results to files"""
    if not results:
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save individual pages
    for result in results:
        text_file = os.path.join(output_dir, f"page_{result['page']:03d}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"Saved text: {text_file}")
    
    # Save combined results
    combined_file = os.path.join(output_dir, "all_pages.txt")
    with open(combined_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(f"=== Page {result['page']} ===\n")
            f.write(result['text'] + "\n\n")
    print(f"Saved combined: {combined_file}")

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    # Example usage
    pdf_file = "data/sample.pdf"  # Change this to your PDF file path
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        print("Please create a sample PDF or update the file path")
    else:
        print("=" * 60)
        print("STARTING PDF TO HTR PROCESSING")
        print("=" * 60)
        
        # Process PDF
        results = process_pdf_file(
            pdf_path=pdf_file,
            output_dir="extracted_results",
            use_dictionary=False  # Set to True if you have dictionary
        )
        
        if results:
            print("=" * 60)
            print("PROCESSING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
            # Save results
            save_results(results, "extracted_results")
            
            # Show summary
            print("\n📊 RESULTS SUMMARY:")
            for result in results:
                print(f"Page {result['page']}: {len(result['text'].split())} words")
            
            print(f"\n✅ All files saved to 'extracted_results' folder")
        else:
            print("❌ Processing failed. Please check the error messages.")