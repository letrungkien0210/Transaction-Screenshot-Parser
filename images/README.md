# Images Directory

Place your transaction screenshot images in this directory for processing.

## Supported Formats
- PNG (.png)
- JPEG (.jpg, .jpeg)
- TIFF (.tiff)
- BMP (.bmp)

## Usage Examples

### Process all images in this directory:
```bash
snap-transact process images/
```

### Process with custom output:
```bash
snap-transact process images/ --output output/my_transactions.csv
```

### Process single image:
```bash
snap-transact process images/transaction1.png
```

## Tips
- Use high-resolution images for better OCR accuracy
- Ensure text is clear and readable
- Avoid blurry or low-contrast images
- Maximum file size: 10MB per image 