<script>
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import Dashboard from './components/Dashboard.svelte';
  import Explorer from './components/Explorer.svelte';
  import Search from './components/Search.svelte';
  import Navbar from './components/Navbar.svelte';
  import TaintFlowViewer from './components/TaintFlowViewer.svelte';
  import Progress from './components/Progress.svelte';
  import SearchFilters from './components/SearchFilters.svelte';
  import { descriptions } from './descriptions.js';
  let context = { repo: 'Loading...', findings: [], hotspots: [], summary: {} };
  let moduleCategories = {};
  let searchTerm = '';
  let view = 'dashboard';
  let activeFile = null;
  let activeModule = null;
  let selectedFinding = null;
  let diffFinding = null;
  let showTaintFlow = false;
  let selectedFindingForFlow = null;
  let useDynamicScoring = false;
  let showProgress = false;
  let progressData = null;
  let filteredFindingsList = [];

  function deepMatch(finding, term) {
      if (!term) return true;
      term = term.toLowerCase();
      
      if (finding.title?.toLowerCase().includes(term)) return true;
      if (finding.source_module?.toLowerCase().includes(term)) return true;
      if (finding.description?.toLowerCase().includes(term)) return true;
      
      if (finding.metadata) {
          try {
              const metaStr = JSON.stringify(finding.metadata).toLowerCase();
              if (metaStr.includes(term)) return true;
          } catch(e) {}
      }
      return false;
  }

  // Handle search/filter updates from SearchFilters component
  function handleSearchUpdate(event) {
      const searchData = event.detail;
      filteredFindingsList = searchData.results;
  }

  // Check for active scans
  async function checkScanStatus() {
      try {
          const response = await fetch('/api/scan/status');
          if (response.ok) {
              const status = await response.json();
              if (status.status === 'running') {
                  showProgress = true;
                  progressData = status;
              }
          }
      } catch (e) {
          console.error('Failed to check scan status:', e);
      }
  }

  // Use filtered findings from SearchFilters if available, otherwise use default filtering
  $: effectiveFindings = filteredFindingsList.length > 0 ? filteredFindingsList : context.findings;
  
  $: effectiveFilteredFindings = effectiveFindings.filter(f => {
      // Apply view filter only if not using SearchFilters
      if (filteredFindingsList.length === 0) {
          const status = f.triage_status || 'UNTRIAGED';
          if (view === 'tp') return status === 'TP';
          if (view === 'fp') return status === 'FP';
      }
      return true;
  });

  $: chartSummary = searchTerm ? recalculateSummary(effectiveFilteredFindings) : context.summary;
  
  // Check for exploits
  $: hasExploits = effectiveFindings.some(f => f.metadata?.has_known_exploit);
  
  // Modules should probably reflect the current list? 
  // User said "TP can filter and show just TP". 
  // If I click a module, I want to see that module's TPs.
  // So availableModules should come from filteredFindings.
  $: filteredSummary = recalculateSummary(effectiveFilteredFindings);
  
  // Flatten all known modules from categories to show tabs even if empty
  $: allModules = [
      ...(moduleCategories.sources || []),
      ...(moduleCategories.extractors || []),
      ...(moduleCategories.enrichers || [])
  ];
  $: uniqueModules = [...new Set(allModules)];
  
  $: filteredContext = {
      ...context,
      findings: effectiveFilteredFindings,
      summary: filteredSummary
  };
  
  $: triageStats = {
      tp: effectiveFindings.filter(f => f.triage_status === 'TP').length,
      fp: effectiveFindings.filter(f => f.triage_status === 'FP').length,
      untriaged: effectiveFindings.filter(f => !f.triage_status || f.triage_status === 'UNTRIAGED').length,
      total: effectiveFindings.length
  };

  $: files = processFiles(filteredContext, useDynamicScoring);

  function recalculateSummary(findings) {
      const s = { total_findings: findings.length, by_severity: {}, by_module: {} };
      findings.forEach(f => {
          s.by_severity[f.severity] = (s.by_severity[f.severity] || 0) + 1;
          s.by_module[f.source_module] = (s.by_module[f.source_module] || 0) + 1;
      });
      return s;
  }

  onMount(async () => {
    // Load Monaco
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs/loader.min.js';
    script.onload = () => {
      window.require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});
      window.require(['vs/editor/editor.main'], (m) => {
        window.monaco = m;
      });
    };
    document.body.appendChild(script);

    // Load data and check for active scans
    await Promise.all([
      loadContextData(),
      checkScanStatus()
    ]);
  });

  async function loadContextData() {
    try {
      const [res, modRes] = await Promise.all([
          fetch('/api/context'),
          fetch('/api/modules')
      ]);
      
      if (res.ok) {
        context = await res.json();
      }
      if (modRes.ok) {
          moduleCategories = await modRes.json();
      }
    } catch (e) { console.error(e); }
  }

  function processFiles(data, useDynamicScoring = false) {
    const map = {};
    (data.hotspots||[]).forEach(h => {
        if(h.type==='file') {
            map[h.identifier] = { 
                path: h.identifier, 
                score: useDynamicScoring ? 0 : (h.score || 0), // Reset if dynamic
                findings: [],
                review_guide: h.review_guide,
                adjacency: h.adjacency
            };
        }
    });
    (data.findings||[]).forEach(f => {
        (f.metadata?.files || []).forEach(p => {
            if(!map[p]) map[p] = { path: p, score: 0, findings: [], review_guide: null, adjacency: null };
            map[p].findings.push(f);
            
            if (useDynamicScoring) {
                 // Dynamic Mode: Always take max priority score
                 if (f.priority_score !== undefined) {
                     if (f.priority_score > map[p].score) map[p].score = f.priority_score;
                 } else if (map[p].score === 0) {
                     // Fallback only if no score established
                     map[p].score += (f.severity==='critical'?10 : f.severity==='high'?5:1);
                 }
            } else {
                // Static Mode: Preserve backend score if present
                if (!map[p].score && f.priority_score) {
                     if (f.priority_score > map[p].score) map[p].score = f.priority_score;
                } else if (!map[p].score) {
                     // Legacy scoring fallback
                     map[p].score += (f.severity==='critical'?10 : f.severity==='high'?5:1);
                }
            }
        });
    });
    return Object.values(map).sort((a,b) => b.score - a.score);
  }

  function handleRecalculate() {
      useDynamicScoring = true;
  }

  function handleNavigate(e) {
      view = e.detail;
      selectedFinding = null;
  }

  async function handleMarkFinding(e) {
      const { finding, status } = e.detail;
      if (!finding.id) return;

      // Optimistic update
      const index = context.findings.findIndex(f => f.id === finding.id);
      if (index !== -1) {
          context.findings[index].triage_status = status;
          
          if (status === 'FP') {
              context.findings[index].research_value = 0.0;
              context.findings[index].confidence_score = 0.0;
              context.findings[index].priority_score = 0;
          }

          // Force reactivity by creating new array reference
          context.findings = [...context.findings]; 
          context = { ...context }; 
      }
      
      try {
          await fetch('/api/triage', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ id: finding.id, status })
          });
      } catch (err) {
          console.error("Failed to mark finding", err);
      }
  }

  function handleSearch(e) {
      searchTerm = e.detail;
  }
  
  function openFile(e) {
      activeFile = e.detail;
      view = 'explorer';
  }

  function handleOpenFinding(e) {
      const finding = e.detail;
      
      // If finding is from file analysis, go to explorer
      if (finding.source_module === 'semgrep_file_analysis') {
          const file = files.find(f => f.path === (finding.metadata?.file || finding.metadata?.files?.[0]));
          if (file) {
              activeFile = file;
              view = 'semgrep_file_analysis';
              return;
          }
      }
      
      // For others, show modal details
      selectedFinding = finding;
  }

  function handleViewDiff() {
      if (!selectedFinding) return;
      diffFinding = selectedFinding;
      selectedFinding = null;
      view = 'diff_view';
  }
  
  function openTaintFlow(finding) {
      selectedFindingForFlow = finding;
      showTaintFlow = true;
  }
  
  function closeTaintFlow() {
      showTaintFlow = false;
      selectedFindingForFlow = null;
  }
  
  function filterModule(e) {
      activeModule = e.detail;
      view = e.detail; // Navigate to module
  }

  function getViewTitle(v) {
      if (v === 'inbox') return 'Inbox (All Findings)';
      if (v === 'tp') return 'True Positives';
      if (v === 'fp') return 'False Positives';
      if (v === 'search') return 'Search Results';
      if (v === 'exploits') return 'Known Exploits';
      return 'Module: ' + v;
  }
  
  $: findingsToDisplay = (() => {
      if (['inbox', 'tp', 'fp'].includes(view)) return effectiveFilteredFindings;
      return effectiveFilteredFindings.filter(f => f.source_module === view);
  })();
  
  function getFindingsForView(v) {
      // Kept for getViewTitle logic if needed, but unused for list now
      return [];
  }

  function formatDate(d) {
      if (!d || d === 'Unknown') return 'Unknown';
      try {
          const date = new Date(d);
          if (isNaN(date.getTime())) return d;
          return date.toLocaleString();
      } catch(e) { return d; }
  }
