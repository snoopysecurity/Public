<script>
  export let activeView;
  export let repoName;
  export let modules = [];
  export let moduleCategories = {};
  export let hasExploits = false;
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function formatName(name) {
      if (name === 'semgrep_file_analysis') return 'File Analysis';
      if (name === 'semgrep_code_intel') return 'Code Intel';
      if (name === 'github_issues_analyse') return 'GH Issues';
      if (name === 'github_prs_analyse') return 'GH PRs';
      if (name === 'github_commits_analyse') return 'GH Commits';
      if (name === 'github_releases_analyse') return 'GH Releases';
      if (name === 'dependency_analysis') return 'Dependencies';
      if (name === 'tech_stack_analysis') return 'Repo Stack';
      if (name === 'contributors') return 'Repo Contributors';
      if (name === 'semgrep') return 'Semgrep analysis';
      if (name === 'unreleased_fix_detector') return 'Unreleased Fixes';
      if (name === 'sast_findings') return 'SAST Findings';
      if (name === 'exploits') return 'Exploits';
      return name.replace(/_/g, ' ').replace('analyse', '').trim();
  }

  $: groupedModules = {
    sources: (moduleCategories.sources || []).filter(m => modules.includes(m)),
    extractors: (moduleCategories.extractors || []).filter(m => modules.includes(m)),
    enrichers: (moduleCategories.enrichers || []).filter(m => modules.includes(m)),
    other: modules.filter(m => {
        const cats = moduleCategories;
        return !(cats.sources?.includes(m) || cats.extractors?.includes(m) || cats.enrichers?.includes(m));
    })
  };
</script>

<nav>
  <div class="nav-left-group">
    <div class="brand">
      <span class="icon">🛡️</span>
      <span class="title">Repo Intel</span>
      {#if repoName}
        <span class="repo">{repoName}</span>
      {/if}
    </div>
    
    <div class="static-tabs">
        <button class:active={activeView === 'dashboard'} on:click={() => dispatch('navigate', 'dashboard')}>Overview</button>
        
        <div class="sep"></div>

        <div class="dropdown-group">
          <button class:active={activeView === 'inbox'} on:click={() => dispatch('navigate', 'inbox')}>Inbox</button>
          <div class="dropdown-content">
              <button class:active={activeView === 'tp'} on:click={() => dispatch('navigate', 'tp')}>TP</button>
              <button class:active={activeView === 'fp'} on:click={() => dispatch('navigate', 'fp')}>FP</button>
          </div>
        </div>
        
        <div class="sep"></div>
    </div>
  </div>

  <div class="modules-container">
    <div class="modules-row top">
        {#if groupedModules.sources.length > 0}
            <div class="dropdown-group">
                <button>Sources ▾</button>
                <div class="dropdown-content">
                    {#each groupedModules.sources as mod}
                        <button class:active={activeView === mod} on:click={() => dispatch('navigate', mod)}>
                            {formatName(mod)}
                        </button>
                    {/each}
                </div>
            </div>
        {/if}

        {#if groupedModules.extractors.length > 0}
            <div class="dropdown-group">
                <button>Extractors ▾</button>
                <div class="dropdown-content">
                    {#each groupedModules.extractors as mod}
                        <button class:active={activeView === mod} on:click={() => dispatch('navigate', mod)}>
                            {formatName(mod)}
                        </button>
                    {/each}
                </div>
            </div>
        {/if}

        {#if groupedModules.enrichers.length > 0}
            <div class="dropdown-group">
                <button>Enrichers ▾</button>
                <div class="dropdown-content">
                    {#each groupedModules.enrichers as mod}
                        <button class:active={activeView === mod} on:click={() => dispatch('navigate', mod)}>
                            {formatName(mod)}
                        </button>
                    {/each}
                </div>
            </div>
        {/if}
        
        {#if groupedModules.other.length > 0}
             <div class="dropdown-group">
                <button>Other ▾</button>
                <div class="dropdown-content">
                    {#each groupedModules.other as mod}
                        <button class:active={activeView === mod} on:click={() => dispatch('navigate', mod)}>
                            {formatName(mod)}
                        </button>
                    {/each}
                </div>
            </div>
        {/if}

        <button class:active={activeView === 'search'} on:click={() => dispatch('navigate', 'search')}>
          Search
        </button>
    </div>
  </div>

  <div class="search-container">
    <span class="search-icon">🔍</span>
    <input 
      type="text" 
      placeholder="Search findings..." 
      on:input={(e) => dispatch('search', e.target.value)}
    >
  </div>
</nav>

<style>
  nav {
    min-height: 50px;
    height: auto;
    background: #1e1e1e;
    border-bottom: 1px solid #333;
    display: flex;
    padding: 0 1.5rem;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .nav-left-group {
    display: flex;
    align-items: center;
    height: 50px;
    flex-shrink: 0;
  }

  .brand { 
    display: flex; 
    align-items: center; 
    gap: 0.75rem; 
    min-width: 200px; 
    flex-shrink: 0; 
    margin-right: 1rem; 
  }
  .title { font-weight: 600; color: #fff; font-size: 1.1rem; }
  .repo { color: #888; font-size: 0.9rem; border-left: 1px solid #444; padding-left: 0.75rem; }
  
  .static-tabs {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
  
  .sep { width: 1px; height: 20px; background: #444; margin: 0 4px; }

  .modules-container {
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .modules-row {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .modules-row.top {
    height: 50px;
  }

  .modules-row.bottom {
    min-height: 40px;
    padding-bottom: 5px;
  }
  
  button {
    background: transparent;
    border: none;
    color: #888;
    height: 40px;
    padding: 0 0.5rem;
    cursor: pointer;
    font-size: 0.85rem;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    white-space: nowrap;
    flex-shrink: 0;
  }
  
  button:hover { color: #ccc; }
  button.active { color: #fff; border-bottom-color: #007acc; }

  /* Search: Fixed width, right aligned, stays at top */
  .search-container {
    display: flex;
    align-items: center;
    background: #252526;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    padding: 4px 8px;
    width: 150px;
    flex-shrink: 0;
    margin-top: 10px; /* Vertically center in the 50px row */
  }
  
  .search-icon { font-size: 0.8rem; margin-right: 8px; opacity: 0.7; }
  
  input {
    background: transparent;
    border: none;
    color: #ccc;
    font-size: 0.9rem;
    width: 100%;
    outline: none;
  }
  
  input::placeholder { color: #666; }

  /* Dropdown Styles */
  .dropdown-group {
    position: relative;
    display: flex;
    align-items: center;
  }
  
  .dropdown-content {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    background-color: #252526;
    min-width: 100px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    border: 1px solid #3e3e42;
    z-index: 100;
    flex-direction: column;
    padding: 4px 0;
  }

  .dropdown-group:hover .dropdown-content {
    display: flex;
  }

  .dropdown-content button {
    width: 100%;
    text-align: left;
    height: 35px;
    border-bottom: none;
    border-left: 2px solid transparent;
    padding: 0 1rem;
  }

  .dropdown-content button:hover {
    background-color: #333;
  }

  .dropdown-content button.active {
    border-left-color: #007acc;
    border-bottom-color: transparent;
    color: #fff;
    background-color: #2d2d2d;
  }

  .exploits-btn { color: #ff5252; font-weight: bold; }
  .exploits-btn:hover { color: #ff8a80; background: rgba(183, 28, 28, 0.1); }
  .exploits-btn.active { color: #ff5252; border-bottom-color: #ff5252; }
</style>
