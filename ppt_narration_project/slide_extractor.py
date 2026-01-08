from pptx import Presentation

UNWANTED_PHRASES = [
    "Auto-generated",
    "Illustration related",
]

def is_unwanted(text):
    return any(phrase.lower() in text.lower() for phrase in UNWANTED_PHRASES)

def extract_slides(ppt_path):
    prs = Presentation(ppt_path)
    slides_data = []

    for idx, slide in enumerate(prs.slides):
        text_blocks = []

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue

            for paragraph in shape.text_frame.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue
                if is_unwanted(text):
                    continue

                # Remove bullet symbols
                text = text.lstrip("•").strip()
                text_blocks.append(text)

        # First meaningful line = title
        slide_title = text_blocks[0] if text_blocks else f"Slide {idx+1}"
        slide_body = text_blocks[1:] if len(text_blocks) > 1 else []

        slides_data.append({
            "slide_index": idx,
            "slide_title": slide_title,
            "original_slide_text": "\n".join(slide_body)
        })

    return slides_data
