import hashlib
import json
import os

def calculate_finding_id(finding):
    """Calculates a stable ID for a finding based on its content."""
    # Create a copy to avoid modifying original
    data = finding.copy()
    
    # Remove mutable fields that shouldn't affect identity
    for key in ["timestamp", "id", "triage_status"]:
        if key in data:
            del data[key]

    # Sort keys to ensure stability
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def parse_repo_name(url):
    """Extract owner/repo from a GitHub URL."""
    if not url: return None
    url = url.rstrip('/')
    if 'github.com' in url:
        parts = url.split('github.com/')
        if len(parts) > 1:
            return '/'.join(parts[1].split('/')[:2])
    
    # Fallback for simple paths
    parts = url.split('/')
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return url

def get_patterns_dir():
    """Returns the absolute path to the patterns directory."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # core/utils.py -> core/ -> root -> patterns
    return os.path.join(script_dir, "..", "patterns")

def get_security_keywords(patterns):
    """Extract unique security keywords from patterns."""
    keywords = set()
    for lang, severities in patterns.items():
        for severity, categories in severities.items():
            for category, items in categories.items():
                # items is a list of dicts with 'original' key
                for pat in items:
                    original = pat["original"] if isinstance(pat, dict) else pat
                    
                    # Clean regex patterns for GitHub search
                    if original.startswith("/") and original.endswith("/"):
                        # Strip slashes
                        clean = original[1:-1]
                        # Remove word boundaries
                        clean = clean.replace(r"\b", "")
                        # Replace common separators
                        clean = clean.replace(r"[-_\s]+", " ")
                        clean = clean.replace(r"[-_\s]*", " ")
                        # Basic cleanup
                        clean = clean.strip()
                        if clean:
                            keywords.add(clean)
                    else:
                        keywords.add(original)

    # Prioritize high-value keywords
    priority = ["vulnerability", "security", "CVE", "exploit", "injection", 
                "XSS", "CSRF", "RCE", "authentication", "authorization"]
    
    # Helper to check case-insensitive presence
    def is_in_priority(kw):
        return any(p.lower() == kw.lower() for p in priority)
        
    final_list = []
    # Add priority words if they appear in keywords (case-insensitive check)
    for p in priority:
        if any(k.lower() == p.lower() for k in keywords):
            final_list.append(p)
            
    # Add remaining keywords
    for k in keywords:
        if not is_in_priority(k):
            final_list.append(k)
            
    return final_list

def get_keyword_precision_map(patterns):
    """
    Extract mapping of security keywords to their precision bucket.
    Returns: dict {keyword: "high_precision"|"low_precision"}
    """
    keyword_map = {}
    for lang, severities in patterns.items():
        for severity, categories in severities.items():
            for category, items in categories.items():
                # items is a list of dicts with 'original' key
                for pat in items:
                    original = pat["original"] if isinstance(pat, dict) else pat
                    
                    # Clean regex patterns for GitHub search (same logic as get_security_keywords)
                    clean = None
                    if original.startswith("/") and original.endswith("/"):
                        # Strip slashes
                        c = original[1:-1]
                        # Remove word boundaries
                        c = c.replace(r"\b", "")
                        # Replace common separators
                        c = c.replace(r"[-_\s]+", " ")
                        c = c.replace(r"[-_\s]*", " ")
                        # Basic cleanup
                        c = c.strip()
                        if c:
                            clean = c
                    else:
                        clean = original
                    
                    if clean:
                        # Store precision. If already exists, prefer high_precision
                        if clean not in keyword_map or severity == "high_precision":
                            keyword_map[clean] = severity
    
    return keyword_map
