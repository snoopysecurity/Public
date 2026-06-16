"""Local server for Code Intel Miner dashboard."""

import os
import json
import asyncio
import uvicorn
from git import Repo
from repo_intel.core.utils import calculate_finding_id
from repo_intel.modules import get_module_categories
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

app = FastAPI()
FINDINGS_DIR = None
DASHBOARD_DIST = os.path.join(os.path.dirname(__file__), "dashboard", "dist")

# WebSocket connections for real-time updates
active_connections: list[WebSocket] = []
scan_progress = None

# Mount assets if available
if os.path.exists(os.path.join(DASHBOARD_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DASHBOARD_DIST, "assets")), name="assets")

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time scan progress updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send current progress if available
        if scan_progress:
            await websocket.send_text(json.dumps(scan_progress))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_progress(progress_data):
    """Broadcast progress updates to all connected WebSocket clients."""
    if active_connections:
        message = json.dumps(progress_data)
        disconnected = []
        
        for connection in active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in active_connections:
                active_connections.remove(conn)


def update_scan_progress(progress_data):
    """Update global scan progress and broadcast to clients."""
    global scan_progress
    scan_progress = progress_data
    
    # Schedule broadcast in event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast_progress(progress_data))
    except:
        # Fallback for synchronous contexts
        pass


@app.get("/api/scan/status")
async def get_scan_status():
    """Get current scan status."""
    if scan_progress:
        return scan_progress
    return {"status": "idle"}


@app.post("/api/scan/start")
async def start_scan(request: Request):
    """Start a new scan with progress tracking."""
    # This would integrate with the CLI/engine for actual scanning
    # For now, return a placeholder response
    return {"status": "not_implemented", "message": "Scan initiation via API not yet implemented"}


@app.get("/api/searches")
async def get_saved_searches():
    """Get saved searches and filters."""
    searches_path = os.path.join(FINDINGS_DIR, "saved_searches.json") if FINDINGS_DIR else None
    
    if not searches_path or not os.path.exists(searches_path):
        return {"searches": [], "filters": {}}
    
    try:
        with open(searches_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"searches": [], "filters": {}}


@app.post("/api/searches")
async def save_search(request: Request):
    """Save a search or filter."""
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    try:
        data = await request.json()
        searches_path = os.path.join(FINDINGS_DIR, "saved_searches.json")
        
        # Load existing searches
        saved_data = {"searches": [], "filters": {}}
        if os.path.exists(searches_path):
            with open(searches_path, "r") as f:
                saved_data = json.load(f)
        
        # Add new search or filter
        if data.get("type") == "search":
            if "searches" not in saved_data:
                saved_data["searches"] = []
            # Check for duplicates
            existing_names = [s["name"] for s in saved_data["searches"]]
            if data["name"] not in existing_names:
                saved_data["searches"].append({
                    "name": data["name"],
                    "query": data["query"],
                    "created_at": data.get("created_at", ""),
                    "description": data.get("description", "")
                })
        elif data.get("type") == "filter":
            if "filters" not in saved_data:
                saved_data["filters"] = {}
            saved_data["filters"][data["name"]] = data["filter"]
        
        # Save updated data
        with open(searches_path, "w") as f:
            json.dump(saved_data, f, indent=2)
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/searches/{search_name}")
async def delete_search(search_name: str):
    """Delete a saved search."""
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    try:
        searches_path = os.path.join(FINDINGS_DIR, "saved_searches.json")
        
        if not os.path.exists(searches_path):
            raise HTTPException(status_code=404, detail="No saved searches found")
        
        with open(searches_path, "r") as f:
            saved_data = json.load(f)
        
        # Remove search if exists
        if "searches" in saved_data:
            saved_data["searches"] = [s for s in saved_data["searches"] if s["name"] != search_name]
        
        # Remove filter if exists
        if "filters" in saved_data and search_name in saved_data["filters"]:
            del saved_data["filters"][search_name]
        
        # Save updated data
        with open(searches_path, "w") as f:
            json.dump(saved_data, f, indent=2)
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def get_dashboard():
    # Prefer Svelte App
    if os.path.exists(os.path.join(DASHBOARD_DIST, "index.html")):
        return FileResponse(os.path.join(DASHBOARD_DIST, "index.html"))
        
    # Fallback to legacy generated dashboard
    if FINDINGS_DIR and os.path.exists(os.path.join(FINDINGS_DIR, "dashboard.html")):
        return FileResponse(os.path.join(FINDINGS_DIR, "dashboard.html"))
        
    raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/api/modules")
