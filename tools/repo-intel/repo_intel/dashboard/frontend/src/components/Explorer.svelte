<script>
  import { onMount, tick, createEventDispatcher } from 'svelte';
  import TaintFlowViewer from './TaintFlowViewer.svelte';
  const dispatch = createEventDispatcher();
  
  export let files;
  export let activeFile; // Can be null initially
  export let activeFinding = null; // Can be null
  export let repoName = '';
  
  let editorContainer;
  let diffContainer;
  let monaco;
  let editor;
  let diffEditor;
  let isDiffMode = false;
  let commitFiles = [];
  let currentDiffHash = null;
  let diffActiveFile = '';
  let searchTerm = '';
  let expandedFinding = null;
  let activeDecorations = [];
  let showTaintFlow = false;
  let selectedFindingForFlow = null;
  
  $: filteredFiles = files.filter(f => f.path.toLowerCase().includes(searchTerm.toLowerCase()));
  
  // Update activeFile if files list updates (e.g. status changes)
  $: if (activeFile && files) {
      const updatedFile = files.find(f => f.path === activeFile.path);
      if (updatedFile && updatedFile !== activeFile) {
          activeFile = updatedFile;
      }
  }

  // Re-run loadFile when activeFile changes
  $: if (activeFile && monaco && editorContainer) {
      loadFile(activeFile);
  }

  // Trigger diff if activeFinding provided
  $: if (activeFinding && monaco && (editor || diffEditor)) {
      showDiff(activeFinding);
  }

  onMount(async () => {
      // Wait for Monaco to be available (loaded by App or index.html)
      if (!window.monaco) {
          await new Promise(r => {
              const check = setInterval(() => {
                  if (window.monaco) { clearInterval(check); r(); }
              }, 100);
          });
      }
      monaco = window.monaco;
      
      // Init Diff Editor (hidden initially)
      if (diffContainer) {
          diffEditor = monaco.editor.createDiffEditor(diffContainer, {
              readOnly: true,
              automaticLayout: true
          });
      }
      
      // If active file passed, load it
      if (activeFile) loadFile(activeFile);
  });

  async function loadFile(file) {
      isDiffMode = false;
      if (!editor) {
          editor = monaco.editor.create(editorContainer, {
              value: "Loading...",
              theme: 'vs-dark',
              readOnly: true,
              automaticLayout: true,
              minimap: { enabled: true }
          });
      }
      
      let content = "// Loading...";
      try {
          const res = await fetch(`/api/source/${file.path}`);
          if (res.ok) content = await res.text();
          else content = `// Source code not available.\n// File: ${file.path}`;
      } catch(e) { content = "// Error loading source."; }
      
      const model = editor.getModel();
      if (model) {
          model.setValue(content);
          monaco.editor.setModelLanguage(model, getLanguage(file.path));
      } else {
          // Should default model exists
          editor.setValue(content);
      }
      
      updateMarkers(file.findings);
  }

  function getLanguage(path) {
      if (path.endsWith('.js') || path.endsWith('.jsx')) return 'javascript';
      if (path.endsWith('.ts') || path.endsWith('.tsx')) return 'typescript';
      if (path.endsWith('.py')) return 'python';
      if (path.endsWith('.html')) return 'html';
      if (path.endsWith('.css')) return 'css';
      if (path.endsWith('.json')) return 'json';
      if (path.endsWith('.java')) return 'java';
      if (path.endsWith('.md')) return 'markdown';
      return 'plaintext';
  }

  function updateMarkers(findings) {
      const markers = findings.map(f => ({
          startLineNumber: f.metadata?.line || 1,
          startColumn: 1,
          endLineNumber: f.metadata?.line || 1,
          endColumn: 1000,
          message: `[${f.source_module}] ${f.title}`,
          severity: f.severity === 'critical' || f.severity === 'high' ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Warning
      }));
      monaco.editor.setModelMarkers(editor.getModel(), 'owner', markers);
  }

  async function showDiff(finding) {
      if (!diffEditor) return;
      isDiffMode = true;
      await tick(); // Wait for DOM update
      diffEditor.layout();
      
      const hash = finding.metadata.commit_hash;
      currentDiffHash = hash;
      
      // Fetch files changed in commit
      try {
          const res = await fetch(`/api/commit_files/${hash}`);
          if (res.ok) {
              commitFiles = await res.json();
          } else {
              commitFiles = [activeFile.path];
          }
      } catch (e) {
          commitFiles = [activeFile.path];
      }

      // Determine initial file to show
      const findingFile = finding.metadata.file || finding.metadata.files?.[0];
      // Try to match finding file, otherwise active file, otherwise first changed file
      if (commitFiles.includes(findingFile)) diffActiveFile = findingFile;
      else if (commitFiles.includes(activeFile?.path)) diffActiveFile = activeFile.path;
      else diffActiveFile = commitFiles[0];
      
      await loadDiffForFile();
  }

  async function loadDiffForFile() {
      if (!currentDiffHash || !diffActiveFile) return;
      
      const hash = currentDiffHash;
      const filePath = diffActiveFile;
      
      try {
          const [original, modified] = await Promise.all([
              fetch(`/api/file_at_commit?commit=${hash}^&path=${filePath}`).then(r => r.ok ? r.text() : ""),
              fetch(`/api/file_at_commit?commit=${hash}&path=${filePath}`).then(r => r.ok ? r.text() : "")
          ]);
          
          const originalModel = monaco.editor.createModel(original, getLanguage(filePath));
          const modifiedModel = monaco.editor.createModel(modified, getLanguage(filePath));
          
          diffEditor.setModel({ original: originalModel, modified: modifiedModel });
      } catch (e) {
          console.error("Diff failed", e);
      }
  }

  function closeDiff() {
      isDiffMode = false;
      if (activeFile) loadFile(activeFile);
  }

  function handleClickFinding(finding) {
      if (finding.metadata?.commit_hash) {
          showDiff(finding);
      } else {
          scrollToFinding(finding);
      }
  }

  async function scrollToFinding(f) {
      if (isDiffMode) {
          closeDiff();
          await tick();
      }
      
      // Wait for DOM update
      await tick();
      
      if (!editor) {
          console.warn("Editor not ready for scroll. Attempting to load...");
          await loadFile(activeFile);
          await tick();
      }
      
      if (editor) {
          const line = f.metadata?.line;
          if (!line) return; // No line info to scroll to
          
          try {
              editor.revealLineInCenter(line);
              editor.setPosition({lineNumber: line, column: 1});
              editor.focus();
              
              // Highlight
              activeDecorations = editor.deltaDecorations(activeDecorations, [
                  {
                      range: new monaco.Range(line, 1, line, 1),
                      options: {
                          isWholeLine: true,
                          className: 'active-highlight'
                      }
                  }
              ]);
          } catch (e) {
              console.error("Scroll failed", e);
          }
      }
  }
  
  function openTaintFlow(finding) {
      selectedFindingForFlow = finding;
      showTaintFlow = true;
  }
  
  function closeTaintFlow() {
      showTaintFlow = false;
      selectedFindingForFlow = null;
  }
