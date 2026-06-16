<script>
  export let findings;
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  let selectedModules = [];
  let selectedSeverities = [];
  
  // Extract unique values
  $: modules = [...new Set(findings.map(f => f.source_module))];
  $: severities = ['critical', 'high', 'medium', 'low', 'info']; // Fixed order

  // Initialize selection (select all by default if empty, but better to start empty = all?)
  // Let's assume empty means "all".

  $: filtered = findings.filter(f => {
      // Filter by Module
      if (selectedModules.length > 0 && !selectedModules.includes(f.source_module)) return false;
      // Filter by Severity
      if (selectedSeverities.length > 0 && !selectedSeverities.includes(f.severity)) return false;
      return true;
  });

  function toggleModule(m) {
      if (selectedModules.includes(m)) selectedModules = selectedModules.filter(x => x !== m);
      else selectedModules = [...selectedModules, m];
  }

  function toggleSeverity(s) {
      if (selectedSeverities.includes(s)) selectedSeverities = selectedSeverities.filter(x => x !== s);
      else selectedSeverities = [...selectedSeverities, s];
  }
  
  function formatSev(s) {
      return s === 'critical' ? 'V. High' : s.charAt(0).toUpperCase() + s.slice(1);
  }
</script>

<div class="search-view">
    <div class="filters">
        <div class="filter-group">
            <h3>Modules</h3>
            <div class="options">
                {#each modules as m}
                    <label>
                        <input type="checkbox" checked={selectedModules.includes(m)} on:change={() => toggleModule(m)}>
                        {m}
                    </label>
                {/each}
            </div>
        </div>
        
        <div class="filter-group">
            <h3>Research Value</h3>
            <div class="options">
                {#each severities as s}
                    <label>
                        <input type="checkbox" checked={selectedSeverities.includes(s)} on:change={() => toggleSeverity(s)}>
                        {formatSev(s)}
                    </label>
                {/each}
            </div>
        </div>
    </div>

    <div class="results">
        <div class="count">{filtered.length} results</div>
        <div class="table-container">
            <table>
                <thead><tr><th>Research Value</th><th>Module</th><th>Title</th></tr></thead>
                <tbody>
                    {#each filtered as finding}
                        <!-- svelte-ignore a11y-click-events-have-key-events -->
                        <tr on:click={() => dispatch('openFinding', finding)}>
                            <td>
                                <span class="badge sev {finding.severity}">{formatSev(finding.severity)}</span>
                                <span class="use-score" title="Confidence Score">Precision: {finding.confidence_score?.toFixed(1) || '-'}</span>
                            </td>
                            <td class="mod-cell">{finding.source_module}</td>
                            <td class="title-cell" title={finding.title}>{finding.title}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    .search-view { display: flex; flex-direction: column; height: 100%; padding: 1.5rem; box-sizing: border-box; gap: 1.5rem; }
    
    .filters { display: flex; gap: 2rem; background: #252526; padding: 1rem; border-radius: 8px; border: 1px solid #333; flex-wrap: wrap; }
    .filter-group h3 { font-size: 0.9rem; color: #888; margin: 0 0 0.5rem 0; text-transform: uppercase; }
    .options { display: flex; gap: 1rem; flex-wrap: wrap; }
    label { display: flex; align-items: center; gap: 0.5rem; color: #ccc; font-size: 0.9rem; cursor: pointer; user-select: none; }
    
    .results { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #252526; border-radius: 8px; border: 1px solid #333; }
    .count { padding: 0.75rem 1rem; border-bottom: 1px solid #333; color: #888; font-size: 0.85rem; }
    
    .table-container { flex: 1; overflow-y: auto; }
    table { width: 100%; border-collapse: collapse; }
    th { text-align: left; background: #2d2d2d; padding: 0.75rem 1rem; color: #888; font-size: 0.75rem; text-transform: uppercase; position: sticky; top: 0; }
    td { padding: 0.75rem 1rem; border-bottom: 1px solid #333; font-size: 0.9rem; color: #ccc; }
    tr:hover { background: #2a2d2e; cursor: pointer; }
    
    .badge { padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .badge.sev.critical { background: rgba(241, 76, 76, 0.2); color: #f14c4c; border: 1px solid rgba(241, 76, 76, 0.3); }
    .badge.sev.high { background: rgba(204, 167, 0, 0.2); color: #cca700; border: 1px solid rgba(204, 167, 0, 0.3); }
    .badge.sev.medium { background: rgba(0, 122, 204, 0.2); color: #007acc; border: 1px solid rgba(0, 122, 204, 0.3); }
    .badge.sev.low { background: #333; color: #ccc; border: 1px solid #444; }
    .use-score { background: #333; color: #aaa; padding: 1px 4px; border-radius: 3px; font-size: 0.7rem; font-family: monospace; margin-left: 5px; }
</style>
