<script>
    import { onMount, createEventDispatcher } from 'svelte';
    
    export let findings = [];
    export let onSearch = null; // Callback for search/filter changes
    
    const dispatch = createEventDispatcher();
    
    // Search state
    let searchTerm = '';
    let savedSearches = [];
    let savedFilters = {};
    let showSaveDialog = false;
    let newSearchName = '';
    let newSearchDescription = '';
    let activeFilter = null;
    
    // Filter state
    let filters = {
        severity: [],
        module: [],
        status: [], // TP, FP, UNTRIAGED
        confidence_min: 0,
        confidence_max: 1,
        research_value_min: 0,
        research_value_max: 1
    };
    
    // Available options for filters
    let availableModules = [];
    let availableSeverities = ['critical', 'high', 'medium', 'low', 'info'];
    let availableStatuses = ['TP', 'FP', 'UNTRIAGED'];
    
    $: filteredFindings = applyFilters(findings);
    $: hasActiveFilters = hasActiveFiltersFunc();
    $: hasActiveSearch = searchTerm.trim() !== '';
    
    onMount(async () => {
        await loadSavedSearches();
        updateAvailableOptions();
    });
    
    async function loadSavedSearches() {
        try {
            const response = await fetch('/api/searches');
            if (response.ok) {
                const data = await response.json();
                savedSearches = data.searches || [];
                savedFilters = data.filters || {};
            }
        } catch (e) {
            console.error('Failed to load saved searches:', e);
        }
    }
    
    function updateAvailableOptions() {
        const modules = new Set();
        findings.forEach(f => {
            if (f.source_module) modules.add(f.source_module);
        });
        availableModules = Array.from(modules).sort();
    }
    
    function applyFilters(items) {
        let filtered = items;
        
        // Apply text search
        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(f => {
                if (f.title?.toLowerCase().includes(term)) return true;
                if (f.description?.toLowerCase().includes(term)) return true;
                if (f.source_module?.toLowerCase().includes(term)) return true;
                if (f.metadata?.file?.toLowerCase().includes(term)) return true;
                
                // Search in metadata
                try {
                    const metaStr = JSON.stringify(f.metadata).toLowerCase();
                    if (metaStr.includes(term)) return true;
                } catch (e) {}
                
                return false;
            });
        }
        
        // Apply severity filter
        if (filters.severity.length > 0) {
            filtered = filtered.filter(f => filters.severity.includes(f.severity));
        }
        
        // Apply module filter
        if (filters.module.length > 0) {
            filtered = filtered.filter(f => filters.module.includes(f.source_module));
        }
        
        // Apply status filter
        if (filters.status.length > 0) {
            filtered = filtered.filter(f => {
                const status = f.triage_status || 'UNTRIAGED';
                return filters.status.includes(status);
            });
        }
        
        // Apply confidence range
        filtered = filtered.filter(f => {
            const conf = f.confidence_score || 0;
            return conf >= filters.confidence_min && conf <= filters.confidence_max;
        });
        
        // Apply research value range
        filtered = filtered.filter(f => {
            const rv = f.research_value || 0;
            return rv >= filters.research_value_min && rv <= filters.research_value_max;
        });
        
        return filtered;
    }
    
    function hasActiveFiltersFunc() {
        return filters.severity.length > 0 || 
               filters.module.length > 0 || 
               filters.status.length > 0 ||
               filters.confidence_min > 0 ||
               filters.confidence_max < 1 ||
               filters.research_value_min > 0 ||
               filters.research_value_max < 1;
    }
    
    function handleSearchInput(event) {
        searchTerm = event.target.value;
        notifyChange();
    }
    
    function handleFilterChange(filterType, value) {
        if (filterType === 'severity' || filterType === 'module' || filterType === 'status') {
            const index = filters[filterType].indexOf(value);
            if (index === -1) {
                filters[filterType] = [...filters[filterType], value];
            } else {
                filters[filterType] = filters[filterType].filter(v => v !== value);
            }
        } else {
            filters[filterType] = value;
        }
        notifyChange();
    }
    
    function notifyChange() {
        const searchData = {
            term: searchTerm,
            filters: { ...filters },
            results: filteredFindings,
            totalCount: findings.length,
            filteredCount: filteredFindings.length
        };
        
        if (onSearch) {
            onSearch(searchData);
        }
        
        dispatch('search', searchData);
    }
    
    async function saveSearch(type = 'search') {
        if (!newSearchName.trim()) {
            alert('Please enter a name for this search.');
            return;
        }
        
        try {
            const data = {
                type: type,
                name: newSearchName.trim(),
                description: newSearchDescription.trim(),
                created_at: new Date().toISOString()
            };
            
            if (type === 'search') {
                data.query = searchTerm;
            } else {
                data.filter = { ...filters };
            }
            
            const response = await fetch('/api/searches', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                await loadSavedSearches();
                showSaveDialog = false;
                newSearchName = '';
                newSearchDescription = '';
            } else {
                alert('Failed to save search');
            }
        } catch (e) {
            console.error('Failed to save search:', e);
            alert('Failed to save search');
        }
    }
    
    async function loadSavedSearch(search) {
        searchTerm = search.query;
        notifyChange();
    }
    
    async function loadSavedFilter(filterName) {
        const filterData = savedFilters[filterName];
        if (filterData) {
            filters = { ...filterData };
            notifyChange();
        }
    }
    
    async function deleteSavedSearch(searchName, type = 'search') {
        if (!confirm(`Delete "${searchName}"?`)) return;
        
        try {
            const response = await fetch(`/api/searches/${searchName}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                await loadSavedSearches();
            } else {
                alert('Failed to delete search');
            }
        } catch (e) {
            console.error('Failed to delete search:', e);
            alert('Failed to delete search');
        }
    }
    
    function clearAllFilters() {
        filters = {
            severity: [],
            module: [],
            status: [],
            confidence_min: 0,
            confidence_max: 1,
            research_value_min: 0,
            research_value_max: 1
        };
        searchTerm = '';
        notifyChange();
    }
    
    function openSaveDialog(type = 'search') {
        showSaveDialog = true;
        activeFilter = type;
    }
</script>

<div class="search-filters-container">
    <!-- Search Bar -->
    <div class="search-section">
        <div class="search-bar">
            <input 
                type="text" 
                placeholder="Search findings... (title, description, module, file)"
                value={searchTerm}
                on:input={handleSearchInput}
                class:active={hasActiveSearch}
            />
            <div class="search-actions">
                {#if hasActiveSearch || hasActiveFilters}
                    <button class="clear-btn" on:click={clearAllFilters}>
                        Clear All
                    </button>
                {/if}
                <button class="save-btn" on:click={() => openSaveDialog('search')}>
                    💾 Save Search
                </button>
            </div>
        </div>
        
        <!-- Search Results Summary -->
        <div class="search-summary">
            {#if hasActiveSearch || hasActiveFilters}
                <span class="results-count">
                    {filteredFindings.length} of {findings.length} results
                </span>
            {/if}
        </div>
    </div>
    
    <!-- Filters Section -->
    <div class="filters-section" class:expanded={hasActiveFilters}>
        <div class="filters-header">
            <h3>Filters</h3>
            <button class="save-btn" on:click={() => openSaveDialog('filter')}>
                💾 Save Filter Set
            </button>
        </div>
        
        <div class="filters-grid">
            <!-- Severity Filter -->
            <div class="filter-group">
                <label>Severity</label>
                <div class="filter-options">
                    {#each availableSeverities as severity}
                        <label class="filter-option">
                            <input 
                                type="checkbox" 
                                checked={filters.severity.includes(severity)}
                                on:change={() => handleFilterChange('severity', severity)}
                            />
                            <span class="severity-indicator {severity}"></span>
                            {severity}
                        </label>
                    {/each}
                </div>
            </div>
            
            <!-- Module Filter -->
            <div class="filter-group">
                <label>Module</label>
                <div class="filter-options scrollable">
                    {#each availableModules as module}
                        <label class="filter-option">
                            <input 
                                type="checkbox" 
                                checked={filters.module.includes(module)}
                                on:change={() => handleFilterChange('module', module)}
                            />
                            {module}
                        </label>
                    {/each}
                </div>
            </div>
            
            <!-- Status Filter -->
            <div class="filter-group">
                <label>Triage Status</label>
                <div class="filter-options">
                    {#each availableStatuses as status}
                        <label class="filter-option">
                            <input 
                                type="checkbox" 
                                checked={filters.status.includes(status)}
                                on:change={() => handleFilterChange('status', status)}
                            />
                            <span class="status-indicator {status.toLowerCase()}"></span>
                            {status}
                        </label>
                    {/each}
                </div>
            </div>
            
            <!-- Score Ranges -->
            <div class="filter-group">
                <label>Confidence Range</label>
                <div class="range-container">
                    <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step="0.1"
                        bind:value={filters.confidence_min}
                        on:change={notifyChange}
                    />
                    <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step="0.1"
                        bind:value={filters.confidence_max}
                        on:change={notifyChange}
                    />
                    <div class="range-labels">
                        <span>{filters.confidence_min.toFixed(1)}</span>
                        <span>{filters.confidence_max.toFixed(1)}</span>
                    </div>
                </div>
            </div>
            
            <div class="filter-group">
                <label>Research Value Range</label>
                <div class="range-container">
                    <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step="0.1"
                        bind:value={filters.research_value_min}
                        on:change={notifyChange}
                    />
                    <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step="0.1"
                        bind:value={filters.research_value_max}
                        on:change={notifyChange}
                    />
                    <div class="range-labels">
                        <span>{filters.research_value_min.toFixed(1)}</span>
                        <span>{filters.research_value_max.toFixed(1)}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Saved Searches & Filters -->
    {#if savedSearches.length > 0 || Object.keys(savedFilters).length > 0}
        <div class="saved-section">
            <h3>Saved Searches & Filters</h3>
            
            {#if savedSearches.length > 0}
                <div class="saved-items">
                    <h4>Searches</h4>
                    {#each savedSearches as search}
                        <div class="saved-item">
                            <div class="saved-item-info">
                                <strong>{search.name}</strong>
                                {#if search.description}
                                    <span class="saved-item-desc">{search.description}</span>
                                {/if}
                                <code class="saved-item-query">"{search.query}"</code>
                            </div>
                            <div class="saved-item-actions">
                                <button class="load-btn" on:click={() => loadSavedSearch(search)}>
                                    Load
                                </button>
                                <button class="delete-btn" on:click={() => deleteSavedSearch(search.name, 'search')}>
                                    Delete
                                </button>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
            
            {#if Object.keys(savedFilters).length > 0}
                <div class="saved-items">
                    <h4>Filter Sets</h4>
                    {#each Object.entries(savedFilters) as [name, filter]}
                        <div class="saved-item">
                            <div class="saved-item-info">
                                <strong>{name}</strong>
                                <span class="saved-item-desc">
                                    {Object.keys(filter).length} active filters
                                </span>
                            </div>
                            <div class="saved-item-actions">
                                <button class="load-btn" on:click={() => loadSavedFilter(name)}>
                                    Load
                                </button>
                                <button class="delete-btn" on:click={() => deleteSavedSearch(name, 'filter')}>
                                    Delete
                                </button>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    {/if}
    
    <!-- Save Dialog -->
    {#if showSaveDialog}
        <div class="dialog-overlay" on:click={() => showSaveDialog = false}>
            <div class="dialog" on:click|stopPropagation>
                <div class="dialog-header">
                    <h3>Save {activeFilter === 'search' ? 'Search' : 'Filter Set'}</h3>
                    <button class="close-btn" on:click={() => showSaveDialog = false}>×</button>
                </div>
                <div class="dialog-content">
                    <div class="form-group">
                        <label>Name *</label>
                        <input 
                            type="text" 
                            bind:value={newSearchName} 
                            placeholder="Enter a name..."
                            class:invalid={!newSearchName.trim()}
                        />
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea 
                            bind:value={newSearchDescription} 
                            placeholder="Optional description..."
                            rows="3"
                        ></textarea>
                    </div>
                </div>
                <div class="dialog-actions">
                    <button class="cancel-btn" on:click={() => showSaveDialog = false}>
                        Cancel
                    </button>
                    <button 
                        class="save-confirm-btn" 
                        on:click={() => saveSearch(activeFilter)}
                        disabled={!newSearchName.trim()}
                    >
                        Save
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .search-filters-container {
        background: #252526;
        border-radius: 8px;
        border: 1px solid #333;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .search-section {
        margin-bottom: 1rem;
    }
    
    .search-bar {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .search-bar input {
        flex: 1;
        background: #1e1e1e;
        border: 1px solid #444;
        color: #ccc;
        padding: 0.75rem;
        border-radius: 6px;
        font-size: 0.9rem;
        transition: border-color 0.2s;
    }
    
    .search-bar input:focus {
        outline: none;
        border-color: #007acc;
    }
    
    .search-bar input.active {
        border-color: #007acc;
        background: #1a1a1a;
    }
    
    .search-actions {
        display: flex;
        gap: 0.5rem;
    }
    
    .clear-btn, .save-btn {
        background: #333;
        color: #ccc;
        border: 1px solid #555;
        padding: 0.5rem 0.75rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.8rem;
        transition: all 0.2s;
        white-space: nowrap;
    }
    
    .clear-btn:hover, .save-btn:hover {
        background: #444;
        color: #fff;
    }
    
    .search-summary {
        margin-top: 0.5rem;
        font-size: 0.8rem;
        color: #888;
    }
    
    .results-count {
        background: #1e1e1e;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-family: monospace;
    }
    
    .filters-section {
        border-top: 1px solid #333;
        padding-top: 1rem;
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
    }
    
    .filters-section.expanded {
        max-height: 1000px;
    }
    
    .filters-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .filters-header h3 {
        margin: 0;
        color: #ccc;
        font-size: 1rem;
    }
    
    .filters-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
    }
    
    .filter-group {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #333;
    }
    
    .filter-group label {
        display: block;
        color: #888;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .filter-options {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        max-height: 150px;
        overflow-y: auto;
    }
    
    .filter-options.scrollable {
        max-height: 120px;
    }
    
    .filter-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 4px;
        transition: background 0.2s;
        font-size: 0.85rem;
        color: #ccc;
    }
    
    .filter-option:hover {
        background: #2a2d2e;
    }
    
    .filter-option input[type="checkbox"] {
        margin: 0;
    }
    
    .severity-indicator, .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.25rem;
    }
    
    .severity-indicator.critical { background: #f14c4c; }
    .severity-indicator.high { background: #cca700; }
    .severity-indicator.medium { background: #007acc; }
    .severity-indicator.low, .severity-indicator.info { background: #666; }
    
    .status-indicator.tp { background: #4caf50; }
    .status-indicator.fp { background: #f44336; }
    .status-indicator.untriaged { background: #666; }
    
    .range-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .range-container input[type="range"] {
        width: 100%;
        margin: 0;
    }
    
    .range-labels {
        display: flex;
        justify-content: space-between;
        font-family: monospace;
        font-size: 0.8rem;
        color: #888;
    }
    
    .saved-section {
        border-top: 1px solid #333;
        padding-top: 1rem;
        margin-top: 1rem;
    }
    
    .saved-section h3 {
        margin: 0 0 1rem 0;
        color: #ccc;
        font-size: 1rem;
    }
    
    .saved-items h4 {
        margin: 0 0 0.5rem 0;
        color: #888;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .saved-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem;
        background: #1e1e1e;
        border-radius: 4px;
        margin-bottom: 0.5rem;
        border: 1px solid #333;
    }
    
    .saved-item-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .saved-item-info strong {
        color: #ccc;
        font-size: 0.9rem;
    }
    
    .saved-item-desc {
        color: #888;
        font-size: 0.8rem;
    }
    
    .saved-item-query {
        color: #007acc;
        font-size: 0.8rem;
        background: #2a2d2e;
        padding: 0.25rem 0.5rem;
        border-radius: 3px;
        font-family: monospace;
    }
    
    .saved-item-actions {
        display: flex;
        gap: 0.5rem;
    }
    
    .load-btn, .delete-btn {
        padding: 0.25rem 0.5rem;
        border-radius: 3px;
        border: none;
        cursor: pointer;
        font-size: 0.75rem;
        transition: all 0.2s;
    }
    
    .load-btn {
        background: #007acc;
        color: white;
    }
    
    .load-btn:hover {
        background: #005a9e;
    }
    
    .delete-btn {
        background: #f44336;
        color: white;
    }
    
    .delete-btn:hover {
        background: #d32f2f;
    }
    
    /* Dialog Styles */
    .dialog-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }
    
    .dialog {
        background: #252526;
        border-radius: 8px;
        border: 1px solid #444;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow: hidden;
    }
    
    .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background: #2d2d2d;
        border-bottom: 1px solid #444;
    }
    
    .dialog-header h3 {
        margin: 0;
        color: #fff;
        font-size: 1.1rem;
    }
    
    .close-btn {
        background: none;
        border: none;
        color: #ccc;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 4px;
        transition: all 0.2s;
    }
    
    .close-btn:hover {
        background: #444;
        color: #fff;
    }
    
    .dialog-content {
        padding: 1rem;
    }
    
    .form-group {
        margin-bottom: 1rem;
    }
    
    .form-group label {
        display: block;
        color: #888;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .form-group input, .form-group textarea {
        width: 100%;
        background: #1e1e1e;
        border: 1px solid #444;
        color: #ccc;
        padding: 0.75rem;
        border-radius: 4px;
        font-size: 0.9rem;
        transition: border-color 0.2s;
        box-sizing: border-box;
    }
    
    .form-group input:focus, .form-group textarea:focus {
        outline: none;
        border-color: #007acc;
    }
    
    .form-group input.invalid {
        border-color: #f44336;
    }
    
    .dialog-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        padding: 1rem;
        background: #2d2d2d;
        border-top: 1px solid #444;
    }
    
    .cancel-btn, .save-confirm-btn {
        padding: 0.5rem 1rem;
        border-radius: 4px;
        border: none;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .cancel-btn {
        background: #333;
        color: #ccc;
    }
    
    .cancel-btn:hover {
        background: #444;
        color: #fff;
    }
    
    .save-confirm-btn {
        background: #007acc;
        color: white;
    }
    
    .save-confirm-btn:hover:not(:disabled) {
        background: #005a9e;
    }
    
    .save-confirm-btn:disabled {
        background: #666;
        color: #999;
        cursor: not-allowed;
    }
</style>
