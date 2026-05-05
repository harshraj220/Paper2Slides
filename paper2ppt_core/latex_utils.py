import re

# Common LaTeX Math Symbols to Unicode
LATEX_SYMBOLS = {
    # Greek
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\epsilon": "ε",
    r"\zeta": "ζ", r"\eta": "η", r"\theta": "θ", r"\iota": "ι", r"\kappa": "κ",
    r"\lambda": "λ", r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ", r"\omicron": "ο",
    r"\pi": "π", r"\rho": "ρ", r"\sigma": "σ", r"\tau": "τ", r"\upsilon": "υ",
    r"\phi": "φ", r"\chi": "χ", r"\psi": "ψ", r"\omega": "ω",
    r"\Gamma": "Γ", r"\Delta": "Δ", r"\Theta": "Θ", r"\Lambda": "Λ",
    r"\Xi": "Ξ", r"\Pi": "Π", r"\Sigma": "Σ", r"\Upsilon": "Υ",
    r"\Phi": "Φ", r"\Psi": "Ψ", r"\Omega": "Ω",
    
    # Operators & Relations
    r"\times": "×", r"\div": "÷", r"\cdot": "⋅", r"\pm": "±", r"\mp": "∓",
    r"\leq": "≤", r"\geq": "≥", r"\neq": "≠", r"\approx": "≈", r"\equiv": "≡",
    r"\infty": "∞", r"\partial": "∂", r"\nabla": "∇", r"\sum": "∑", r"\prod": "∏",
    r"\int": "∫", r"\in": "∈", r"\notin": "∉", r"\subset": "⊂", r"\supset": "⊃",
    r"\cup": "∪", r"\cap": "∩", r"\forall": "∀", r"\exists": "∃", r"\neg": "¬",
    r"\rightarrow": "→", r"\leftarrow": "←", r"\Rightarrow": "⇒", r"\Leftarrow": "⇐",
    r"\leftrightarrow": "↔", r"\longrightarrow": "⟶", 
    
    # Logic
    r"\land": "∧", r"\lor": "∨", 
    
    # Misc
    r"\ell": "ℓ", r"\Re": "ℜ", r"\Im": "ℑ", r"\hbar": "ℏ",
    r"\emptyset": "∅",
}

def clean_latex_expression(latex_str):
    """
    Basic cleanup of a raw latex string before parsing.
    Removes delimiters like \( \) and \$ \$.
    """
    s = latex_str.strip()
    # Remove outer delimiters carefully
    if s.startswith(r"\(") and s.endswith(r"\)"):
        return s[2:-2].strip()
    if s.startswith(r"\[") and s.endswith(r"\]"):
        return s[2:-2].strip()
    if s.startswith("$") and s.endswith("$"):
        return s[1:-1].strip()
    return s

def split_text_and_math(text):
    """
    Splits text into a list of (type, content) tuples.
    Type is 'text' or 'math'.
    Handles \\(...\\) and $...$ delimiters.
    """
    tokens = []
    # Regex for \\( ... \\) OR $ ... $ (non-greedy)
    # Fixed regex to capture closing backslash
    pattern = re.compile(r'(\\\(.*?\\\))|(\$[^$]+\$)')
    
    last_idx = 0
    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            tokens.append(('text', text[last_idx:start]))
        
        math_content = match.group(0)
        clean_content = clean_latex_expression(math_content)
        tokens.append(('math', clean_content))
        last_idx = end
        
    if last_idx < len(text):
        tokens.append(('text', text[last_idx:]))
        
    return tokens

def parse_mixed_content(text):
    """
    Main entry point. Parses a string containing mix of text and latex.
    Returns a unified list of (text_segment, style_dict).
    """
    raw_tokens = split_text_and_math(text)
    final_segments = []
    
    for kind, content in raw_tokens:
        if kind == 'text':
            # Plain text has no special style
            final_segments.append((content, {}))
        else:
            # Parse math content
            math_segments = parse_latex_recursive(content, {"italic": False}) # default upright unless var
            final_segments.extend(math_segments)
            
    return final_segments

