#!/usr/bin/env python3
"""
Diagnostic script to test image extraction from PDF
Usage: python3 test_images.py <paper.pdf>
"""

import sys
import os
from paper2ppt_core.io import load_input_paper

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_images.py <paper.pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"DIAGNOSTIC: Testing image extraction from {pdf_path}")
    print(f"{'='*70}\n")
    
    # Load paper
    pages_text, pages_images = load_input_paper(pdf_path)
    
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}\n")
    
    print(f"Total pages: {len(pages_text)}")
    
    total_images = sum(len(imgs) for imgs in pages_images.values())
    print(f"Total images extracted: {total_images}\n")
    
    if total_images == 0:
        print("⚠️  WARNING: No images were extracted!")
        print("\nPossible causes:")
        print("  1. PDF has no images")
        print("  2. Images are embedded in a format PyMuPDF can't extract")
        print("  3. PDF is scanned/rasterized (images are part of page rendering)")
        print("\nTry opening the PDF and checking if it has extractable figures.")
    else:
        print("✅ Images extracted successfully!\n")
        
        for page_num, images in sorted(pages_images.items()):
            if images:
                print(f"Page {page_num + 1}: {len(images)} image(s)")
                for i, img in enumerate(images, 1):
                    path = img.get("path", "")
                    caption = img.get("caption", "")
                    
                    # Check if file exists and get size
                    if os.path.exists(path):
                        size_kb = os.path.getsize(path) / 1024
                        print(f"  [{i}] ✓ {os.path.basename(path)} ({size_kb:.1f} KB)")
                    else:
                        print(f"  [{i}] ✗ {os.path.basename(path)} (FILE NOT FOUND)")
                    
                    if caption:
                        print(f"      Caption: {caption[:100]}{'...' if len(caption) > 100 else ''}")
                print()
        
        # Check output directory
        outdir = "./paper2ppt_figs"
        if os.path.exists(outdir):
            files = os.listdir(outdir)
            print(f"\nOutput directory '{outdir}' contains {len(files)} files")
            print(f"You can view these images to verify they were extracted correctly.\n")
    
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()