</script>

<main>
  <Navbar 
    activeView={view} 
    modules={uniqueModules} 
    moduleCategories={moduleCategories}
    repoName={context.repo} 
    hasExploits={hasExploits}
    on:navigate={handleNavigate} 
    on:search={handleSearch}
  />
  
  <div class="content">
    {#if view === 'dashboard'}
      <Dashboard 
        summary={chartSummary}
        findings={effectiveFilteredFindings}
        {triageStats}
        {files} 
        repo={context.repo}
        on:openFile={openFile} 
        on:openFinding={handleOpenFinding} 
        on:filterModule={filterModule} 
        on:markFinding={handleMarkFinding}
        on:recalculate={handleRecalculate}
      />
    
    {:else if view === 'semgrep_file_analysis'}
      <div class="module-wrapper">
          <div class="module-header-block">
              <h2>File Analysis (Semgrep)</h2>
              <p>{descriptions.semgrep_file_analysis}</p>
          </div>
          <div class="explorer-container">
            <Explorer 
                files={files.filter(f => f.findings.some(find => find.source_module === 'semgrep_file_analysis'))} 
                {activeFile} 
                repoName={context.repo} 
                on:markFinding={handleMarkFinding}
            />
          </div>
      </div>

    {:else if view === 'explorer'}
      <Explorer 
        {files} 
        {activeFile} 
        repoName={context.repo} 
        on:markFinding={handleMarkFinding}
      />

    {:else if view === 'diff_view'}
      <Explorer 
        files={[]} 
        activeFinding={diffFinding} 
        repoName={context.repo} 
        on:markFinding={handleMarkFinding}
      />

    {:else if view === 'search'}
      <Search findings={effectiveFilteredFindings} on:openFinding={handleOpenFinding} />
      
    {:else}
      <!-- Generic Table for Inbox, TP, FP, and Modules -->
      <div class="module-view">
          <div class="header">
            <div class="title-group">
                <h2>{getViewTitle(view)}</h2>
                {#if descriptions[view]}
                    <p class="module-description">{descriptions[view]}</p>
                {/if}
            </div>
          </div>
          <div class="table-container">
            {#if findingsToDisplay.length === 0}
                <div class="empty-state">
                    <h3>No findings available</h3>
                    <p>This module was either not run or found no issues.</p>
                </div>
            {:else}
                <table>
                    <thead><tr><th>Target</th><th>Module</th><th>Research Value</th><th>Title</th><th>Actions</th></tr></thead>
                    <tbody>
                        {#each findingsToDisplay as finding}
                            <!-- svelte-ignore a11y-click-events-have-key-events -->
                            <tr on:click={() => handleOpenFinding({ detail: finding })}>
                                <td class="file">
                                    {#if finding.metadata?.file || finding.metadata?.files?.[0]}
                                        {finding.metadata?.file || finding.metadata?.files?.[0]}
                                    {:else if finding.metadata?.url}
                                        <a href={finding.metadata.url} target="_blank" on:click|stopPropagation>External Link ↗</a>
                                    {:else}
                                        N/A
                                    {/if}
                                </td>
                                <td class="mod-cell">{finding.source_module}</td>
                                <td>
                                    <span class="badge sev {finding.severity}">{finding.severity === 'critical' ? 'V. High' : finding.severity}</span>
                                    <span class="use-score" title="Confidence Score">Precision: {finding.confidence_score?.toFixed(1) || '-'}</span>
                                </td>
                                <td class="title">{finding.title}</td>
                                <td class="actions-cell">
                                    {#if finding.metadata?.taint_flows && finding.metadata.taint_flows.length > 0}
                                        <button class="btn-taint" on:click|stopPropagation={() => openTaintFlow(finding)} title="View Taint Flow">
                                            🌊 Flow
                                        </button>
                                    {/if}
                                    <button class="btn-xs success" class:selected={finding.triage_status === 'TP'} title="Mark TP" on:click|stopPropagation={() => handleMarkFinding({ detail: { finding, status: 'TP' } })}>✓</button>
                                    <button class="btn-xs danger" class:selected={finding.triage_status === 'FP'} title="Mark FP" on:click|stopPropagation={() => handleMarkFinding({ detail: { finding, status: 'FP' } })}>✗</button>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            {/if}
          </div>
      </div>
    {/if}

    {#if selectedFinding}
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <div class="modal-backdrop" on:click={() => selectedFinding = null}>
            <div class="modal" on:click|stopPropagation>
                <div class="modal-header">
                    <h2>{selectedFinding.title}</h2>
                    <button class="close-btn" on:click={() => selectedFinding = null}>&times;</button>
                </div>
                <div class="modal-body">
                    <div class="meta-row">
                        <span class="badge sev {selectedFinding.severity}">{selectedFinding.severity}</span>
                        <span class="mod">{selectedFinding.source_module}</span>
                        
                        <div class="triage-controls">
                            <button class="action-btn success small" class:selected={selectedFinding.triage_status === 'TP'} on:click={() => handleMarkFinding({ detail: { finding: selectedFinding, status: 'TP' } })}>
                                {selectedFinding.triage_status === 'TP' ? '✓ True Positive' : 'Mark TP'}
                            </button>
                            <button class="action-btn danger small" class:selected={selectedFinding.triage_status === 'FP'} on:click={() => handleMarkFinding({ detail: { finding: selectedFinding, status: 'FP' } })}>
                                {selectedFinding.triage_status === 'FP' ? '✗ False Positive' : 'Mark FP'}
                            </button>
                        </div>
                    </div>
                    
                    <div class="scores-row">
                        <div class="score-item">
                            <div class="score-label">Confidence</div>
                            <div class="score-desc">How reliable is the tool/signal?</div>
                            <div class="score-bar"><div class="score-fill" style="width: {(selectedFinding.confidence_score || 0)*100}%"></div></div>
                            <div class="score-val">{selectedFinding.confidence_score?.toFixed(1) || '0.0'}</div>
                        </div>
                        <div class="score-item">
                            <div class="score-label">Research Value</div>
                            <div class="score-desc">How actionable is this finding?</div>
                            <div class="score-bar"><div class="score-fill" style="width: {(selectedFinding.research_value || 0)*100}%"></div></div>
                            <div class="score-val">{selectedFinding.research_value?.toFixed(1) || '0.0'}</div>
                        </div>
                        <div class="score-item">
                            <div class="score-label">Impact</div>
                            <div class="score-desc">Technical severity / blast radius</div>
                            <div class="score-bar"><div class="score-fill" style="width: {(selectedFinding.severity_score || 0)*100}%"></div></div>
                            <div class="score-val">{selectedFinding.severity_score?.toFixed(1) || '0.0'}</div>
                        </div>
                    </div>

                    <p class="desc">{selectedFinding.description}</p>

                    {#if selectedFinding.metadata?.techs && selectedFinding.metadata.techs.length > 0}
                        <div class="field block">
                            <span class="label">Technologies:</span>
                            <div class="tag-cloud">
                                {#each selectedFinding.metadata.techs as tech}
                                    <span class="tag">{tech}</span>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.dependencies && selectedFinding.metadata.dependencies.length > 0}
                        <div class="field block">
                            <span class="label">Dependencies ({selectedFinding.metadata.dependencies.length}):</span>
                            <div class="dependency-list">
                                {#each selectedFinding.metadata.dependencies as dep}
                                    <div class="dep-item">
                                        {#if dep[0]}<span class="dep-eco">[{dep[0]}]</span>{/if}
                                        <span class="dep-name">{dep[1]}</span>
                                        {#if dep[2]}<span class="dep-ver">{dep[2]}</span>{/if}
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.state}
                        <div class="field">
                            <span class="label">Status:</span> {selectedFinding.metadata.state}
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.release_tag}
                        <div class="field">
                            <span class="label">Version:</span> {selectedFinding.metadata.release_tag}
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.created_at}
                        <div class="field">
                            <span class="label">Opened:</span> {formatDate(selectedFinding.metadata.created_at)}
                        </div>
                    {:else if selectedFinding.metadata?.committed_date}
                        <div class="field">
                            <span class="label">Committed:</span> {formatDate(selectedFinding.metadata.committed_date)}
                        </div>
                    {:else if selectedFinding.metadata?.published_at}
                        <div class="field">
                            <span class="label">Date:</span> {formatDate(selectedFinding.metadata.published_at)}
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.author}
                        <div class="field">
                            <span class="label">Author:</span> {selectedFinding.metadata.author}
                        </div>
                    {/if}
                    
                    {#if selectedFinding.metadata?.url}
                        <div class="field">
                            <span class="label">Link:</span> 
                            <a href={selectedFinding.metadata.url} target="_blank">{selectedFinding.metadata.url}</a>
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.commit_hash}
                        <div class="actions-row">
                            <button class="action-btn primary" on:click={handleViewDiff}>View Diff in Code Editor</button>
                            <a class="action-btn secondary" href={`https://github.com/${context.repo}/commit/${selectedFinding.metadata.commit_hash}`} target="_blank">View on GitHub ↗</a>
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.body}
                        <div class="field block">
                            <span class="label">Body:</span>
                            <pre class="body-text">{selectedFinding.metadata.body}</pre>
                        </div>
                    {/if}
                    
                    {#if selectedFinding.nvd_enrichment}
                        <div class="field block nvd-box">
                            <span class="label">CVE Analysis (NVD):</span>
                            <div class="nvd-content">
                                <div class="score-row">
                                    <span class="badge sev {selectedFinding.nvd_enrichment.severity?.toLowerCase() || 'critical'}">{selectedFinding.nvd_enrichment.severity || 'Unknown'}</span>
                                    <span class="cvss-score">CVSS: {selectedFinding.nvd_enrichment.cvss_score || '-'}</span>
                                </div>
                                <p class="nvd-desc">{selectedFinding.nvd_enrichment.description}</p>
                            </div>
                        </div>
                    {/if}

                    {#if selectedFinding.metadata?.has_known_exploit}
                        <div class="field block exploit-box">
                            <span class="label">⚠️ Known Exploit Detected</span>
                            <div class="exploit-content">
                                <div class="exploit-sources">
                                    {#each selectedFinding.metadata.exploit_data.sources as source}
                                        <span class="tag exploit-tag">{source}</span>
                                    {/each}
                                </div>
                                {#if selectedFinding.metadata.exploit_data.epss}
                                    <div class="epss-row">
                                        <strong>EPSS Score:</strong> {selectedFinding.metadata.exploit_data.epss}
                                        {#if selectedFinding.metadata.exploit_data.epss > 0.1}
                                            <span class="high-prob">(High Probability)</span>
                                        {/if}
                                    </div>
                                {/if}
                                {#if selectedFinding.metadata.exploit_data.kev_details}
                                    <div class="kev-details">
                                        <strong>CISA KEV:</strong>
                                        <p>{selectedFinding.metadata.exploit_data.kev_details.vulnerabilityName}</p>
                                        <p class="sm">Action: {selectedFinding.metadata.exploit_data.kev_details.requiredAction}</p>
                                    </div>
                                {/if}
                                {#if selectedFinding.metadata.exploit_data.trickest_url}
                                    <div class="trickest-link">
                                        <a href={selectedFinding.metadata.exploit_data.trickest_url} target="_blank">🔗 View Trickest PoC</a>
                                    </div>
                                {/if}
                            </div>
                        </div>
                    {/if}

                    <div class="raw-meta">
                        <h3>Raw Metadata</h3>
                        <pre>{JSON.stringify(selectedFinding.metadata, null, 2)}</pre>
                    </div>
                </div>
            </div>
        </div>
    {/if}
  </div>
  
  <!-- Progress Indicator -->
  <Progress bind:show={showProgress} scanData={progressData} />
  
  <!-- Search and Filters -->
  {#if context.findings && context.findings.length > 0}
    <SearchFilters 
      findings={context.findings} 
      on:search={handleSearchUpdate}
    />
  {/if}
</main>

<style>
  main { height: 100vh; display: flex; flex-direction: column; background: #1e1e1e; color: #ccc; }
  .content { flex: 1; overflow: hidden; position: relative; }
  
  .module-view { padding: 2rem; overflow-y: auto; height: 100%; box-sizing: border-box; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
  
  .title-group { display: flex; flex-direction: column; gap: 0.5rem; }
  .module-description { color: #888; font-size: 0.95rem; max-width: 800px; line-height: 1.5; margin: 0; }

  .module-wrapper { display: flex; flex-direction: column; height: 100%; }
  .module-header-block { padding: 1rem 2rem; background: #1e1e1e; border-bottom: 1px solid #333; flex-shrink: 0; }
  .module-header-block h2 { margin: 0 0 0.5rem 0; font-size: 1.2rem; color: #fff; }
  .module-header-block p { margin: 0; color: #888; font-size: 0.9rem; max-width: 800px; line-height: 1.5; }
  .explorer-container { flex: 1; overflow: hidden; }

  .table-container { background: #252526; border-radius: 8px; overflow: hidden; border: 1px solid #333; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; background: #2d2d2d; padding: 1rem; color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 0.75rem 1rem; border-bottom: 1px solid #333; font-size: 0.9rem; }
  tr:last-child td { border-bottom: none; }
  tr:hover { background: #2a2d2e; cursor: pointer; }
  
  .file { color: #fff; font-weight: 500; font-family: monospace; }
  .mod-cell { color: #888; font-size: 0.9rem; }
  .title { color: #ddd; }
  
  .badge { padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; display: inline-block; }
  .badge.sev.critical { background: rgba(241, 76, 76, 0.2); color: #f14c4c; border: 1px solid rgba(241, 76, 76, 0.3); }
  .badge.sev.high { background: rgba(204, 167, 0, 0.2); color: #cca700; border: 1px solid rgba(204, 167, 0, 0.3); }
  .badge.sev.medium { background: rgba(0, 122, 204, 0.2); color: #007acc; border: 1px solid rgba(0, 122, 204, 0.3); }
  .badge.sev.low, .badge.sev.info { background: #333; color: #ccc; border: 1px solid #444; }
  
  .use-score { background: #333; color: #aaa; padding: 1px 4px; border-radius: 3px; font-size: 0.7rem; font-family: monospace; margin-left: 5px; }

  .scores-row { display: flex; gap: 20px; margin-bottom: 20px; padding: 15px; background: #1e1e1e; border-radius: 4px; border: 1px solid #444; }
  .score-item { flex: 1; display: flex; flex-direction: column; gap: 4px; }
  .score-label { color: #fff; font-size: 0.85rem; font-weight: bold; }
  .score-desc { color: #888; font-size: 0.75rem; margin-bottom: 6px; }
  .score-bar { height: 8px; background: #333; border-radius: 4px; overflow: hidden; }
  .score-fill { height: 100%; background: #007acc; transition: width 0.3s ease; }
  .score-val { color: #ccc; font-family: monospace; font-size: 0.85rem; text-align: right; margin-top: 4px; }

  .btn { background: #333; border: 1px solid #555; color: white; padding: 6px 12px; cursor: pointer; border-radius: 4px; }
  .btn:hover { background: #444; }

  /* Modal Styles */
  .modal-backdrop { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000; }
  .modal { background: #252526; width: 80%; max-width: 800px; max-height: 80vh; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; border: 1px solid #444; }
  .modal-header { padding: 1rem; background: #2d2d2d; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }
  .modal-header h2 { margin: 0; font-size: 1.2rem; color: #fff; }
  .close-btn { background: none; border: none; color: #ccc; font-size: 1.5rem; cursor: pointer; }
  .modal-body { padding: 1.5rem; overflow-y: auto; flex: 1; }
  
  .meta-row { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.5rem; }
  .mod { color: #888; font-weight: bold; }
  .desc { font-size: 1rem; line-height: 1.5; margin-bottom: 1.5rem; color: #ddd; white-space: pre-wrap; }
  
  .field { margin-bottom: 1rem; }
  .field.block { margin-top: 1.5rem; }
  .label { color: #888; font-weight: bold; margin-right: 0.5rem; display: block; margin-bottom: 0.25rem; }
  .body-text { background: #1e1e1e; padding: 1rem; border-radius: 4px; white-space: pre-wrap; font-family: sans-serif; color: #ccc; max-height: 300px; overflow-y: auto; border: 1px solid #333; }
  
  .actions-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
  .action-btn { padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold; text-decoration: none; font-size: 0.9rem; text-align: center; border: none; }
  .action-btn.primary { background: #007acc; color: white; }
  .action-btn.primary:hover { background: #0062a3; }
  .action-btn.secondary { background: #333; color: #ccc; border: 1px solid #555; }
  .action-btn.secondary:hover { background: #444; }
  
  .action-btn.success { background: #1b5e20; color: white; border: 1px solid #2e7d32; }
  .action-btn.success:hover, .action-btn.success.selected { background: #2e7d32; }
  .action-btn.danger { background: #b71c1c; color: white; border: 1px solid #c62828; }
  .action-btn.danger:hover, .action-btn.danger.selected { background: #c62828; }
  .action-btn.small { padding: 4px 10px; font-size: 0.8rem; }

  .triage-controls { margin-left: auto; display: flex; gap: 0.5rem; }
  
  .btn-xs { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; border: none; cursor: pointer; color: white; margin-left: 4px; opacity: 0.4; }
  .btn-xs:hover { opacity: 0.8; }
  .btn-xs.selected { opacity: 1; border: 1px solid rgba(255,255,255,0.5); }
  .btn-xs.success { background: #2e7d32; }
  .btn-xs.danger { background: #c62828; }
  
  .actions-cell { text-align: right; white-space: nowrap; }

  .raw-meta { margin-top: 2rem; border-top: 1px solid #333; padding-top: 1rem; }
  .raw-meta h3 { font-size: 0.9rem; color: #888; margin-bottom: 0.5rem; }
  .raw-meta pre { background: #1e1e1e; padding: 1rem; border-radius: 4px; font-size: 0.8rem; color: #888; overflow-x: auto; }
  
  a { color: #3794ff; text-decoration: none; }
  a:hover { text-decoration: underline; }

  .tag-cloud { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
  .tag { background: #333; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; color: #ccc; border: 1px solid #444; }
  
  .dependency-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 0.5rem; max-height: 400px; overflow-y: auto; background: #1e1e1e; padding: 1rem; border-radius: 4px; border: 1px solid #333; margin-top: 0.5rem; }
  .dep-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; padding: 2px 0; border-bottom: 1px solid #2a2a2a; }
  .dep-eco { color: #888; font-size: 0.75rem; }
    .dep-name { color: #ddd; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .dep-ver { color: #666; font-size: 0.75rem; font-family: monospace; margin-left: auto; }

    .nvd-box { background: #2d2d2d; padding: 1rem; border-radius: 4px; border: 1px solid #444; }
    .score-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
    .cvss-score { font-weight: bold; color: #ccc; }
    .nvd-desc { margin: 0; font-size: 0.9rem; color: #ccc; }

    .exploit-box { background: rgba(183, 28, 28, 0.2); border: 1px solid #c62828; padding: 1rem; border-radius: 4px; }
    .exploit-box .label { color: #ff5252; margin-bottom: 0.5rem; display: block; font-size: 1rem; }
    .exploit-tag { background: #b71c1c; color: white; border-color: #d32f2f; }
    .epss-row { margin-top: 0.5rem; color: #ddd; }
    .high-prob { color: #ff5252; font-weight: bold; margin-left: 0.5rem; }
    .kev-details { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.1); }
    .kev-details p { margin: 0.25rem 0; font-size: 0.9rem; color: #ddd; }
    .kev-details .sm { font-size: 0.8rem; color: #aaa; }
    .trickest-link { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.1); }
    .trickest-link a { color: #ff5252; font-weight: bold; text-decoration: none; }
    .trickest-link a:hover { text-decoration: underline; }
  
  .btn-taint { background: #ff6b6b; border: none; color: white; padding: 4px 8px; font-size: 0.7rem; cursor: pointer; border-radius: 3px; margin-right: 4px; }
  .btn-taint:hover { background: #ff5252; }

  .empty-state { padding: 4rem 2rem; text-align: center; color: #666; }
  .empty-state h3 { font-size: 1.2rem; margin-bottom: 0.5rem; color: #888; }
</style>

<TaintFlowViewer 
  finding={selectedFindingForFlow} 
  show={showTaintFlow} 
  on:close={closeTaintFlow}
/>
