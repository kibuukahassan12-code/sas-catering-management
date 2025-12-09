/**
 * Floor Planner Editor - Complete Fabric.js Implementation
 * Features: Full CRUD, Undo/Redo, Autosave, Export, Snap, Grid, Zoom
 */

// Global state
let canvas;
let currentZoom = 1;
let gridEnabled = true;
let snapEnabled = true;
let snapSize = 20;
let undoStack = [];
let redoStack = [];
let maxUndoSteps = 50;
let autoSaveInterval;
let isDirty = false;
let saveStatusEl;
let selectedObject = null;

// Initialize editor
document.addEventListener('DOMContentLoaded', function() {
    initializeCanvas();
    setupEventListeners();
    setupKeyboardShortcuts();
    loadInitialLayout();
    startAutosave();
});

function initializeCanvas() {
    canvas = new fabric.Canvas('fp-canvas', {
        width: 1200,
        height: 700,
        backgroundColor: '#1a1a1a',
        selection: true,
        preserveObjectStacking: true,
        renderOnAddRemove: true
    });

    // Enable object controls
    canvas.on('object:added', onObjectAdded);
    canvas.on('object:removed', onObjectRemoved);
    canvas.on('object:modified', onObjectModified);
    canvas.on('object:moving', onObjectMoving);
    canvas.on('object:scaling', onObjectScaling);
    canvas.on('object:rotating', onObjectRotating);
    canvas.on('selection:created', onSelectionCreated);
    canvas.on('selection:updated', onSelectionUpdated);
    canvas.on('selection:cleared', onSelectionCleared);
    canvas.on('path:created', onObjectAdded);

    // Grid rendering
    renderGrid();
    
    saveStatusEl = document.getElementById('save-status');
}

function setupEventListeners() {
    // Toolbar buttons
    document.getElementById('btn-undo').addEventListener('click', undo);
    document.getElementById('btn-redo').addEventListener('click', redo);
    document.getElementById('btn-grid').addEventListener('click', toggleGrid);
    document.getElementById('btn-snap').addEventListener('click', toggleSnap);
    document.getElementById('btn-zoom-in').addEventListener('click', () => zoom(1.2));
    document.getElementById('btn-zoom-out').addEventListener('click', () => zoom(0.8));
    document.getElementById('btn-export').addEventListener('click', showExportMenu);

    // Add furniture buttons
    document.getElementById('btn-add-table-round').addEventListener('click', () => addRoundTable());
    document.getElementById('btn-add-table-rect').addEventListener('click', () => addRectangularTable());
    document.getElementById('btn-add-chair').addEventListener('click', () => addChair());
    document.getElementById('btn-add-bar').addEventListener('click', () => addBar());
    document.getElementById('btn-add-stage').addEventListener('click', () => addStage());
    document.getElementById('btn-add-dancefloor').addEventListener('click', () => addDancefloor());
    document.getElementById('btn-add-buffet').addEventListener('click', () => addBuffet());

    // Furniture library items
    document.querySelectorAll('.furniture-item').forEach(item => {
        item.addEventListener('click', function() {
            const type = this.dataset.type;
            switch(type) {
                case 'table-round': addRoundTable(); break;
                case 'table-rect': addRectangularTable(); break;
                case 'chair': addChair(); break;
                case 'bar': addBar(); break;
                case 'stage': addStage(); break;
                case 'dancefloor': addDancefloor(); break;
                case 'buffet': addBuffet(); break;
            }
        });
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+Z: Undo
        if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
            e.preventDefault();
            undo();
        }
        // Ctrl+Y or Ctrl+Shift+Z: Redo
        if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'Z')) {
            e.preventDefault();
            redo();
        }
        // Ctrl+S: Save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            saveFloorPlan();
        }
        // Delete: Remove selected
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (canvas.getActiveObject()) {
                e.preventDefault();
                removeSelected();
            }
        }
    });
}

function loadInitialLayout() {
    if (typeof INITIAL_LAYOUT !== 'undefined' && INITIAL_LAYOUT && typeof INITIAL_LAYOUT === 'object') {
        // Load layout even if objects array is empty (new floor plan)
        canvas.loadFromJSON(INITIAL_LAYOUT, function() {
            canvas.renderAll();
            if (INITIAL_LAYOUT.meta) {
                currentZoom = INITIAL_LAYOUT.meta.zoom || 1;
                gridEnabled = INITIAL_LAYOUT.meta.grid !== false;
                snapEnabled = INITIAL_LAYOUT.meta.snap !== false;
                updateZoomDisplay();
                updateGridToggle();
                updateSnapToggle();
            }
            saveState();
        });
    } else {
        // Initialize with empty layout
        const emptyLayout = {
            objects: [],
            meta: {
                zoom: 1,
                pan: { x: 0, y: 0 },
                grid: true,
                snap: true
            }
        };
        canvas.loadFromJSON(emptyLayout, function() {
            canvas.renderAll();
            saveState();
        });
    }
}

