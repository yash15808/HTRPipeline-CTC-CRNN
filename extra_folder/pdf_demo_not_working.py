import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from htr_pipeline import read_page, DetectorConfig, LineClusteringConfig, ReaderConfig

class PDFProcessor:
    def __init__(self, poppler_path=None, dpi=200):
        """
        Initialize PDF processor with HTR capabilities
        :param poppler_path: Path to poppler bin directory
        :param dpi: Resolution for image conversion
        """
        self.poppler_path = poppler_path
        self.dpi = dpi

    def find_poppler(self):
        """Try to automatically find Poppler installation"""
        possible_paths = [
            r"C:\poppler\poppler\Library\bin",
            r"C:\Program Files\poppler\bin",
            r"C:\poppler\bin",
            r"C:\Users\{}\AppData\Local\Programs\poppler\bin".format(os.getenv('USERNAME')),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def pdf_to_images(self, pdf_path, output_dir=None):
        """
        Convert PDF to OpenCV images (in memory) or save to files
        :param pdf_path: Path to the PDF file
        :param output_dir: Optional directory to save images
        :return: List of OpenCV images or image paths
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        poppler_path = self.poppler_path or self.find_poppler()
        if poppler_path is None:
            raise RuntimeError("Poppler not found. Please install Poppler.")

        print(f"Converting PDF '{os.path.basename(pdf_path)}' to images (DPI={self.dpi})...")

        # Convert to PIL images
        pil_images = convert_from_path(
            pdf_path,
            dpi=self.dpi,
            poppler_path=poppler_path
        )

        cv2_images = []
        image_paths = []

        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        for i, pil_image in enumerate(pil_images, start=1):
            # Convert PIL to OpenCV format (grayscale)
            if pil_image.mode != 'L':
                pil_image = pil_image.convert('L')
            cv2_img = np.array(pil_image)
            cv2_images.append(cv2_img)

            # Save image if output directory specified
            if output_dir:
                image_path = os.path.join(output_dir, f"page_{i:03d}.png")
                pil_image.save(image_path, "PNG")
                image_paths.append(image_path)
                print(f"Saved page {i} -> {image_path}")

        return cv2_images if not output_dir else image_paths

    def process_pdf_with_htr(self, pdf_path, output_dir=None, 
                           scale=0.4, margin=5, min_words_per_line=2, 
                           decoder='best_path', use_dictionary=False):
        """
        Complete PDF to text processing with HTR
        :param pdf_path: Path to PDF file
        :param output_dir: Directory to save extracted images
        :param scale: Detector scale parameter
        :param margin: Detector margin parameter
        :param min_words_per_line: Minimum words per line for clustering
        :param decoder: Text decoder ('best_path' or 'word_beam_search')
        :param use_dictionary: Whether to use dictionary for word beam search
        :return: List of results with text and metadata
        """
        # Convert PDF to OpenCV images
        images = self.pdf_to_images(pdf_path, output_dir)
        
        results = []
        
        for page_num, image in enumerate(images, start=1):
            print(f"Processing page {page_num}...")
            
            # Process with HTR pipeline
            read_lines = read_page(
                image,
                detector_config=DetectorConfig(scale=scale, margin=margin),
                line_clustering_config=LineClusteringConfig(min_words_per_line=min_words_per_line),
                reader_config=ReaderConfig(
                    decoder=decoder,
                    prefix_tree=None  # You can add prefix_tree if using dictionary
                )
            )
            
            # Extract text
            page_text = ""
            for read_line in read_lines:
                page_text += ' '.join(read_word.text for read_word in read_line) + "\n"
            
            results.append({
                'page_number': page_num,
                'text': page_text.strip(),
                'lines_count': len(read_lines),
                'words_count': sum(len(line) for line in read_lines),
                'image_shape': image.shape
            })
            
            print(f"Page {page_num} processed: {len(read_lines)} lines, {sum(len(line) for line in read_lines)} words")
        
        return results

    def process_pdf_to_files(self, pdf_path, output_dir="output_pages", **htr_kwargs):
        """
        Process PDF and save results to text files
        """
        results = self.process_pdf_with_htr(pdf_path, output_dir, **htr_kwargs)
        
        # Save individual page results
        for result in results:
            text_filename = os.path.join(output_dir, f"page_{result['page_number']:03d}.txt")
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            print(f"Saved text: {text_filename}")
        
        # Save combined results
        combined_text = "\n".join([f"--- Page {r['page_number']} ---\n{r['text']}\n" for r in results])
        combined_filename = os.path.join(output_dir, "combined_results.txt")
        with open(combined_filename, 'w', encoding='utf-8') as f:
            f.write(combined_text)
        
        print(f"Saved combined results: {combined_filename}")
        
        return results

# Example usage and demonstration
if __name__ == "__main__":
    def demo_htr_pipeline():
        """Demonstrate the complete HTR PDF processing pipeline"""
        
        # Initialize processor
        processor = PDFProcessor(dpi=200)
        
        # PDF file to process (change this to your PDF path)
        pdf_path = "data/sample.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            print("Please create a sample PDF or update the path")
            return
        
        try:
            # Option 1: Process and get results in memory
            print("=" * 60)
            print("PROCESSING PDF WITH HTR (IN MEMORY)")
            print("=" * 60)
            
            results = processor.process_pdf_with_htr(
                pdf_path,
                scale=0.4,
                margin=5,
                min_words_per_line=2,
                decoder='best_path'
            )
            
            # Display results
            print("\nEXTRACTION RESULTS:")
            print("=" * 40)
            for result in results:
                print(f"Page {result['page_number']}:")
                print(f"Lines: {result['lines_count']}, Words: {result['words_count']}")
                print("Text:")
                print(result['text'])
                print("-" * 40)
            
            # Option 2: Process and save to files
            print("\n" + "=" * 60)
            print("PROCESSING PDF WITH HTR (SAVE TO FILES)")
            print("=" * 60)
            
            results = processor.process_pdf_to_files(
                pdf_path,
                output_dir="extracted_results",
                scale=0.2,
                margin=3,
                min_words_per_line=5,
                decoder='best_path'
            )
            
            print(f"\nProcessing complete! Check the 'extracted_results' folder.")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("\nTroubleshooting tips:")
            print("1. Ensure Poppler is installed")
            print("2. Check PDF file exists")
            print("3. Verify HTR model files are in place")

    # Run the demo
    demo_htr_pipeline()