</script>

<div class="explorer">
    <aside class="sidebar">
        <div class="search">
            <input type="text" placeholder="Filter files..." bind:value={searchTerm}>
        </div>
        <ul class="file-list">
            {#each filteredFiles as file}
                <!-- svelte-ignore a11y-click-events-have-key-events -->
                <li class:active={activeFile === file} on:click={() => activeFile = file}>
                    <div class="name">{file.path}</div>
                    <span class="badge" class:crit={file.score >= 10}>{file.findings.length}</span>
                </li>
            {/each}
        </ul>
    </aside>
    
    <div class="main">
        {#if isDiffMode}
            <div class="diff-header">
                <span class="diff-title">Commit: {currentDiffHash?.substring(0,7)}</span>
                <select bind:value={diffActiveFile} on:change={loadDiffForFile} class="diff-select">
                    {#each commitFiles as file}
                        <option value={file}>{file}</option>
                    {/each}
                </select>
                <button class="btn-close" on:click={closeDiff}>Close Diff</button>
            </div>
        {/if}
        <div class="editors" class:has-header={isDiffMode}>
            <div class="editor-container" bind:this={editorContainer} class:hidden={isDiffMode}></div>
            <div class="diff-container" bind:this={diffContainer} class:hidden={!isDiffMode}></div>
        </div>
        
        <div class="findings-panel">
            <div class="panel-header">Audit Guide & Findings for {activeFile?.path || '...'}</div>
            <div class="panel-content">
                {#if activeFile?.review_guide || activeFile?.adjacency}
                    <div class="audit-guide">
                        {#if activeFile.review_guide?.summary}
                            <div class="guide-title">🕵️ Why am I looking here?</div>
                            <div class="guide-text">{activeFile.review_guide.summary}</div>
                        {/if}

                        {#if activeFile.review_guide?.questions && activeFile.review_guide.questions.length > 0}
                            <div class="guide-questions">
                                <div class="guide-q-title">Suggested Review Questions</div>
                                <ul class="guide-q-list">
                                    {#each activeFile.review_guide.questions as q}
                                        <li>{q}</li>
                                    {/each}
                                </ul>
                            </div>
                        {/if}

                        {#if activeFile.adjacency}
                            <div class="adjacency-box">
                                {#if activeFile.adjacency.importers && activeFile.adjacency.importers.length > 0}
                                    <div class="adj-group">
                                        <span class="adj-label">Referenced By:</span>
                                        {#each activeFile.adjacency.importers as p}
                                            <!-- svelte-ignore a11y-click-events-have-key-events -->
                                            <!-- We dispatch an event or call parent to switch file, or handle locally if files prop contains it -->
                                            <!-- Assuming dispatch('openFile', p) works if App handles it, or check if we can switch activeFile directly -->
                                            <!-- Explorer receives 'files' prop, so we can find it. -->
                                            <span class="adj-link" on:click={() => {
                                                const target = files.find(f => f.path === p);
                                                if(target) activeFile = target;
                                            }}>{p}</span>
                                        {/each}
                                    </div>
                                {/if}
                                {#if activeFile.adjacency.siblings && activeFile.adjacency.siblings.length > 0}
                                    <div class="adj-group">
                                        <span class="adj-label">Siblings:</span>
                                        {#each activeFile.adjacency.siblings as p}
                                            <!-- svelte-ignore a11y-click-events-have-key-events -->
                                            <span class="adj-link" on:click={() => {
                                                const target = files.find(f => f.path.endsWith(p)); // heuristic matching or full path?
                                                // Siblings are just filenames usually from backend.
                                                // We need to resolve path. 
                                                // Backend Adjacency logic: siblings are just filenames.
                                                // Frontend needs full path.
                                                // Maybe safer to skip link if we can't resolve easily, or just show text.
                                                // But let's try.
                                            }}>{p}</span>
                                        {/each}
                                    </div>
                                {/if}
                            </div>
                        {/if}
                    </div>
                {/if}

                {#each activeFile?.findings || [] as finding}
                    <!-- svelte-ignore a11y-click-events-have-key-events -->
                    <div class="finding-row" on:click={() => handleClickFinding(finding)}>
                        <div class="row-header">
                            <span class="sev {finding.severity}">{finding.severity === 'critical' ? 'V. High' : finding.severity}</span>
                            <span class="use-score" title="Confidence Score">Precision: {finding.confidence_score?.toFixed(1) || '-'}</span>
                            <span class="mod">{finding.source_module}</span>
                            <span class="msg">{finding.title}</span>
                            <div class="actions">
                                {#if finding.metadata?.taint_flows && finding.metadata.taint_flows.length > 0}
                                    <button class="btn-taint" on:click|stopPropagation={() => openTaintFlow(finding)} title="View Taint Flow">
                                        🌊 Flow
                                    </button>
                                {/if}
                                <button class="btn-xs success" class:selected={finding.triage_status === 'TP'} title="Mark TP" on:click|stopPropagation={() => dispatch('markFinding', { finding, status: 'TP' })}>✓</button>
                                <button class="btn-xs danger" class:selected={finding.triage_status === 'FP'} title="Mark FP" on:click|stopPropagation={() => dispatch('markFinding', { finding, status: 'FP' })}>✗</button>
                                <button class="btn-icon" on:click|stopPropagation={() => expandedFinding = expandedFinding === finding ? null : finding}>
                                    {expandedFinding === finding ? '▼' : '▶'}
                                </button>
                                {#if finding.metadata?.commit_hash}
                                    <button class="btn-diff" on:click|stopPropagation={() => showDiff(finding)}>Diff</button>
                                    {#if repoName && !repoName.startsWith('http')}
                                        <a href={`https://github.com/${repoName}/commit/${finding.metadata.commit_hash}`} target="_blank" class="btn-icon" title="View on GitHub" on:click|stopPropagation>
                                            GitHub ↗
                                        </a>
                                    {/if}
                                {/if}
                            </div>
                        </div>
                        {#if expandedFinding === finding}
                            <div class="finding-details" on:click|stopPropagation>
                                <div class="scores-row">
                                    <div class="score-item">
                                        <div class="score-label">Confidence</div>
                                        <div class="score-desc">How reliable is the tool/signal?</div>
                                        <div class="score-bar"><div class="score-fill" style="width: {(finding.confidence_score || 0)*100}%"></div></div>
                                        <div class="score-val">{finding.confidence_score?.toFixed(1) || '0.0'}</div>
                                    </div>
                                    <div class="score-item">
                                        <div class="score-label">Research Value</div>
                                        <div class="score-desc">How actionable is this finding?</div>
                                        <div class="score-bar"><div class="score-fill" style="width: {(finding.research_value || 0)*100}%"></div></div>
                                        <div class="score-val">{finding.research_value?.toFixed(1) || '0.0'}</div>
                                    </div>
                                    <div class="score-item">
                                        <div class="score-label">Impact</div>
                                        <div class="score-desc">Technical severity / blast radius</div>
                                        <div class="score-bar"><div class="score-fill" style="width: {(finding.severity_score || 0)*100}%"></div></div>
                                        <div class="score-val">{finding.severity_score?.toFixed(1) || '0.0'}</div>
                                    </div>
                                </div>
                                
                                {#if finding.metadata?.description}
                                    <div class="desc">{finding.metadata.description}</div>
                                {/if}
                                
                                {#if finding.metadata?.body}
                                    <div class="body-content">
                                        <div class="body-label">Description/Body:</div>
                                        <pre class="body-text">{finding.metadata.body}</pre>
                                    </div>
                                {/if}
                                
                                <div class="detail-grid">
                                    {#each Object.entries(finding.metadata || {}) as [key, val]}
                                        {#if key !== 'description' && key !== 'files' && key !== 'line' && key !== 'body'}
                                            <div class="key">{key}:</div>
                                            <div class="val">
                                                {#if key === 'references' && Array.isArray(val)}
                                                    {#each val as ref}
                                                        <a href={ref} target="_blank" rel="noopener">{ref}</a><br>
                                                    {/each}
                                                {:else}
                                                    {typeof val === 'object' ? JSON.stringify(val) : val}
                                                {/if}
                                            </div>
                                        {/if}
                                    {/each}
                                </div>
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        </div>
    </div>
</div>

<style>
    .explorer { display: flex; height: 100%; overflow: hidden; }
    
    .sidebar { width: 300px; background: #252526; border-right: 1px solid #3e3e42; display: flex; flex-direction: column; }
    .search { padding: 0.5rem; border-bottom: 1px solid #3e3e42; }
    .search input { width: 100%; background: #333; border: 1px solid #444; color: #ccc; padding: 4px; box-sizing: border-box; }
    
    .file-list { flex: 1; overflow-y: auto; list-style: none; padding: 0; margin: 0; }
    .file-list li { padding: 6px 12px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid transparent; }
    .file-list li:hover { background: #2a2d2e; }
    .file-list li.active { background: #37373d; color: #fff; border-left-color: #007acc; }
    .badge { background: #333; padding: 2px 6px; border-radius: 10px; font-size: 0.75rem; }
    .badge.crit { background: #f14c4c; color: white; }
    
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
    
    .diff-header { height: 40px; background: #2d2d2d; border-bottom: 1px solid #3e3e42; display: flex; align-items: center; padding: 0 1rem; gap: 1rem; }
    .diff-title { color: #ccc; font-weight: bold; font-size: 0.9rem; }
    .diff-select { background: #1e1e1e; color: #ccc; border: 1px solid #3e3e42; padding: 4px; border-radius: 4px; flex: 1; max-width: 400px; }
    .btn-close { background: #333; color: #ccc; border: 1px solid #444; padding: 4px 12px; cursor: pointer; border-radius: 4px; font-size: 0.8rem; }
    .btn-close:hover { background: #444; }
    
    .editors { flex: 1; position: relative; }
    .editors.has-header { height: calc(100% - 40px); }
    .editor-container, .diff-container { width: 100%; height: 100%; position: absolute; top: 0; left: 0; }
    .hidden { visibility: hidden; z-index: -1; }
    
    .findings-panel { height: 350px; background: #252526; border-top: 1px solid #3e3e42; display: flex; flex-direction: column; }
    .panel-header { padding: 6px 12px; background: #2d2d2d; font-weight: bold; font-size: 0.8rem; border-bottom: 1px solid #333; }
    .panel-content { flex: 1; overflow-y: auto; }

    /* Audit Guide Styles */
    .audit-guide { padding: 1rem; background: #1e262c; border-bottom: 1px solid #3e3e42; }
    .guide-title { font-weight: bold; color: #fff; margin-bottom: 0.5rem; }
    .guide-text { font-size: 0.9rem; line-height: 1.5; color: #ddd; margin-bottom: 1rem; }
    .guide-questions { background: rgba(0,0,0,0.2); padding: 0.8rem; border-radius: 4px; margin-bottom: 1rem; }
    .guide-q-title { color: #888; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem; font-weight: 600; }
    .guide-q-list { margin: 0; padding-left: 1.2rem; font-size: 0.9rem; color: #ccc; }
    .guide-q-list li { margin-bottom: 0.3rem; }
    .adjacency-box { display: flex; gap: 1rem; font-size: 0.85rem; flex-wrap: wrap; }
    .adj-group { display: flex; align-items: center; gap: 0.5rem; }
    .adj-label { color: #888; text-transform: uppercase; font-size: 0.7rem; font-weight: 600; }
    .adj-link { color: #007acc; cursor: pointer; background: rgba(0, 122, 204, 0.1); padding: 2px 6px; border-radius: 3px; }
    .adj-link:hover { background: rgba(0, 122, 204, 0.3); }
    
    .finding-row { border-bottom: 1px solid #333; display: flex; flex-direction: column; cursor: pointer; }
    .row-header { padding: 6px 12px; display: flex; gap: 10px; align-items: center; }
    .row-header:hover { background: #2a2d2e; }
    
    .sev { width: 60px; font-weight: bold; text-transform: uppercase; font-size: 0.7rem; }
    .sev.critical { color: #f14c4c; }
    .sev.high { color: #cca700; }
    .sev.medium { color: #007acc; }
    .sev.low, .sev.info { color: #888; }
    .use-score { background: #333; color: #aaa; padding: 1px 4px; border-radius: 3px; font-size: 0.7rem; font-family: monospace; margin-right: 5px; }
    .mod { width: 80px; color: #888; font-size: 0.8rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .msg { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .actions { display: flex; gap: 5px; }
    
    .btn-diff { background: #007acc; border: none; color: white; padding: 2px 6px; font-size: 0.7rem; cursor: pointer; border-radius: 3px; }
    .btn-icon { background: none; border: none; color: #888; cursor: pointer; font-size: 0.7rem; }
    .btn-xs { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; border: none; cursor: pointer; color: white; margin-right: 4px; opacity: 0.4; }
    .btn-xs:hover { opacity: 0.8; }
    .btn-xs.selected { opacity: 1; border: 1px solid rgba(255,255,255,0.5); }
    .btn-xs.success { background: #2e7d32; }
    .btn-xs.danger { background: #c62828; }
    
    .finding-details { background: #1e1e1e; padding: 12px; font-size: 0.85rem; border-top: 1px solid #333; }
    
    .scores-row { display: flex; gap: 20px; margin-bottom: 12px; padding: 12px; background: #252526; border-radius: 4px; border: 1px solid #3e3e42; }
    .score-item { flex: 1; display: flex; flex-direction: column; gap: 4px; }
    .score-label { color: #fff; font-size: 0.8rem; font-weight: bold; }
    .score-desc { color: #888; font-size: 0.7rem; margin-bottom: 4px; height: 2.2em; }
    .score-bar { height: 6px; background: #333; border-radius: 3px; overflow: hidden; }
    .score-fill { height: 100%; background: #007acc; transition: width 0.3s ease; }
    .score-val { color: #ccc; font-family: monospace; font-size: 0.8rem; text-align: right; margin-top: 2px; }
    
    .desc { margin-bottom: 12px; color: #ddd; line-height: 1.4; padding: 8px; background: #252526; border-radius: 4px; border-left: 3px solid #007acc; }
    
    .body-content { margin-bottom: 12px; background: #252526; padding: 8px; border-radius: 4px; }
    .body-label { color: #888; font-weight: bold; margin-bottom: 4px; font-size: 0.75rem; }
    .body-text { white-space: pre-wrap; font-family: sans-serif; color: #ccc; margin: 0; font-size: 0.8rem; max-height: 200px; overflow-y: auto; }

    .detail-grid { display: grid; grid-template-columns: 120px 1fr; gap: 8px; }
    .key { color: #888; font-weight: bold; text-align: right; padding-right: 10px; }
    .val { color: #ccc; word-break: break-all; font-family: monospace; }
    .val a { color: #3794ff; text-decoration: none; }
    .val a:hover { text-decoration: underline; }
    
    :global(.active-highlight) { background: rgba(55, 148, 255, 0.2); border-left: 2px solid #3794ff; }
    
    .btn-taint { background: #ff6b6b; border: none; color: white; padding: 2px 8px; font-size: 0.7rem; cursor: pointer; border-radius: 3px; margin-right: 4px; }
    .btn-taint:hover { background: #ff5252; }
</style>

<TaintFlowViewer 
  finding={selectedFindingForFlow} 
  show={showTaintFlow} 
  on:close={closeTaintFlow}
/>
