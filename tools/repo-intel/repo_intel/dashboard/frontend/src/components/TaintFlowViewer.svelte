<script>
  import { onMount, createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  
  export let finding = null;
  export let show = false;
  
  let flowViewer;
  let monaco;
  let editor;
  let currentFlow = null;
  let currentStep = 0;
  let flowSteps = [];
  let loadingStep = false;
  
  $: if (show && finding && finding.metadata?.taint_flows) {
    loadTaintFlow();
  }
  
  onMount(async () => {
    // Wait for Monaco to be available
    if (!window.monaco) {
      await new Promise(r => {
        const check = setInterval(() => {
          if (window.monaco) { clearInterval(check); r(); }
        }, 100);
      });
    }
    monaco = window.monaco;
  });
  
  function loadTaintFlow() {
    if (!finding?.metadata?.taint_flows) return;
    
    // Completely destroy and recreate editor for new finding
    if (editor) {
      console.log('Destroying previous Monaco editor instance');
      editor.dispose();
      editor = null;
    }
    
    const taintFlows = finding.metadata.taint_flows;
    if (taintFlows.length > 0) {
      currentFlow = taintFlows[0];
      flowSteps = currentFlow.steps;
      currentStep = 0;
      console.log(`Loading taint flow with ${flowSteps.length} steps for finding: ${finding.title}`);
      
      // Wait a bit for DOM to settle, then load first step
      setTimeout(() => {
        loadStep(currentStep);
      }, 100);
    }
  }
  
  async function loadStep(stepIndex) {
    if (!flowSteps[stepIndex] || !monaco || loadingStep) return;
    
    loadingStep = true;
    const step = flowSteps[stepIndex];
    
    // Create fresh editor instance
    if (!editor && flowViewer) {
      console.log('Creating new Monaco editor instance');
      try {
        editor = monaco.editor.create(flowViewer, {
          theme: 'vs-dark',
          readOnly: true,
          automaticLayout: true,
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          fontSize: 14,
          lineNumbers: 'on',
          renderWhitespace: 'selection',
          wordWrap: 'on'
        });
        console.log('Monaco editor created successfully');
      } catch (e) {
        console.error('Failed to create Monaco editor:', e);
        loadingStep = false;
        return;
      }
    }
    
    // Show loading state
    if (editor) {
      const model = editor.getModel();
      if (model) {
        model.setValue('// Loading source code...');
      }
    }
    
    // Load file content with timeout and retry
    let content = "// Loading...";
    let retries = 2;
    
    while (retries > 0) {
      try {
        console.log(`Fetching source file: /api/source/${step.file} (attempt ${3 - retries})`);
        
        // Add timeout to prevent hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout
        
        const res = await fetch(`/api/source/${step.file}`, {
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        console.log(`Response status: ${res.status}`);
        
        if (res.ok) {
          content = await res.text();
          console.log(`Content length: ${content.length} characters`);
          if (!content || content.trim() === '') {
            content = `// Empty file: ${step.file}`;
          }
          break; // Success, exit retry loop
        } else {
          console.log(`Failed to fetch file: ${res.statusText}`);
          if (retries === 1) {
            // Last attempt failed
            content = `// Source code not available.\n// File: ${step.file}\n// HTTP Status: ${res.status} ${res.statusText}\n// \n// This file was not found in the current repository.\n// The SARIF file may reference a different repository.\n// \n// To view the source code, run:\n// repo-intel --modules sast_findings --sarif-file <sarif-file> --target <original-repo-url>`;
          }
        }
      } catch(e) { 
        console.error('Error loading source file:', e);
        if (e.name === 'AbortError') {
          if (retries === 1) {
            content = `// Request timeout for file: ${step.file}\n// The request took too long to complete.\n// Please try again or check if the file exists.`;
          }
        } else {
          if (retries === 1) {
            content = `// Error loading source file: ${step.file}\n// ${e.message}`;
          }
        }
      }
      
      retries--;
      if (retries > 0) {
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    // Set content and language
    const editorModel = editor.getModel();
    if (editorModel) {
      // Create a new model to ensure clean state
      const newModel = monaco.editor.createModel(content, getLanguage(step.file));
      editor.setModel(newModel);
      
      // Dispose the old model if it exists
      if (editorModel !== newModel) {
        editorModel.dispose();
      }
      
      console.log(`Set new model with ${content.length} characters for file: ${step.file}`);
    } else {
      editor.setValue(content);
      monaco.editor.setModelLanguage(editor.getModel(), getLanguage(step.file));
      console.log(`Set content directly with ${content.length} characters`);
    }
    
    // Highlight the step after a short delay to ensure content is rendered
    setTimeout(() => {
      highlightStep(step);
      loadingStep = false;
    }, 200);
  }
  
  function highlightStep(step) {
    if (!editor) return;
    
    const startLine = step.line || 1;
    const endLine = step.end_line || startLine;
    const startCol = step.column || 1;
    const endCol = step.end_column || startCol;
    
    // Clear previous decorations
    editor.deltaDecorations([], []);
    
    // Add decorations for the current step
    const decorations = [];
    
    // Highlight the specific range (if we have column info)
    if (startCol && endCol && startCol > 0 && endCol > 0) {
      decorations.push({
        range: new monaco.Range(startLine, startCol, endLine, endCol + 1),
        options: {
          className: 'taint-flow-highlight',
          isWholeLine: false,
          minimap: {
            color: '#ff6b6b',
            position: 1
          },
          stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
        }
      });
    }
    
    // Always highlight the entire line
    decorations.push({
      range: new monaco.Range(startLine, 1, startLine, 1),
      options: {
        className: 'taint-flow-line',
        isWholeLine: true,
        minimap: {
          color: '#4ecdc4',
          position: 2
        },
        stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
      }
    });
    
    // Apply decorations
    const appliedDecorations = editor.deltaDecorations([], decorations);
    
    // Scroll to the line with a small delay to ensure rendering
    setTimeout(() => {
      if (editor) {
        editor.revealLineInCenter(startLine);
        editor.setPosition({lineNumber: startLine, column: startCol || 1});
      }
    }, 100);
  }
  
  function getLanguage(path) {
    if (path.endsWith('.js') || path.endsWith('.jsx')) return 'javascript';
    if (path.endsWith('.ts') || path.endsWith('.tsx')) return 'typescript';
    if (path.endsWith('.py')) return 'python';
    if (path.endsWith('.java')) return 'java';
    if (path.endsWith('.go')) return 'go';
    if (path.endsWith('.c') || path.endsWith('.h')) return 'c';
    if (path.endsWith('.cpp') || path.endsWith('.hpp') || path.endsWith('.cc')) return 'cpp';
    if (path.endsWith('.cs')) return 'csharp';
    if (path.endsWith('.php')) return 'php';
    if (path.endsWith('.rb')) return 'ruby';
    return 'plaintext';
  }
  
  function nextStep() {
    if (currentStep < flowSteps.length - 1) {
      currentStep++;
      loadStep(currentStep);
    }
  }
  
  function prevStep() {
    if (currentStep > 0) {
      currentStep--;
      loadStep(currentStep);
    }
  }
  
  function goToStep(index) {
    currentStep = index;
    loadStep(currentStep);
  }
  
  function close() {
    show = false;
    dispatch('close');
  }
</script>

<style>
  .taint-flow-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .taint-flow-content {
    background: #1e1e1e;
    border-radius: 8px;
    width: 90%;
    height: 90%;
    max-width: 1200px;
    display: flex;
    flex-direction: column;
  }
  
  .taint-flow-header {
    padding: 20px;
    border-bottom: 1px solid #333;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .taint-flow-title {
    color: #fff;
    margin: 0;
    font-size: 18px;
  }
  
  .taint-flow-close {
    background: #ff6b6b;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .taint-flow-body {
    display: flex;
    flex: 1;
    overflow: hidden;
  }
  
  .taint-flow-sidebar {
    width: 300px;
    background: #252526;
    border-right: 1px solid #333;
    padding: 20px;
    overflow-y: auto;
  }
  
  .taint-flow-main {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  .taint-flow-controls {
    padding: 15px;
    background: #2d2d30;
    border-bottom: 1px solid #333;
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .taint-flow-viewer {
    flex: 1;
    position: relative;
  }
  
  .step-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .step-item {
    padding: 10px;
    margin-bottom: 5px;
    background: #2d2d30;
    border-radius: 4px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.2s;
  }
  
  .step-item:hover {
    background: #3e3e42;
    border-color: #007acc;
  }
  
  .step-item.active {
    background: #007acc;
    border-color: #007acc;
  }
  
  .step-number {
    display: inline-block;
    width: 25px;
    height: 25px;
    background: #007acc;
    color: white;
    text-align: center;
    line-height: 25px;
    border-radius: 50%;
    font-size: 12px;
    margin-right: 10px;
  }
  
  .step-item.active .step-number {
    background: #fff;
    color: #007acc;
  }
  
  .step-info {
    color: #cccccc;
    font-size: 12px;
  }
  
  .step-file {
    color: #9cdcfe;
    font-weight: bold;
  }
  
  .step-location {
    color: #ce9178;
  }
  
  .step-message {
    color: #d4d4d4;
    margin-top: 5px;
    font-style: italic;
  }
  
  .nav-button {
    background: #007acc;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .nav-button:disabled {
    background: #555;
    cursor: not-allowed;
  }
  
  .step-counter {
    color: #cccccc;
    font-size: 14px;
  }
  
  /* Monaco editor decorations */
  :global(.taint-flow-highlight) {
    background-color: rgba(255, 107, 107, 0.4) !important;
    border: 2px solid #ff6b6b !important;
    border-radius: 3px !important;
    box-shadow: 0 0 4px rgba(255, 107, 107, 0.6) !important;
    animation: pulse-highlight 2s ease-in-out !important;
  }
  
  :global(.taint-flow-line) {
    background-color: rgba(78, 205, 196, 0.15) !important;
    border-left: 4px solid #4ecdc4 !important;
    box-shadow: 0 0 8px rgba(78, 205, 196, 0.3) !important;
  }
  
  @keyframes pulse-highlight {
    0% { background-color: rgba(255, 107, 107, 0.6); }
    50% { background-color: rgba(255, 107, 107, 0.3); }
    100% { background-color: rgba(255, 107, 107, 0.4); }
  }
</style>

{#if show && finding}
  <div class="taint-flow-modal" on:click={close}>
    <div class="taint-flow-content" on:click|stopPropagation>
      <div class="taint-flow-header">
        <h3 class="taint-flow-title">
          Taint Flow: {finding.title}
        </h3>
        <button class="taint-flow-close" on:click={close}>Close</button>
      </div>
      
      <div class="taint-flow-body">
        <div class="taint-flow-sidebar">
          <h4 style="color: #fff; margin-bottom: 15px;">Flow Steps</h4>
          {#if flowSteps.length > 0}
            <ul class="step-list">
              {#each flowSteps as step, i}
                <li 
                  class="step-item" 
                  class:active={i === currentStep}
                  on:click={() => goToStep(i)}
                >
                  <span class="step-number">{i + 1}</span>
                  <div class="step-info">
                    <div class="step-file">{step.file}</div>
                    <div class="step-location">Line {step.line}{step.column ? `, Col ${step.column}` : ''}</div>
                    {#if step.message}
                      <div class="step-message">{step.message}</div>
                    {/if}
                  </div>
                </li>
              {/each}
            </ul>
          {:else}
            <p style="color: #888;">No taint flow data available</p>
          {/if}
        </div>
        
        <div class="taint-flow-main">
          <div class="taint-flow-controls">
            <button class="nav-button" on:click={prevStep} disabled={currentStep === 0}>
              ← Previous
            </button>
            <span class="step-counter">
              Step {currentStep + 1} of {flowSteps.length}
            </span>
            <button class="nav-button" on:click={nextStep} disabled={currentStep === flowSteps.length - 1}>
              Next →
            </button>
          </div>
          
          <div class="taint-flow-viewer" bind:this={flowViewer}></div>
        </div>
      </div>
    </div>
  </div>
{/if}