def parse_latex_recursive(latex_str, current_style=None):
    """
    Recursively parses latex string into segments with style.
    Returns: List of (text, style_dict)
    """
    if current_style is None:
        current_style = {}
        
    # 1. Replace symbols (Global replacement for simplicity)
    # Note: replacing in 'latex_str' destroys commands, so we must be careful.
    # We should only replace symbols that are standalone or we know won't break logic.
    # But for now, let's assume our symbols (Greek, operators) are safe to replace globally
    # IF they are not part of other commands.
    
    # Sorted keys by length to avoid prefix issues (\sigma vs \s) - though \sigma is unique enough
    # We do this step lazily on text segments, NOT on the whole string, to avoid breaking \text{}
    
    segments = []
    i = 0
    n = len(latex_str)
    
    current_text = ""
    
    def flush_current():
        nonlocal current_text
        if current_text:
            # Apply symbol replacement on the plain text leaf
            txt = current_text
            for pat, rep in LATEX_SYMBOLS.items():
                # Naive replace is risky for substrings, but these are all backslash commands
                # So we can just replace literal string regular matches
                # But we must be careful of \\alpha vs \\alphabet (unlikely in math)
                if pat in txt:
                     txt = txt.replace(pat.replace("\\\\", "\\"), rep)
            
            # Heuristic: If it's single letters, italicize them (Math semantic)
            # Unless we are inside \text or already have style
            final_style = current_style.copy()
            if not final_style.get("no_italic") and re.match(r"^[a-zA-Z]$", txt):
                final_style["italic"] = True
                
            segments.append((txt, final_style))
        current_text = ""

    while i < n:
        char = latex_str[i]
        
        # --- COMMANDS ---
        if char == '\\':
            # Check for specific structural commands
            rest = latex_str[i:]
            
            # \text{...}
            if rest.startswith(r"\text{"):
                flush_current()
                j = i + 6
                brace_count = 1
                start_content = j
                while j < n and brace_count > 0:
                    if latex_str[j] == '{': brace_count += 1
                    elif latex_str[j] == '}': brace_count -= 1
                    j += 1
                
                content = latex_str[start_content:j-1]
                # Recurse? \text implies normal text mode, so reset math styles (like italic)
                # But preserve sub/sup? Typically \text inside math is upright.
                # We treat it as a leaf text mostly, but it might contain symbols? 
                # Usually \text{ offload } is just text.
                segments.append((content, {"no_italic": True, "subscript": current_style.get("subscript"), "superscript": current_style.get("superscript")}))
                i = j
                continue
            
            # \frac{num}{den}
            elif rest.startswith(r"\frac{"):
                flush_current()
                j = i + 6
                # Numerator
                brace_count = 1
                start_num = j
                while j < n and brace_count > 0:
                     if latex_str[j] == '{': brace_count += 1
                     elif latex_str[j] == '}': brace_count -= 1
                     j += 1
                num_text = latex_str[start_num:j-1]
                
                # Denominator
                if j < n and latex_str[j] == '{':
                    j += 1
                    brace_count = 1
                    start_den = j
                    while j < n and brace_count > 0:
                        if latex_str[j] == '{': brace_count += 1
                        elif latex_str[j] == '}': brace_count -= 1
                        j += 1
                    den_text = latex_str[start_den:j-1]
                    
                    # Flatten fraction to (num)/(den)
                    # We recursively parse the parts
                    parsed_num = parse_latex_recursive(num_text, current_style)
                    parsed_den = parse_latex_recursive(den_text, current_style)
                    
                    segments.append(("(", current_style))
                    segments.extend(parsed_num)
                    segments.append((")/(", current_style))
                    segments.extend(parsed_den)
                    segments.append((")", current_style))
                    
                    i = j
                    continue

            # Fallback for other commands (\alpha, etc.) -> Add to buffer
            current_text += char
            i += 1
            
        # --- SUBSCRIPT ---
        elif char == '_':
            flush_current()
            i += 1
            # Check for brace
            if i < n and latex_str[i] == '{':
                j = i + 1
                brace_count = 1
                start_sub = j
                while j < n and brace_count > 0:
                    if latex_str[j] == '{': brace_count += 1
                    elif latex_str[j] == '}': brace_count -= 1
                    j += 1
                content = latex_str[start_sub:j-1]
                
                # Merge styles
                new_style = current_style.copy()
                new_style["subscript"] = True
                new_style["superscript"] = False # Reset if mixed
                
                segments.extend(parse_latex_recursive(content, new_style))
                i = j
            elif i < n:
                # Single char
                content = latex_str[i]
                new_style = current_style.copy()
                new_style["subscript"] = True
                segments.extend(parse_latex_recursive(content, new_style))
                i += 1
                
        # --- SUPERSCRIPT ---
        elif char == '^':
            flush_current()
            i += 1
            if i < n and latex_str[i] == '{':
                j = i + 1
                brace_count = 1
                start_sup = j
                while j < n and brace_count > 0:
                    if latex_str[j] == '{': brace_count += 1
                    elif latex_str[j] == '}': brace_count -= 1
                    j += 1
                content = latex_str[start_sup:j-1]
                
                new_style = current_style.copy()
                new_style["superscript"] = True
                new_style["subscript"] = False
                
                segments.extend(parse_latex_recursive(content, new_style))
                i = j
            elif i < n:
                content = latex_str[i]
                new_style = current_style.copy()
                new_style["superscript"] = True
                segments.extend(parse_latex_recursive(content, new_style))
                i += 1

        # --- NORMAL CHAR ---
        else:
            current_text += char
            i += 1
            
    flush_current()
    return segments
