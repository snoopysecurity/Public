<script>
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import { descriptions } from '../descriptions.js';
  
  export let summary;
  export let findings;
  export let files;
  export let triageStats = { tp: 0, fp: 0, untriaged: 0, total: 0 };
  export let repo = '';
  
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  
  let modChartCanvas;
  let modChart;
  let rvChartCanvas;
  let rvChart;
  
  $: rvDist = calculateResearchDistribution(findings);

  function calculateResearchDistribution(findings) {
      const dist = { High: 0, Medium: 0, Low: 0 };
      
      findings.forEach(f => {
          const r = f.research_value !== undefined ? f.research_value : 0.5;
          
          if (r >= 0.7) dist.High++;
          else if (r >= 0.4) dist.Medium++;
          else dist.Low++;
      });
      return dist;
  }

  onMount(() => {
      renderCharts();
  });

  $: if (summary) {
      updateCharts();
  }
  
  $: cveFindings = (() => {
      // Deduplicate CVEs by ID
      const unique = {};
      findings.filter(f => f.signal_type === 'cve').forEach(f => {
          // Use metadata.cve_id as key, or title fallback
          const id = f.metadata?.cve_id || f.title;
          // Prefer the one with nvd_enrichment or critical severity
          if (!unique[id] || (f.nvd_enrichment && !unique[id].nvd_enrichment)) {
              unique[id] = f;
          }
      });
      return Object.values(unique);
  })();

  function updateCharts() {
      if (modChart) {
          const modData = summary.by_module || {};
          modChart.data.labels = Object.keys(modData);
          modChart.data.datasets[0].data = Object.values(modData);
          modChart.update();
      }
      
      if (rvChart) {
          rvChart.data.datasets[0].data = [rvDist.High, rvDist.Medium, rvDist.Low];
          rvChart.update();
      }
  }

  function renderCharts() {
      // Research Value Chart
      if (rvChart) rvChart.destroy();
      rvChart = new Chart(rvChartCanvas, {
          type: 'doughnut',
          data: {
              labels: ['High', 'Medium', 'Low'],
              datasets: [{
                  data: [rvDist.High, rvDist.Medium, rvDist.Low],
                  backgroundColor: ['#cca700', '#007acc', '#333'],
                  borderWidth: 0
              }]
          },
          options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { 
                  legend: { position: 'right', labels: { color: '#ccc' } } 
              }
          }
      });

      // Module Chart
      if (modChart) modChart.destroy();
      const modData = summary?.by_module || {};
      modChart = new Chart(modChartCanvas, {
          type: 'bar',
          data: {
              labels: Object.keys(modData),
              datasets: [{
                  label: 'Findings',
                  data: Object.values(modData),
                  backgroundColor: '#007acc',
                  borderRadius: 4
              }]
          },
          options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                  y: { grid: { color: '#333' }, ticks: { color: '#888' } },
                  x: { grid: { display: false }, ticks: { color: '#888' } }
              },
              plugins: { legend: { display: false } },
              onClick: (e, elements) => {
                  if (elements.length > 0) {
                      const index = elements[0].index;
                      const moduleName = Object.keys(modData)[index];
                      dispatch('filterModule', moduleName);
                  }
              }
          }
      });
  }

  function exportTPs() {
      const tps = findings.filter(f => f.triage_status === 'TP');
      if (tps.length === 0) {
          alert('No True Positive findings to export.');
          return;
      }
      
      const headers = ['ID', 'Module', 'Title', 'Severity', 'File', 'Line', 'Confidence', 'Triage Status', 'External Link', 'Raw Metadata'];
      
      const csvRows = [headers.join(',')];
      
      tps.forEach(f => {
          const escape = (text) => {
              if (text === null || text === undefined) return '';
              const str = String(text);
              if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                  return `"${str.replace(/"/g, '""')}"`;
              }
              return str;
          };

          const file = f.metadata?.file || f.metadata?.files?.[0] || '';
          const line = f.metadata?.line_number || f.metadata?.line || '';
          
          let link = f.metadata?.url || '';
          if (!link && f.metadata?.commit_hash && repo && repo !== 'Loading...') {
              link = `https://github.com/${repo}/commit/${f.metadata.commit_hash}`;
          }
          if (!link && f.metadata?.exploit_data?.trickest_url) {
              link = f.metadata.exploit_data.trickest_url;
          }
          
          const metadata = JSON.stringify(f.metadata || {});

          const row = [
              escape(f.id),
              escape(f.source_module),
              escape(f.title),
              escape(f.severity),
              escape(file),
              escape(line),
              escape(f.confidence_score),
              escape(f.triage_status),
              escape(link),
              escape(metadata)
          ];
          csvRows.push(row.join(','));
      });
      
      const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tp-export-${new Date().toISOString().slice(0,10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
  }
</script>

<div class="dashboard">
    <div class="dashboard-header">
        <div class="header-row">
            <h2 class="dash-title">Overview</h2>
            <button class="export-btn-main" on:click={exportTPs}>Export all TP Findings</button>
        </div>
        <p class="dashboard-description">{descriptions.dashboard}</p>
    </div>

    <div class="stats-row">
        <div class="card stat">
            <div class="num">{summary?.total_findings || 0}</div>
            <div class="label">Total Findings</div>
        </div>
        
        <!-- Triage Stats Area -->
        <div class="card stat triage-stat">
            <div class="triage-grid">
                <div class="t-item">
                    <span class="t-num tp">{triageStats.tp}</span>
                    <span class="t-lbl">TP</span>
                </div>
                <div class="t-item">
                    <span class="t-num fp">{triageStats.fp}</span>
                    <span class="t-lbl">FP</span>
                </div>
                <div class="t-item">
                    <span class="t-num">{triageStats.untriaged}</span>
                    <span class="t-lbl">Open</span>
                </div>
            </div>
            <div class="label">Triage Status</div>
        </div>

        <div class="card stat">
            <div class="num crit">{summary?.by_severity?.critical || 0}</div>
            <div class="label">Very High Prec.</div>
        </div>
        <div class="card stat">
            <div class="num high">{summary?.by_severity?.high || 0}</div>
            <div class="label">High Prec.</div>
        </div>
    </div>
    
    <div class="charts-row">
        <div class="card chart-card">
            <h3>Research Value Distribution</h3>
            <div class="canvas-container">
                <canvas bind:this={rvChartCanvas}></canvas>
            </div>
        </div>
        <div class="card chart-card">
            <h3>Module Breakdown (Click to Filter)</h3>
            <div class="canvas-container">
                <canvas bind:this={modChartCanvas}></canvas>
            </div>
        </div>
    </div>

    {#if cveFindings.length > 0}
        <div class="card list-card full-width" style="margin-bottom: 1.5rem; height: auto; max-height: 300px;">
            <h3>Detected CVEs ({cveFindings.length})</h3>
            <table>
                <thead><tr><th>ID</th><th>Severity</th><th>CVSS</th><th>Description</th></tr></thead>
                <tbody>
                    {#each cveFindings as finding}
                        <tr on:click={() => dispatch('openFinding', finding)}>
                            <td><span class="badge cve">{finding.metadata?.cve_id || finding.title}</span></td>
                            <td>
                                {#if finding.nvd_enrichment}
                                    <span class="badge sev {finding.nvd_enrichment.severity?.toLowerCase() || 'critical'}">{finding.nvd_enrichment.severity || 'Unknown'}</span>
                                {:else}
                                    <span class="badge sev critical">Critical</span>
                                {/if}
                            </td>
                            <td>{finding.nvd_enrichment?.cvss_score || '-'}</td>
                            <td>{finding.nvd_enrichment?.description || finding.description}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
    
    <div class="split-lists">
        <!-- Top Hotspots -->
        <div class="card list-card">
            <div class="card-header">
                <h3>Top Hotspots</h3>
                <button class="btn-refresh" on:click={() => dispatch('recalculate')}>Recalculate Scores</button>
            </div>
            <table>
                <thead><tr><th>File</th><th>Score</th><th>Findings</th></tr></thead>
                <tbody>
                    {#each files.slice(0, 8) as file}
                        <tr on:click={() => dispatch('openFile', file)}>
                            <td class="path" title={file.path}>{file.path}</td>
                            <td>
                                <span class="badge score" class:crit={file.score>=10} class:high={file.score>=5 && file.score<10}>
                                    {file.score}
                                </span>
                            </td>
                            <td class="reason">{file.findings.length}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>

        <!-- Recent Findings -->
        <div class="card list-card">
            <h3>Findings List ({findings.length})</h3>
            <table>
                <thead><tr><th>Research Value</th><th>Module</th><th>Title</th><th>Actions</th></tr></thead>
                <tbody>
                    {#each findings.slice(0, 8) as finding}
                        <tr on:click={() => dispatch('openFinding', finding)}>
                            <td>
                                <span class="badge sev {finding.severity}">{finding.severity === 'critical' ? 'V. High' : finding.severity}</span>
                                <span class="use-score" title="Confidence Score">Precision: {finding.confidence_score?.toFixed(1) || '-'}</span>
                            </td>
                            <td class="mod-cell">{finding.source_module}</td>
                            <td class="title-cell" title={finding.title}>{finding.title}</td>
                            <td class="actions-cell">
                                <button class="btn-xs success" class:selected={finding.triage_status === 'TP'} title="Mark TP" on:click|stopPropagation={() => dispatch('markFinding', { finding, status: 'TP' })}>✓</button>
                                <button class="btn-xs danger" class:selected={finding.triage_status === 'FP'} title="Mark FP" on:click|stopPropagation={() => dispatch('markFinding', { finding, status: 'FP' })}>✗</button>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    .dashboard { padding: 2rem; max-width: 1200px; margin: 0 auto; width: 100%; box-sizing: border-box; overflow-y: auto; height: 100%; }
    
    .dashboard-header { margin-bottom: 2rem; border-bottom: 1px solid #333; padding-bottom: 1rem; }
    .header-row { display: flex; justify-content: space-between; align-items: center; }
    .dash-title { margin: 0; font-size: 1.5rem; color: #fff; border: none; padding: 0; }
    .export-btn-main { background: #333; color: #ccc; border: 1px solid #555; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }
    .export-btn-main:hover { background: #444; color: #fff; border-color: #666; }
    .dashboard-description { color: #888; font-size: 0.95rem; max-width: 800px; line-height: 1.5; margin: 0.5rem 0 0 0; }

    .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 2rem; }
    .stat { text-align: center; padding: 1.5rem; }
    .num { font-size: 2.5rem; font-weight: 700; color: #fff; }
    .num.crit { color: #f14c4c; }
    .num.high { color: #cca700; }
    .label { color: #888; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; margin-top: 0.5rem; }
    
    .charts-row { display: grid; grid-template-columns: 1fr 2fr; gap: 1.5rem; margin-bottom: 2rem; }
    .chart-card { padding: 1.5rem; display: flex; flex-direction: column; height: 300px; }
    .canvas-container { flex: 1; position: relative; width: 100%; height: 100%; }
    
    .split-lists { display: flex; flex-direction: column; gap: 1.5rem; }
    .list-card { padding: 1.5rem; height: auto; max-height: 400px; display: flex; flex-direction: column; }
    .list-card table { display: block; overflow-y: auto; max-height: 350px; }
    .list-card thead, .list-card tbody tr { display: table; width: 100%; table-layout: fixed; }
    
    .card { background: #252526; border-radius: 8px; border: 1px solid #333; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    h3 { margin: 0 0 1rem 0; font-size: 1rem; color: #ccc; border-bottom: 1px solid #333; padding-bottom: 0.5rem; }
    
    .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; margin-bottom: 1rem; padding-bottom: 0.5rem; }
    .card-header h3 { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
    .btn-refresh { background: #333; color: #ccc; border: 1px solid #555; padding: 4px 8px; font-size: 0.75rem; border-radius: 4px; cursor: pointer; }
    .btn-refresh:hover { background: #444; color: #fff; }

    table { width: 100%; border-collapse: collapse; }
    th { text-align: left; color: #888; font-size: 0.75rem; padding: 0.5rem; border-bottom: 1px solid #333; text-transform: uppercase; letter-spacing: 0.5px; }
    td { padding: 0.5rem; border-bottom: 1px solid #333; color: #ccc; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    tr:hover { background: #2a2d2e; cursor: pointer; }
    
    .path { font-weight: 500; color: #fff; font-family: monospace; }
    .reason { color: #888; text-align: right; }
    .mod-cell { color: #888; }

    /* Matrix Styles Removed */
    .title-cell { color: #ddd; }
    
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
    .badge.score { background: #333; color: #aaa; }
    .badge.score.crit { background: #f14c4c; color: #fff; }
    .badge.score.high { background: #cca700; color: #000; }
    
    .badge.sev.critical { background: rgba(241, 76, 76, 0.2); color: #f14c4c; border: 1px solid rgba(241, 76, 76, 0.3); }
    .badge.sev.high { background: rgba(204, 167, 0, 0.2); color: #cca700; border: 1px solid rgba(204, 167, 0, 0.3); }
    .badge.sev.medium { background: rgba(0, 122, 204, 0.2); color: #007acc; border: 1px solid rgba(0, 122, 204, 0.3); }
    .badge.sev.low, .badge.sev.info { background: #333; color: #ccc; border: 1px solid #444; }
    
    .use-score { background: #333; color: #aaa; padding: 1px 4px; border-radius: 3px; font-size: 0.7rem; font-family: monospace; margin-left: 5px; }

    .badge.cve { background: #e91e63; color: white; }

    .triage-grid { display: flex; justify-content: space-around; align-items: center; width: 100%; margin-bottom: 0.5rem; }
    .t-item { display: flex; flex-direction: column; align-items: center; }
    .t-num { font-weight: bold; font-size: 1.5rem; color: #ccc; }
    .t-num.tp { color: #2e7d32; }
    .t-num.fp { color: #c62828; }
    .t-lbl { font-size: 0.7rem; color: #888; text-transform: uppercase; }

    .actions-cell { text-align: right; white-space: nowrap; }
    .btn-xs { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; border: none; cursor: pointer; color: white; margin-left: 4px; opacity: 0.4; }
    .btn-xs:hover { opacity: 0.8; }
    .btn-xs.selected { opacity: 1; border: 1px solid rgba(255,255,255,0.5); }
    .btn-xs.success { background: #2e7d32; }
    .btn-xs.danger { background: #c62828; }
</style>
