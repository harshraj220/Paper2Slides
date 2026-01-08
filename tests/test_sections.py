from paper2ppt_core.sections import split_into_sections

def test_split_simple():
    pages = [
        "Title of Paper\n\nAbstract\nThis is the abstract text.\n\nIntroduction\nIntro text here.\n\nMethod\nMethod details here."
    ]
    secs = split_into_sections(pages)
    assert isinstance(secs, list) and len(secs) >= 1

    # check for abstract presence (in title/raw_title or text)
    found_abstract = False
    for s in secs:
        t = s.get('title','').lower()
        rt = s.get('raw_title','').lower() if s.get('raw_title') else ''
        txt = s.get('text','').lower()
        if 'abstract' in t or 'abstract' in rt or 'abstract' in txt:
            found_abstract = True
            break
    assert found_abstract