// ============================================================================
// UNDO/REDO
// ============================================================================

function saveState() {
    const state = JSON.stringify(canvas.toJSON(['type', 'metadata']));
    undoStack.push(state);
    if (undoStack.length > maxUndoSteps) {
        undoStack.shift();
    }
    redoStack = [];
    isDirty = true;
}

function undo() {
    if (undoStack.length <= 1) return;
    
    const currentState = undoStack.pop();
    redoStack.push(currentState);
    
    if (undoStack.length > 0) {
        canvas.loadFromJSON(JSON.parse(undoStack[undoStack.length - 1]), function() {
            canvas.renderAll();
            updateInspector();
        });
    }
}

function redo() {
    if (redoStack.length === 0) return;
    
    const state = redoStack.pop();
    undoStack.push(state);
    
    canvas.loadFromJSON(JSON.parse(state), function() {
        canvas.renderAll();
        updateInspector();
    });
}

// ============================================================================
// FURNITURE ELEMENTS
// ============================================================================

function addRoundTable() {
    const table = new fabric.Circle({
        radius: 60,
        left: 200,
        top: 200,
        fill: '#F26822',
        stroke: '#FFBD4A',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'table', shape: 'round', capacity: 8 }
    });
    addObjectWithMetadata(table, 'table-round');
}

function addRectangularTable() {
    const table = new fabric.Rect({
        width: 120,
        height: 80,
        left: 200,
        top: 200,
        fill: '#F26822',
        stroke: '#FFBD4A',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'table', shape: 'rect', capacity: 6 }
    });
    addObjectWithMetadata(table, 'table-rect');
}

function addChair() {
    const chair = new fabric.Rect({
        width: 30,
        height: 30,
        left: 200,
        top: 200,
        fill: '#4A90E2',
        stroke: '#2E5C8A',
        strokeWidth: 1,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'chair' }
    });
    addObjectWithMetadata(chair, 'chair');
}

function addBar() {
    const bar = new fabric.Rect({
        width: 200,
        height: 60,
        left: 200,
        top: 200,
        fill: '#8B4513',
        stroke: '#654321',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'bar' }
    });
    addObjectWithMetadata(bar, 'bar');
}

function addStage() {
    const stage = new fabric.Rect({
        width: 300,
        height: 100,
        left: 200,
        top: 200,
        fill: '#2C3E50',
        stroke: '#1A252F',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'stage' }
    });
    addObjectWithMetadata(stage, 'stage');
}

function addDancefloor() {
    const dancefloor = new fabric.Rect({
        width: 200,
        height: 200,
        left: 200,
        top: 200,
        fill: '#9B59B6',
        stroke: '#7D3C98',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'dancefloor' }
    });
    addObjectWithMetadata(dancefloor, 'dancefloor');
}

function addBuffet() {
    const buffet = new fabric.Rect({
        width: 150,
        height: 80,
        left: 200,
        top: 200,
        fill: '#E67E22',
        stroke: '#D35400',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'buffet' }
    });
    addObjectWithMetadata(buffet, 'buffet');
}

function addObjectWithMetadata(obj, type) {
    obj.set('type', type);
    obj.setControlsVisibility({
        mt: true, mb: true, ml: true, mr: true,
        tl: true, tr: true, bl: true, br: true,
        mtr: true
    });
    canvas.add(obj);
    canvas.setActiveObject(obj);
    canvas.renderAll();
    saveState();
    updateInspector();
}

// ============================================================================
// GRID & SNAP
// ============================================================================

function renderGrid() {
    if (!gridEnabled) return;
    
    const gridSize = 20;
    const width = canvas.width;
    const height = canvas.height;
    
    canvas.contextTop.clearRect(0, 0, width, height);
    canvas.contextTop.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    canvas.contextTop.lineWidth = 1;
    
    for (let x = 0; x <= width; x += gridSize) {
        canvas.contextTop.beginPath();
        canvas.contextTop.moveTo(x, 0);
        canvas.contextTop.lineTo(x, height);
        canvas.contextTop.stroke();
    }
    
    for (let y = 0; y <= height; y += gridSize) {
        canvas.contextTop.beginPath();
        canvas.contextTop.moveTo(0, y);
        canvas.contextTop.lineTo(width, y);
        canvas.contextTop.stroke();
    }
}

