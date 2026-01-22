#!/usr/bin/env python3
"""
Quick test script to verify the pipeline works
Usage: python3 quick_test.py aiawn.pdf
"""

import sys
import os

def test_image_extraction(pdf_path):
    """Test if images can be extracted"""
    print("\n" + "="*70)
    print("TEST 1: Image Extraction")
    print("="*70)
    
    from paper2ppt_core.io import load_input_paper
    
    pages_text, pages_images = load_input_paper(pdf_path)
    
    total = sum(len(imgs) for imgs in pages_images.values())
    print(f"✓ Pages: {len(pages_text)}")
    print(f"✓ Images: {total}")
    
    for page, imgs in pages_images.items():
        if imgs:
            print(f"  Page {page+1}: {len(imgs)} images")
            for img in imgs:
                exists = "✓" if os.path.exists(img['path']) else "✗"
                print(f"    {exists} {os.path.basename(img['path'])}")
    
    return total > 0


def test_section_detection(pdf_path):
    """Test if sections are detected"""
    print("\n" + "="*70)
    print("TEST 2: Section Detection")
    print("="*70)
    
    from paper2ppt_core.io import load_input_paper
    from paper2ppt_core.sections import split_into_sections
    
    pages_text, _ = load_input_paper(pdf_path)
    sections = split_into_sections(pages_text)
    
    print(f"✓ Sections found: {len(sections)}")
    for i, sec in enumerate(sections, 1):
        title = sec.get("title", "Unknown")
        text_len = len(sec.get("text", ""))
        pages = sec.get("pages", set())
        print(f"  [{i}] {title} ({text_len} chars, pages: {sorted(pages)})")
    
    return len(sections) > 0


def test_slide_generation(pdf_path):
    """Test slide generation"""
    print("\n" + "="*70)
    print("TEST 3: Slide Generation")
    print("="*70)
    
    output = "test_output.pptx"
    
    from paper2ppt_cli import generate_slides
    
    result = generate_slides(pdf_path, output, max_bullets=4)
    
    if os.path.exists(output):
        size_mb = os.path.getsize(output) / (1024 * 1024)
        print(f"\n✓ Presentation created: {output} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"\n✗ Failed to create presentation")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 quick_test.py <paper.pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print("\n" + "="*70)
    print(f"TESTING PAPER2SLIDES PIPELINE")
    print(f"Input: {pdf_path}")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Image Extraction", test_image_extraction(pdf_path)))
    except Exception as e:
        print(f"\n✗ Image extraction failed: {e}")
        results.append(("Image Extraction", False))
    
    try:
        results.append(("Section Detection", test_section_detection(pdf_path)))
    except Exception as e:
        print(f"\n✗ Section detection failed: {e}")
        results.append(("Section Detection", False))
    
    try:
        results.append(("Slide Generation", test_slide_generation(pdf_path)))
    except Exception as e:
        print(f"\n✗ Slide generation failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Slide Generation", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("="*70))
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())