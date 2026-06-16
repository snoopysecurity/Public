"""
Base class for signal modules.

Signal modules are sources of security-relevant information that help answer:
"Where should I start auditing this repo?"

Each module collects signals from a different source (commits, issues, NVD, etc.)
and returns normalized findings.
"""

"""
__Logic:__

- Defines the abstract base class `SignalModule` for all signal collection modules.
- Provides a registry system using the `@register_module` decorator.
- Implements shared functionality for NVD enrichment (`_enrich_cves`).
- Manages NVD API rate limiting and parallel fetching.
"""

from abc import ABC, abstractmethod
import time
import requests
import os
import concurrent.futures


# Module registry
_MODULE_REGISTRY = {}


def register_module(cls):
    """Decorator to register a signal module."""
    _MODULE_REGISTRY[cls.name] = cls
    return cls


def get_available_modules():
    """Get all registered modules."""
    return _MODULE_REGISTRY.copy()


def get_module(name):
    """Get a module class by name."""
    return _MODULE_REGISTRY.get(name)


class SignalModule(ABC):
    """
    Base class for all signal modules.
    
    A signal module collects security-relevant signals from a specific source.
    """
    
    name = None  # Unique identifier
    description = None  # Human-readable description
    
    # Class-level cache for NVD data to avoid redundant fetches across modules
    _nvd_cache = {}
    _blacklist = None
    _filepath_blacklist = None
    
    def __init__(self, **kwargs):
        """Initialize module with optional config."""
        self.config = kwargs
        
    def _load_blacklist(self):
        """Load blacklist terms."""
        if SignalModule._blacklist is not None:
            return
            
        SignalModule._blacklist = set()
        try:
            # Locate blacklist file relative to this file
            script_dir = os.path.dirname(os.path.realpath(__file__))
            blacklist_path = os.path.join(script_dir, "..", "patterns", "blacklist.txt")
            
            if os.path.exists(blacklist_path):
                with open(blacklist_path, "r") as f:
                    for line in f:
                        term = line.strip()
                        if term and not term.startswith("#"):
                            SignalModule._blacklist.add(term.lower())
        except Exception as e:
            print(f"Warning: Failed to load blacklist: {e}")

    def _check_blacklist(self, text):
        """Check if text contains any blacklisted terms. Returns the matching term or None."""
        if SignalModule._blacklist is None:
            self._load_blacklist()
            
        if not SignalModule._blacklist:
            return None
            
        text_lower = text.lower()
        for term in SignalModule._blacklist:
            if term in text_lower:
                return term
        return None

    def _load_filepath_blacklist(self):
        """Load filepath blacklist terms."""
        if SignalModule._filepath_blacklist is not None:
            return
            
        SignalModule._filepath_blacklist = set()
        try:
            # Locate blacklist file relative to this file
            script_dir = os.path.dirname(os.path.realpath(__file__))
            blacklist_path = os.path.join(script_dir, "..", "patterns", "filepath_blacklist.txt")
            
            if os.path.exists(blacklist_path):
                with open(blacklist_path, "r") as f:
                    for line in f:
                        term = line.strip()
                        if term and not term.startswith("#"):
                            SignalModule._filepath_blacklist.add(term.lower())
        except Exception as e:
            print(f"Warning: Failed to load filepath blacklist: {e}")

    def _check_filepath_blacklist(self, metadata):
        """Check if finding files match any filepath blacklisted terms."""
        if SignalModule._filepath_blacklist is None:
            self._load_filepath_blacklist()
            
        if not SignalModule._filepath_blacklist:
            return None
            
        files = metadata.get("files", [])
        if not isinstance(files, list): files = [str(files)]
        if metadata.get("file"): files.append(str(metadata.get("file")))
        
        # Deduplicate
        files = list(set(files))
        
        for f in files:
            f_lower = str(f).lower()
            for term in SignalModule._filepath_blacklist:
                if term in f_lower:
                    return term
        return None
    
    @abstractmethod
    def collect(self, repo_url, repo_name, repo_path=None, **kwargs):
        """
        Collect signals from this source.
        
        Args:
            repo_url: Full URL to the repository
            repo_name: Parsed owner/repo name
            repo_path: Local path to the cloned repository (optional)
            **kwargs: Additional config (github_token, throttle, etc.)
        
        Returns:
            List of findings (dicts with signal_type, title, description, etc.)
        """
        pass
    
    def enrich(self, findings, **kwargs):
        """
        Enrich findings with additional data from this source.
        
        Args:
            findings: List of finding dicts/objects to enrich in-place
            **kwargs: Config options
            
        Returns:
            Enriched list of findings
        """
        return findings
    
    def get_scores(self):
        """
        Return the confidence, impact, and research value scores for this module.
        Can be overridden by subclasses for dynamic scoring.
        
        Returns:
            dict: {
                "confidence_score": int (1-10),
                "impact_score": int (1-10),
                "research_value": int (1-10)
            }
        """
        return {
            "confidence_score": 5,
            "impact_score": 5,
            "research_value": 5
        }

    def _make_finding(self, signal_type, title, description, metadata=None, **kwargs):
        """
        Helper to create a normalized finding dict using static module severity.
        
        Args:
            signal_type: Type of signal
            title: Title of finding
            description: Description
            metadata: Additional data
            **kwargs: Score overrides (confidence_score, impact_score, research_value)
        """
        # Get scores from method
        scores = self.get_scores()
        
        # Apply overrides from kwargs if present
        confidence_score = kwargs.get("confidence_score", scores.get("confidence_score", 5))
        impact_score = kwargs.get("impact_score", scores.get("impact_score", 5))
        research_value = kwargs.get("research_value", scores.get("research_value", 5))

        # Calculate scores from module attributes (1-10 -> 0.0-1.0)
        confidence_val = confidence_score / 10.0
        impact = impact_score / 10.0
        research_val = research_value / 10.0
        
        # Map confidence score to confidence string
        confidence = "medium"
        if confidence_score >= 8:
            confidence = "high"
        elif confidence_score <= 3:
            confidence = "low"
            
        # Initial severity (will be overwritten by Engine based on Priority)
        severity = "medium"
        
        # Check blacklist (Content)
        blacklisted_term = self._check_blacklist(f"{title} {description}")
        if blacklisted_term:
            if "[BLACKLIST MATCH]" not in title:
                title = f"[BLACKLIST MATCH] {title}"
            description += f"\n\n[BLACKLIST MATCH] Finding score lowered because it matched blacklist keyword: '{blacklisted_term}'"
            
            severity = "info"
            # Downgrade scores if blacklisted
            impact = 0.1
            research_val = 0.1
            confidence_val = min(confidence_val, 0.5)
            
            if metadata is None: metadata = {}
            
            # Apply confidence penalty
            adj = metadata.get("module_confidence_adjustment", 0.0)
            metadata["module_confidence_adjustment"] = adj - 0.5
            
            reason = metadata.get("module_confidence_reason", "")
            if reason: reason += ", "
            reason += f"Blacklisted term '{blacklisted_term}' (-0.5)"
            metadata["module_confidence_reason"] = reason

        # Check filepath blacklist (File Paths)
        filepath_term = self._check_filepath_blacklist(metadata or {})
        if filepath_term:
            if "[BLACKLIST MATCH]" not in title:
                title = f"[BLACKLIST MATCH] {title}"
            description += f"\n\n[BLACKLIST MATCH] Finding score lowered because it matched filepath blacklist: '{filepath_term}'"
            
            severity = "info"
            # Downgrade scores for context matches
            impact = 0.1
            research_val = 0.1
            # Confidence might still be high (it *is* a finding), but research_value is low.
            # But let's downgrade it a bit to be safe
            confidence_val = min(confidence_val, 0.6)
            
            if metadata is None: metadata = {}
            
            # Apply confidence penalty
            adj = metadata.get("module_confidence_adjustment", 0.0)
            metadata["module_confidence_adjustment"] = adj - 0.3
            
            reason = metadata.get("module_confidence_reason", "")
            if reason: reason += ", "
            reason += f"Filepath blacklist '{filepath_term}' (-0.3)"
            metadata["module_confidence_reason"] = reason

        return {
            "signal_type": signal_type,
            "title": title,
            "description": description,
            "source_module": self.name,
            "severity": severity,
            "confidence": confidence,
            "metadata": metadata or {},
            
            # Explicit Module Scoring (Research Value, Confidence, Impact)
            "research_value": research_val,
            "confidence_score": confidence_val,
            "severity_score": impact,
            
            # Legacy/Aggregated Fields
            "priority_score": 0,
            "impact_score": impact, # Alias for severity_score
            
            "confidence_reason": None,
            "impact_reason": None,
            "priority_reason": None
        }

    def _enrich_cves(self, findings):
        """Fetch NVD data for CVE findings in parallel (if possible)."""
        cve_ids = set()
        findings_map = {}
        
        for finding in findings:
            if finding.get("signal_type") == "cve":
                cve_id = finding.get("metadata", {}).get("cve_id")
                if cve_id:
                    cve_ids.add(cve_id)
                    if cve_id not in findings_map:
                        findings_map[cve_id] = []
                    findings_map[cve_id].append(finding)
        
        if not cve_ids:
            return

        # Check for cached results
        to_fetch = []
        for cve_id in cve_ids:
            if cve_id in SignalModule._nvd_cache:
                self._apply_enrichment(findings_map[cve_id], SignalModule._nvd_cache[cve_id])
            else:
                to_fetch.append(cve_id)
        
        if not to_fetch:
            return

        # Determine strategy based on API key presence
        # NVD_API_KEY env var
        api_key = os.environ.get("NVD_API_KEY")
        max_workers = 4 if api_key else 1
        # Delay logic:
        # If no key: 6s delay enforced by sleep (sequential)
        # If key: 0.6s delay enforced (parallel but spread out)
        delay = 0.6 if api_key else 6.0
        
        if len(to_fetch) > 0:
            print(f"      Fetching NVD data for {len(to_fetch)} CVEs (workers={max_workers})...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cve = {
                executor.submit(self._fetch_nvd, cve_id, api_key, delay): cve_id 
                for cve_id in to_fetch
            }
            
            for future in concurrent.futures.as_completed(future_to_cve):
                cve_id = future_to_cve[future]
                try:
                    data = future.result()
                    if data:
                        enrichment = self._parse_nvd_response(data, cve_id)
                        SignalModule._nvd_cache[cve_id] = enrichment
                        self._apply_enrichment(findings_map[cve_id], enrichment)
                    else:
                        # Cache None to avoid refetching failed IDs?
                        # Maybe better not to cache failures in case of transient network issues
                        pass
                except Exception as e:
                    print(f"      [!] Error fetching {cve_id}: {e}")

    def _fetch_nvd(self, cve_id, api_key, delay):
        """Helper to fetch a single CVE."""
        headers = {}
        if api_key:
            headers["apiKey"] = api_key
            
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
        
        if delay > 0:
            time.sleep(delay)
            
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print(f"      [!] NVD Rate Limit Hit (403) for {cve_id}")
            elif response.status_code == 503:
                time.sleep(5) # Backoff
        except:
            pass
        return None

    def _apply_enrichment(self, findings_list, enrichment):
        """Apply NVD data to a list of findings."""
        if not enrichment: return
        for finding in findings_list:
            finding["nvd_enrichment"] = enrichment
            # Also add to metadata as requested
            if "metadata" not in finding:
                finding["metadata"] = {}
            finding["metadata"]["nvd"] = enrichment

    def _parse_nvd_response(self, data, cve_id):
        """Extract useful info from NVD response."""
        try:
            vulns = data.get("vulnerabilities", [])
            if not vulns: return None
            cve = vulns[0].get("cve", {})
            metrics = cve.get("metrics", {})
            
            score = None
            severity = None
            if "cvssMetricV31" in metrics:
                score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
                severity = metrics["cvssMetricV31"][0]["cvssData"]["baseSeverity"]
            elif "cvssMetricV2" in metrics:
                score = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]
                severity = metrics["cvssMetricV2"][0]["baseSeverity"]
                
            desc = cve.get("descriptions", [{}])[0].get("value", "No description")
            
            return {
                "cvss_score": score,
                "severity": severity,
                "description": desc[:200] + "..."
            }
        except: return None
