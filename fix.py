import pathlib
path = pathlib.Path('scripts/pdf_gradio_demo.py')
lines = path.read_text(encoding='utf-8').splitlines(True)
# Delete lines 342 to 372 (0-indexed)
del lines[342:373]
path.write_text(''.join(lines), encoding='utf-8')
print("Lines deleted.")
