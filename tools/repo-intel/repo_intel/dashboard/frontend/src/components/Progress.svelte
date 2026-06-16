<script>
    import { onMount, onDestroy } from 'svelte';
    
    export let show = false;
    export let scanData = null;
    
    let websocket = null;
    let progress = {
        total_modules: 0,
        completed_modules: 0,
        current_module: '',
        current_step: '',
        findings_count: 0,
        progress_percent: 0,
        elapsed_time: 0,
        status: 'idle',
        error_message: null
    };
    
    let reconnectAttempts = 0;
    let maxReconnectAttempts = 5;
    let reconnectTimeout = null;
    
    $: isActive = show && (progress.status === 'running' || progress.status === 'completed');
    $: isCompleted = progress.status === 'completed';
    $: hasError = progress.status === 'error';
    $: progressWidth = `${progress.progress_percent}%`;
    $: elapsedFormatted = formatTime(progress.elapsed_time);
    
    function formatTime(seconds) {
        if (seconds < 60) return `${seconds.toFixed(1)}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    }
    
    function connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/progress`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = () => {
                console.log('Progress WebSocket connected');
                reconnectAttempts = 0;
            };
            
            websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    progress = { ...progress, ...data };
                    
                    // Auto-hide when completed after 3 seconds
                    if (data.status === 'completed') {
                        setTimeout(() => {
                            if (progress.status === 'completed') {
                                show = false;
                            }
                        }, 3000);
                    }
                } catch (e) {
                    console.error('Error parsing progress data:', e);
                }
            };
            
            websocket.onclose = () => {
                console.log('Progress WebSocket disconnected');
                websocket = null;
                
                // Attempt to reconnect
                if (reconnectAttempts < maxReconnectAttempts && show) {
                    reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
                    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
                    
                    reconnectTimeout = setTimeout(connectWebSocket, delay);
                }
            };
            
            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (e) {
            console.error('Failed to connect WebSocket:', e);
        }
    }
    
    function disconnectWebSocket() {
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }
        
        if (websocket) {
            websocket.close();
            websocket = null;
        }
    }
    
    $: if (show && !websocket) {
        connectWebSocket();
    } else if (!show && websocket) {
        disconnectWebSocket();
    }
    
    onDestroy(() => {
        disconnectWebSocket();
    });
    
    function dismiss() {
        show = false;
    }
    
    function retryConnection() {
        reconnectAttempts = 0;
        connectWebSocket();
    }
</script>

{#if isActive}
    <div class="progress-overlay" class:completed={isCompleted} class:error={hasError}>
        <div class="progress-container">
            <div class="progress-header">
                <div class="progress-title">
                    {#if hasError}
                        <span class="error-icon">⚠️</span>
                        Scan Failed
                    {:else if isCompleted}
                        <span class="success-icon">✅</span>
                        Scan Completed
                    {:else}
                        <span class="scanning-icon">🔍</span>
                        Scanning Repository
                    {/if}
                </div>
                <button class="close-btn" on:click={dismiss}>×</button>
            </div>
            
            <div class="progress-content">
                {#if hasError}
                    <div class="error-message">
                        <p>{progress.error_message || 'An unknown error occurred during scanning.'}</p>
                        <button class="retry-btn" on:click={retryConnection}>Retry Connection</button>
                    </div>
                {:else}
                    <div class="progress-bar-container">
                        <div class="progress-info">
                            <span class="progress-text">{progress.current_step || 'Initializing...'}</span>
                            <span class="progress-percent">{progress.progress_percent.toFixed(1)}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {progressWidth}"></div>
                        </div>
                    </div>
                    
                    <div class="progress-details">
                        <div class="detail-row">
                            <span class="detail-label">Current Module:</span>
                            <span class="detail-value">{progress.current_module || 'None'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Modules:</span>
                            <span class="detail-value">{progress.completed_modules} / {progress.total_modules}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Findings:</span>
                            <span class="detail-value">{progress.findings_count}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Elapsed:</span>
                            <span class="detail-value">{elapsedFormatted}</span>
                        </div>
                    </div>
                    
                    {#if isCompleted}
                        <div class="completion-summary">
                            <p>Found <strong>{progress.findings_count}</strong> findings in <strong>{elapsedFormatted}</strong></p>
                        </div>
                    {/if}
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
    .progress-overlay {
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
        backdrop-filter: blur(4px);
    }
    
    .progress-container {
        background: #252526;
        border-radius: 12px;
        border: 1px solid #444;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow: hidden;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-20px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem;
        background: #2d2d2d;
        border-bottom: 1px solid #444;
    }
    
    .progress-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .scanning-icon {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .success-icon {
        color: #4caf50;
    }
    
    .error-icon {
        color: #f44336;
    }
    
    .close-btn {
        background: none;
        border: none;
        color: #ccc;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0.5rem;
        border-radius: 4px;
        transition: all 0.2s;
    }
    
    .close-btn:hover {
        background: #444;
        color: #fff;
    }
    
    .progress-content {
        padding: 1.5rem;
    }
    
    .progress-bar-container {
        margin-bottom: 1.5rem;
    }
    
    .progress-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .progress-text {
        color: #ddd;
        font-size: 0.9rem;
    }
    
    .progress-percent {
        color: #007acc;
        font-weight: 600;
        font-family: monospace;
    }
    
    .progress-bar {
        height: 8px;
        background: #333;
        border-radius: 4px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #007acc, #005a9e);
        transition: width 0.3s ease;
        border-radius: 4px;
    }
    
    .progress-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    
    .detail-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        background: #1e1e1e;
        border-radius: 4px;
    }
    
    .detail-label {
        color: #888;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .detail-value {
        color: #ccc;
        font-weight: 500;
        font-family: monospace;
        font-size: 0.9rem;
    }
    
    .completion-summary {
        text-align: center;
        padding: 1rem;
        background: #1e1e1e;
        border-radius: 4px;
        border: 1px solid #444;
    }
    
    .completion-summary p {
        margin: 0;
        color: #ddd;
        font-size: 0.9rem;
    }
    
    .error-message {
        text-align: center;
        padding: 1rem;
    }
    
    .error-message p {
        color: #f44336;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    
    .retry-btn {
        background: #007acc;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.2s;
    }
    
    .retry-btn:hover {
        background: #005a9e;
    }
    
    /* Completed state styling */
    .progress-overlay.completed {
        animation: fadeOut 0.5s ease-out 2.5s forwards;
    }
    
    @keyframes fadeOut {
        to {
            opacity: 0;
            pointer-events: none;
        }
    }
    
    .progress-overlay.completed .progress-fill {
        background: linear-gradient(90deg, #4caf50, #388e3c);
    }
    
    .progress-overlay.error .progress-fill {
        background: linear-gradient(90deg, #f44336, #d32f2f);
    }
</style>