function toggleGrid() {
    gridEnabled = !gridEnabled;
    updateGridToggle();
    renderGrid();
}

function updateGridToggle() {
    const btn = document.getElementById('btn-grid');
    if (gridEnabled) {
        btn.classList.add('active');
    } else {
        btn.classList.remove('active');
    }
}

function toggleSnap() {
    snapEnabled = !snapEnabled;
    updateSnapToggle();
}

function updateSnapToggle() {
    const btn = document.getElementById('btn-snap');
    if (snapEnabled) {
        btn.classList.add('active');
    } else {
        btn.classList.remove('active');
    }
}

function snapToGrid(value) {
    if (!snapEnabled) return value;
    return Math.round(value / snapSize) * snapSize;
}

// ============================================================================
// ZOOM
// ============================================================================

function zoom(factor) {
    currentZoom *= factor;
    currentZoom = Math.max(0.1, Math.min(3, currentZoom));
    
    const objects = canvas.getObjects();
    canvas.setZoom(currentZoom);
    canvas.renderAll();
    updateZoomDisplay();
    renderGrid();
}

function updateZoomDisplay() {
    document.getElementById('zoom-level').textContent = Math.round(currentZoom * 100) + '%';
}

// ============================================================================
// OBJECT EVENTS
// ============================================================================

function onObjectAdded(e) {
    saveState();
    if (e.target) {
        updateInspector();
    }
}

function onObjectRemoved(e) {
    saveState();
    updateInspector();
}

function onObjectModified(e) {
    if (snapEnabled && e.target) {
        e.target.set({
            left: snapToGrid(e.target.left),
            top: snapToGrid(e.target.top)
        });
    }
    saveState();
    updateInspector();
}

function onObjectMoving(e) {
    if (snapEnabled && e.target) {
        e.target.set({
            left: snapToGrid(e.target.left),
            top: snapToGrid(e.target.top)
        });
    }
    renderGrid();
}

function onObjectScaling(e) {
    renderGrid();
}

function onObjectRotating(e) {
    renderGrid();
}

function onSelectionCreated(e) {
    selectedObject = e.selected[0];
    updateInspector();
}

function onSelectionUpdated(e) {
    selectedObject = e.selected[0];
    updateInspector();
}

function onSelectionCleared() {
    selectedObject = null;
    updateInspector();
}

function removeSelected() {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        if (activeObject.type === 'activeSelection') {
            activeObject.getObjects().forEach(obj => canvas.remove(obj));
        } else {
            canvas.remove(activeObject);
        }
        canvas.discardActiveObject();
        canvas.renderAll();
        saveState();
        updateInspector();
    }
}

// ============================================================================
// OBJECT INSPECTOR
// ============================================================================

function updateInspector() {
    const inspector = document.getElementById('object-inspector');
    const activeObject = canvas.getActiveObject();
    
    if (!activeObject || activeObject.type === 'activeSelection') {
        inspector.innerHTML = '<div class="inspector-placeholder"><p>Select an object to edit</p></div>';
        return;
    }
    
    const metadata = activeObject.metadata || {};
    const type = activeObject.type || 'unknown';
    
    let html = `
        <div class="inspector-content">
            <div class="inspector-section">
                <label>Type</label>
                <input type="text" value="${type}" readonly class="form-control-sm">
            </div>
            <div class="inspector-section">
                <label>Position</label>
                <div class="inspector-row">
                    <input type="number" id="insp-x" value="${Math.round(activeObject.left)}" class="form-control-sm">
                    <input type="number" id="insp-y" value="${Math.round(activeObject.top)}" class="form-control-sm">
                </div>
            </div>
            <div class="inspector-section">
                <label>Size</label>
                <div class="inspector-row">
                    <input type="number" id="insp-width" value="${Math.round(activeObject.width * activeObject.scaleX)}" class="form-control-sm">
                    <input type="number" id="insp-height" value="${Math.round(activeObject.height * activeObject.scaleY)}" class="form-control-sm">
                </div>
            </div>
            <div class="inspector-section">
                <label>Rotation</label>
                <input type="number" id="insp-rotation" value="${Math.round(activeObject.angle)}" class="form-control-sm">
            </div>
    `;
    
    if (metadata.type === 'table') {
        html += `
            <div class="inspector-section">
                <label>Table Capacity</label>
                <input type="number" id="insp-capacity" value="${metadata.capacity || 8}" class="form-control-sm">
            </div>
        `;
    }
    
    html += `
            <div class="inspector-section">
                <label>Color</label>
                <input type="color" id="insp-color" value="${rgbToHex(activeObject.fill)}" class="form-control-sm">
            </div>
            <div class="inspector-section">
                <label>Label</label>
                <input type="text" id="insp-label" value="${metadata.label || ''}" placeholder="Optional label" class="form-control-sm">
            </div>
        </div>
    `;
    
    inspector.innerHTML = html;
    
    // Bind input events
    document.getElementById('insp-x').addEventListener('input', function() {
        activeObject.set('left', parseFloat(this.value));
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-y').addEventListener('input', function() {
        activeObject.set('top', parseFloat(this.value));
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-width').addEventListener('input', function() {
        const scale = parseFloat(this.value) / activeObject.width;
        activeObject.set('scaleX', scale);
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-height').addEventListener('input', function() {
        const scale = parseFloat(this.value) / activeObject.height;
        activeObject.set('scaleY', scale);
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-rotation').addEventListener('input', function() {
        activeObject.set('angle', parseFloat(this.value));
        canvas.renderAll();
        saveState();
    });
    
    if (document.getElementById('insp-capacity')) {
        document.getElementById('insp-capacity').addEventListener('input', function() {
            if (!activeObject.metadata) activeObject.metadata = {};
            activeObject.metadata.capacity = parseInt(this.value);
            saveState();
        });
    }
    
    document.getElementById('insp-color').addEventListener('input', function() {
        activeObject.set('fill', this.value);
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-label').addEventListener('input', function() {
        if (!activeObject.metadata) activeObject.metadata = {};
        activeObject.metadata.label = this.value;
        saveState();
    });
}

