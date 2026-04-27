# Ink2Text: Handwritten Text Recognition (HTR) Pipeline

This is an advanced **Handwritten Text Recognition (HTR) pipeline** that operates on **scanned pages, images, and PDFs** to seamlessly digitize handwritten and printed content.

## Features
* Detect words and lines from dense, sparse, and varied handwriting styles
* Read detected words using CRNN and CTC decoder
* Support for local Cloud OCR processing (via Mistral) for high accuracy
* Advanced visual UI powered by Gradio 
* Multi-page PDF Processing support

## Installation

### Prerequisites
For PDF processing, you need to install **Poppler** on your system:
- **Windows**: Download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/) and add its `bin/` directory to your system PATH.
- **Linux**: `sudo apt-get install poppler-utils`
- **macOS**: `brew install poppler`

### Install Dependencies
You can install the required packages using the newly created `requirements.txt`:

```bash
pip install -r requirements.txt
```

Alternatively, you can install the package and its basic dependencies directly:
```bash
pip install -e .
```

## Usage

### Run the Web UI (Gradio)

The web interface is the recommended way to use Ink2Text, offering full PDF support and interactive configurations.

1. Go to the root directory of the repository
2. Run the Gradio demo:
   ```bash
   python scripts/pdf_gradio_demo.py
   ```
3. Open the URL shown in your terminal (usually `http://127.0.0.1:7860/`).

### Use Python Package

Import the function `read_page` to detect and read text programmatically.

```python
import cv2
from htr_pipeline import read_page, DetectorConfig, LineClusteringConfig

# Read image
img = cv2.imread('data/sample_1.png', cv2.IMREAD_GRAYSCALE)

# Detect and read text
read_lines = read_page(img, 
                       detector_config=DetectorConfig(scale=0.4, margin=5), 
                       line_clustering_config=LineClusteringConfig(min_words_per_line=2))

# Output text
for read_line in read_lines:
    print(' '.join(read_word.text for read_word in read_line))
```

## Selection of Parameters

Configuration is done by passing instances of these dataclasses to the `read_page` function:
* `DetectorConfig`: configure the word detector
* `LineClusteringConfig`: configure the line clustering algorithm
* `ReaderConfig`: configure the text reader

**Scale**
The most important parameter for the detector is the scale. The detector works best for text of height 50px. 
Setting a scale != 1 automatically resizes the image before applying the detector.
*Example: Text height h is 100px in the original image. Set the scale to 0.5 so that detection happens at the ideal text size.*

**Margin**
The second most important parameter for the detector is the margin. 
It allows adding a few pixels around the detected words which might improve reading quality.

**Minimum Words Per Line**
For the line clustering algorithm, the minimum number of words can be set with the parameter `min_words_per_line`. Lines which contain fewer words will be ignored.
*Example: if it is known that all lines contain 2 or more words, set the parameter to 2 to ignore false positive detections that form lines with only a single word.*
