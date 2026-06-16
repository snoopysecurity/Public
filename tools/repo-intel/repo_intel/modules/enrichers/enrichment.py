"""
Base class for enrichment modules.

To create a new module:
1. Create a new file in this directory (e.g., my_module.py)
2. Import and subclass EnrichmentModule
3. Implement the required methods

Example:
    from repo_intel.modules.enrichment import EnrichmentModule

    class MyModule(EnrichmentModule):
        name = "my_module"
        description = "Description of what this module does"
        
        def can_enrich(self, findings):
            # Return True if this module can enrich the findings
            return any(f["type"] == "pattern" for f in findings)
        
        def enrich(self, findings, **kwargs):
            # Enrich and return findings
            return findings
"""

"""
__Logic:__

- Defines the base class `EnrichmentModule` for modules that add context to existing findings.
- Provides a registry system for enrichment modules.
- specific modules subclass this to implement `enrich(findings)` logic.
"""

# Registry of all available modules
_MODULE_REGISTRY = {}


def register_module(cls):
    """Decorator to register a module in the registry."""
    _MODULE_REGISTRY[cls.name] = cls
    return cls


def get_available_modules():
    """Returns a dict of all registered modules."""
    return _MODULE_REGISTRY.copy()


def get_module(name):
    """Get a module class by name."""
    return _MODULE_REGISTRY.get(name)


class EnrichmentModule:
    """Base class for enrichment modules.
    
    Subclasses must define:
        - name: str - unique identifier for the module
        - description: str - human-readable description
        - can_enrich(findings) - returns True if module can process findings
        - enrich(findings, **kwargs) - enriches and returns findings
    """
    
    name = None
    description = None
    
    def __init__(self, **kwargs):
        """Initialize the module with optional config."""
        self.config = kwargs
        
    def can_enrich(self, findings):
        """Check if this module can enrich the given findings."""
        return True
        
    def enrich(self, findings, **kwargs):
        """Enriches the findings with external intelligence."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement enrich()")