function rgbToHex(rgb) {
    if (typeof rgb === 'string' && rgb.startsWith('#')) return rgb;
    if (typeof rgb === 'string') {
        const match = rgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (match) {
            return '#' + [1, 2, 3].map(i => ('0' + parseInt(match[i]).toString(16)).slice(-2)).join('');
        }
    }
    return '#000000';
}

// ============================================================================
// AUTOSAVE
// ============================================================================

function startAutosave() {
    autoSaveInterval = setInterval(function() {
        if (isDirty) {
            saveFloorPlan(true);
        }
    }, 5000); // Autosave every 5 seconds
}

function saveFloorPlan(isAutosave = false) {
    if (typeof FLOORPLAN_ID === 'undefined' || !FLOORPLAN_ID) {
        console.warn('Cannot save: Floor plan ID not available');
        return;
    }
    
    if (isAutosave) {
        saveStatusEl.textContent = 'Autosaving...';
        saveStatusEl.className = 'save-status saving';
    } else {
        saveStatusEl.textContent = 'Saving...';
        saveStatusEl.className = 'save-status saving';
    }
    
    const layout = canvas.toJSON(['type', 'metadata']);
    layout.meta = {
        zoom: currentZoom,
        pan: { x: 0, y: 0 },
        grid: gridEnabled,
        snap: snapEnabled
    };
    
    // Save layout
    fetch(`/floorplanner/${FLOORPLAN_ID}/save`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ layout: layout })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Generate and save thumbnail
            const thumbnail = canvas.toDataURL('image/png');
            return fetch(`/floorplanner/${FLOORPLAN_ID}/save-thumbnail`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ thumbnail: thumbnail })
            });
        } else {
            throw new Error(data.error || 'Save failed');
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            saveStatusEl.textContent = 'Saved ✓';
            saveStatusEl.className = 'save-status saved';
            isDirty = false;
            
            setTimeout(() => {
                if (!isDirty) {
                    saveStatusEl.textContent = 'Ready';
                    saveStatusEl.className = 'save-status';
                }
            }, 2000);
        } else {
            throw new Error(data.error || 'Thumbnail save failed');
        }
    })
    .catch(error => {
        console.error('Save error:', error);
        saveStatusEl.textContent = 'Error saving';
        saveStatusEl.className = 'save-status error';
    });
}

// ============================================================================
// EXPORT
// ============================================================================

function showExportMenu() {
    const menu = document.createElement('div');
    menu.className = 'export-menu';
    menu.innerHTML = `
        <a href="/floorplanner/${FLOORPLAN_ID}/export/png" target="_blank" class="export-option">Export as PNG</a>
        <a href="/floorplanner/${FLOORPLAN_ID}/export/pdf" target="_blank" class="export-option">Export as PDF</a>
    `;
    
    // Remove existing menu if any
    const existing = document.querySelector('.export-menu');
    if (existing) existing.remove();
    
    document.body.appendChild(menu);
    
    // Position menu
    const btn = document.getElementById('btn-export');
    const rect = btn.getBoundingClientRect();
    menu.style.top = (rect.bottom + 5) + 'px';
    menu.style.right = (window.innerWidth - rect.right) + 'px';
    
    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target) && e.target !== btn) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 10);
}

