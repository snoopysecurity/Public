import os
import re

def load_patterns(patterns_dir):
    """Loads patterns from the given directory and compiles regexes."""
    patterns = {}
    if not os.path.exists(patterns_dir):
        return patterns

    for lang in os.listdir(patterns_dir):
        lang_path = os.path.join(patterns_dir, lang)
        if os.path.isdir(lang_path):
            patterns[lang] = {}
            for precision in os.listdir(lang_path):
                precision_path = os.path.join(lang_path, precision)
                if os.path.isdir(precision_path):
                    patterns[lang][precision] = {}
                    for filename in os.listdir(precision_path):
                        if filename.endswith(".txt"):
                            category = os.path.splitext(filename)[0]
                            path = os.path.join(precision_path, filename)
                            
                            compiled_list = []
                            with open(path, "r") as f:
                                for line in f:
                                    line = line.strip()
                                    if not line: continue
                                    
                                    regex = None
                                    is_regex = False
                                    
                                    if line.startswith("/") and line.endswith("/"):
                                        try:
                                            # Compile complex regex
                                            regex = re.compile(line[1:-1], re.IGNORECASE)
                                            is_regex = True
                                        except re.error:
                                            pass
                                    else:
                                        # Compile literal as word boundary regex
                                        try:
                                            regex = re.compile(r"\b" + re.escape(line) + r"\b", re.IGNORECASE)
                                        except re.error:
                                            pass
                                    
                                    if regex:
                                        compiled_list.append({
                                            "regex": regex,
                                            "original": line,
                                            "is_regex": is_regex
                                        })
                                    
                            patterns[lang][precision][category] = compiled_list
    return patterns

def match_patterns(text, patterns, lang, file_path=None, include_categories=None, exclude_categories=None):
    """Matches patterns against the given text using pre-compiled regexes."""
    findings = []
    
    # Context Downgrade Logic
    is_test_context = False
    context_downgrade_reason = None
    if file_path:
        lower_path = file_path.lower()
        if any(x in lower_path for x in ["test/", "spec/", "mock", "doc"]):
            is_test_context = True
            context_downgrade_reason = "Found in test/doc context"

    if lang in patterns:
        for precision_bucket, categories in patterns[lang].items():
            # precision_bucket is 'high_precision' or 'low_precision'
            
            for category, pattern_list in categories.items():
                # Filter categories
                if include_categories and category not in include_categories:
                    continue
                if exclude_categories and category in exclude_categories:
                    continue

                for pat_obj in pattern_list:
                    matched_values = set()
                    try:
                        # Use finditer to capture all unique occurrences (e.g. multiple different CVEs)
                        for match_obj in pat_obj["regex"].finditer(text):
                            if pat_obj["is_regex"]:
                                val = match_obj.group(0)
                            else:
                                val = pat_obj["original"]
                            
                            if val:
                                matched_values.add(val)
                    except Exception:
                        pass
                    
                    for val in matched_values:
                        _add_finding(findings, val, category, precision_bucket, is_test_context, context_downgrade_reason)
                        
    return findings

def _add_finding(findings, match_val, category, precision_bucket, is_test_context, downgrade_reason):
    """Helper to add finding."""
    confidence = "high" if precision_bucket == "high_precision" else "low"
    if is_test_context:
        confidence = "low"
    
    severity = "high" if precision_bucket == "high_precision" else "medium"
    if category == "todo":
        severity = "low"
        
    metadata = {}
    if is_test_context and downgrade_reason:
        metadata["downgrade_reason"] = downgrade_reason

    findings.append({
        "type": "pattern",
        "severity": severity,
        "confidence": confidence,
        "category": category,
        "value": match_val,
        "precision_bucket": precision_bucket,
        "metadata": metadata
    })