async def get_modules():
    """Return module categories for navigation."""
    return get_module_categories()

@app.get("/api/context")
async def get_context():
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    context_path = os.path.join(FINDINGS_DIR, "context.json")
    triage_path = os.path.join(FINDINGS_DIR, "triage.json")
    
    if not os.path.exists(context_path):
        raise HTTPException(status_code=404, detail="context.json not found")

    with open(context_path, "r") as f:
        context = json.load(f)
        
    # Load triage data
    triage_data = {}
    if os.path.exists(triage_path):
        try:
            with open(triage_path, "r") as f:
                triage_data = json.load(f)
        except Exception:
            print("[!] Failed to load triage.json")

    # Inject IDs and triage status
    if "findings" in context:
        for finding in context["findings"]:
            finding_id = finding.get("id") or calculate_finding_id(finding)
            finding["id"] = finding_id
            finding["triage_status"] = triage_data.get(finding_id, "UNTRIAGED")
            
            # Zero out research value for False Positives
            if finding["triage_status"] == 'FP':
                finding["research_value"] = 0.0
                finding["confidence_score"] = 0.0
                finding["priority_score"] = 0
            
    return context

@app.post("/api/triage")
async def update_triage(request: Request):
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    try:
        data = await request.json()
        finding_id = data.get("id")
        status = data.get("status")
        
        if not finding_id or not status:
            raise HTTPException(status_code=400, detail="Missing id or status")
            
        triage_path = os.path.join(FINDINGS_DIR, "triage.json")
        triage_data = {}
        
        if os.path.exists(triage_path):
            try:
                with open(triage_path, "r") as f:
                    triage_data = json.load(f)
            except Exception:
                pass
        
        triage_data[finding_id] = status
        
        with open(triage_path, "w") as f:
            json.dump(triage_data, f, indent=2)
            
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/source/{file_path:path}")
async def get_source(file_path: str):
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    # Security check: prevent directory traversal
    safe_path = os.path.normpath(os.path.join(FINDINGS_DIR, "source", file_path))
    source_root = os.path.abspath(os.path.join(FINDINGS_DIR, "source"))
    
    if not safe_path.startswith(source_root) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    if os.path.isdir(safe_path):
        raise HTTPException(status_code=400, detail="Path is a directory")
        
    return FileResponse(safe_path)

@app.get("/api/diff/{commit_hash}")
async def get_diff(commit_hash: str):
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    source_dir = os.path.join(FINDINGS_DIR, "source")
    if not os.path.exists(source_dir):
        raise HTTPException(status_code=404, detail="Source repository not found")
        
    try:
        repo = Repo(source_dir)
        # Use git show to get the diff/patch
        diff_text = repo.git.show(commit_hash)
        return PlainTextResponse(diff_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/commit_files/{commit_hash}")
async def get_commit_files(commit_hash: str):
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    source_dir = os.path.join(FINDINGS_DIR, "source")
    try:
        repo = Repo(source_dir)
        # git show --name-only --pretty="" <commit>
        # Note: --pretty="" suppresses the commit message, leaving only filenames
        files_text = repo.git.show(commit_hash, name_only=True, pretty="format:")
        files = [f.strip() for f in files_text.splitlines() if f.strip()]
        return JSONResponse(files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/file_at_commit")
async def get_file_at_commit(commit: str, path: str):
    if not FINDINGS_DIR:
        raise HTTPException(status_code=500, detail="Findings directory not configured")
    
    source_dir = os.path.join(FINDINGS_DIR, "source")
    try:
        repo = Repo(source_dir)
        # git show commit:path
        content = repo.git.show(f"{commit}:{path}")
        return PlainTextResponse(content)
    except Exception as e:
        # File might not exist in that commit (added/deleted)
        raise HTTPException(status_code=404, detail="File content not found at commit")

def start_server(output_dir, port=8000):
    global FINDINGS_DIR
    FINDINGS_DIR = os.path.abspath(output_dir)
    
    # Check for legacy dashboard or dist presence (optional warning)
    dash_path = os.path.join(FINDINGS_DIR, "dashboard.html")
    dist_path = os.path.join(DASHBOARD_DIST, "index.html")
    
    if not os.path.exists(dash_path) and not os.path.exists(dist_path):
         print(f"[!] Warning: Neither dashboard.html nor Svelte app found.")

    print(f"[*] Starting local server at http://localhost:{port}")
    print(f"[*] Serving findings from {FINDINGS_DIR}")
    uvicorn.run(app, host="127.0.0.1", port=port)
