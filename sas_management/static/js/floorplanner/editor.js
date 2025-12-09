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
        width: 1400,
        height: 900,
        backgroundColor: '#1a1a1a',
        selection: true,
        preserveObjectStacking: true,
        renderOnAddRemove: true,
        selectionColor: 'rgba(242, 104, 34, 0.3)',
        selectionLineWidth: 2,
        selectionBorderColor: '#F26822'
    });

    // Enable object controls with better styling
    fabric.Object.prototype.transparentCorners = false;
    fabric.Object.prototype.cornerColor = '#F26822';
    fabric.Object.prototype.cornerSize = 12;
    fabric.Object.prototype.cornerStyle = 'circle';
    fabric.Object.prototype.borderColor = '#FFBD4A';
    fabric.Object.prototype.borderScaleFactor = 2;

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
    canvas.on('mouse:wheel', onMouseWheel);
    canvas.on('mouse:down', onCanvasMouseDown);
    canvas.on('mouse:move', onCanvasMouseMove);
    canvas.on('mouse:up', onCanvasMouseUp);

    // Grid rendering
    renderGrid();
    
    saveStatusEl = document.getElementById('save-status');
}

// Panning state
let isPanning = false;
let lastPosX = 0;
let lastPosY = 0;

function onCanvasMouseDown(opt) {
    const evt = opt.e;
    if (evt.altKey === true || evt.button === 1) {
        isPanning = true;
        canvas.selection = false;
        lastPosX = evt.clientX;
        lastPosY = evt.clientY;
        canvas.defaultCursor = 'move';
    }
}

function onCanvasMouseMove(opt) {
    if (isPanning) {
        const e = opt.e;
        const vpt = canvas.viewportTransform;
        vpt[4] += e.clientX - lastPosX;
        vpt[5] += e.clientY - lastPosY;
        canvas.requestRenderAll();
        lastPosX = e.clientX;
        lastPosY = e.clientY;
    }
}

function onCanvasMouseUp(opt) {
    canvas.setViewportTransform(canvas.viewportTransform);
    isPanning = false;
    canvas.selection = true;
    canvas.defaultCursor = 'default';
}

function onMouseWheel(opt) {
    const delta = opt.e.deltaY;
    let zoom = canvas.getZoom();
    zoom *= 0.999 ** delta;
    if (zoom > 3) zoom = 3;
    if (zoom < 0.1) zoom = 0.1;
    canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
    currentZoom = zoom;
    updateZoomDisplay();
    renderGrid();
    opt.e.preventDefault();
    opt.e.stopPropagation();
}

function setupEventListeners() {
    // Toolbar buttons
    document.getElementById('btn-undo').addEventListener('click', undo);
    document.getElementById('btn-redo').addEventListener('click', redo);
    document.getElementById('btn-grid').addEventListener('click', toggleGrid);
    document.getElementById('btn-snap').addEventListener('click', toggleSnap);
    document.getElementById('btn-zoom-in').addEventListener('click', () => zoom(1.2));
    document.getElementById('btn-zoom-out').addEventListener('click', () => zoom(0.8));
    document.getElementById('btn-zoom-reset').addEventListener('click', resetZoom);
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
        // Ctrl+C: Copy
        if (e.ctrlKey && e.key === 'c') {
            e.preventDefault();
            copySelected();
        }
        // Ctrl+V: Paste
        if (e.ctrlKey && e.key === 'v') {
            e.preventDefault();
            pasteSelected();
        }
        // Ctrl+D: Duplicate
        if (e.ctrlKey && e.key === 'd') {
            e.preventDefault();
            duplicateSelected();
        }
        // Ctrl+= or Ctrl++: Zoom in
        if (e.ctrlKey && (e.key === '=' || e.key === '+')) {
            e.preventDefault();
            zoom(1.2);
        }
        // Ctrl+-: Zoom out
        if (e.ctrlKey && e.key === '-') {
            e.preventDefault();
            zoom(0.8);
        }
        // Ctrl+0: Reset zoom
        if (e.ctrlKey && e.key === '0') {
            e.preventDefault();
            resetZoom();
        }
        // Delete: Remove selected
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (canvas.getActiveObject()) {
                e.preventDefault();
                removeSelected();
            }
        }
        // Arrow keys: Move selected object
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            const activeObject = canvas.getActiveObject();
            if (activeObject) {
                e.preventDefault();
                const step = e.shiftKey ? 10 : 1;
                let deltaX = 0;
                let deltaY = 0;
                if (e.key === 'ArrowUp') deltaY = -step;
                if (e.key === 'ArrowDown') deltaY = step;
                if (e.key === 'ArrowLeft') deltaX = -step;
                if (e.key === 'ArrowRight') deltaX = step;
                activeObject.set({
                    left: activeObject.left + deltaX,
                    top: activeObject.top + deltaY
                });
                canvas.renderAll();
                saveState();
                updateInspector();
            }
        }
    });
}

// Copy/Paste functionality
let clipboard = null;

function copySelected() {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        activeObject.clone(function(cloned) {
            clipboard = cloned;
        }, ['type', 'metadata']);
    }
}

function pasteSelected() {
    if (clipboard) {
        clipboard.clone(function(clonedObj) {
            canvas.discardActiveObject();
            clonedObj.set({
                left: clonedObj.left + 20,
                top: clonedObj.top + 20,
                evented: true
            });
            if (clonedObj.type === 'activeSelection') {
                clonedObj.canvas = canvas;
                clonedObj.forEachObject(function(obj) {
                    canvas.add(obj);
                });
                clonedObj.setCoords();
            } else {
                canvas.add(clonedObj);
            }
            clipboard.top += 20;
            clipboard.left += 20;
            canvas.setActiveObject(clonedObj);
            canvas.renderAll();
            saveState();
            updateInspector();
        }, ['type', 'metadata']);
    }
}

function duplicateSelected() {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        activeObject.clone(function(cloned) {
            cloned.set({
                left: cloned.left + 20,
                top: cloned.top + 20
            });
            canvas.add(cloned);
            canvas.setActiveObject(cloned);
            canvas.renderAll();
            saveState();
            updateInspector();
        }, ['type', 'metadata']);
    }
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
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const table = new fabric.Circle({
        radius: 60,
        left: centerX,
        top: centerY,
        fill: '#F26822',
        stroke: '#FFBD4A',
        strokeWidth: 3,
        originX: 'center',
        originY: 'center',
        shadow: {
            color: 'rgba(0, 0, 0, 0.3)',
            blur: 10,
            offsetX: 2,
            offsetY: 2
        },
        metadata: { type: 'table', shape: 'round', capacity: 8 }
    });
    
    // Add label text
    const text = new fabric.Text('Table', {
        fontSize: 14,
        fill: '#FFFFFF',
        fontFamily: 'Arial',
        fontWeight: 'bold',
        originX: 'center',
        originY: 'center',
        left: centerX,
        top: centerY,
        selectable: false,
        evented: false
    });
    
    const group = new fabric.Group([table, text], {
        left: centerX,
        top: centerY,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'table', shape: 'round', capacity: 8 }
    });
    
    addObjectWithMetadata(group, 'table-round');
}

function addRectangularTable() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const table = new fabric.Rect({
        width: 120,
        height: 80,
        left: centerX,
        top: centerY,
        fill: '#F26822',
        stroke: '#FFBD4A',
        strokeWidth: 3,
        rx: 8,
        ry: 8,
        originX: 'center',
        originY: 'center',
        shadow: {
            color: 'rgba(0, 0, 0, 0.3)',
            blur: 10,
            offsetX: 2,
            offsetY: 2
        },
        metadata: { type: 'table', shape: 'rect', capacity: 6 }
    });
    
    // Add label text
    const text = new fabric.Text('Table', {
        fontSize: 14,
        fill: '#FFFFFF',
        fontFamily: 'Arial',
        fontWeight: 'bold',
        originX: 'center',
        originY: 'center',
        left: centerX,
        top: centerY,
        selectable: false,
        evented: false
    });
    
    const group = new fabric.Group([table, text], {
        left: centerX,
        top: centerY,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'table', shape: 'rect', capacity: 6 }
    });
    
    addObjectWithMetadata(group, 'table-rect');
}

function addChair() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const chair = new fabric.Circle({
        radius: 15,
        left: centerX,
        top: centerY,
        fill: '#4A90E2',
        stroke: '#2E5C8A',
        strokeWidth: 2,
        originX: 'center',
        originY: 'center',
        shadow: {
            color: 'rgba(0, 0, 0, 0.2)',
            blur: 5,
            offsetX: 1,
            offsetY: 1
        },
        metadata: { type: 'chair' }
    });
    
    addObjectWithMetadata(chair, 'chair');
}

function addBar() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const bar = new fabric.Rect({
        width: 200,
        height: 60,
        left: centerX,
        top: centerY,
        fill: '#8B4513',
        stroke: '#654321',
        strokeWidth: 3,
        rx: 4,
        ry: 4,
        originX: 'center',
        originY: 'center',
        shadow: {
            color: 'rgba(0, 0, 0, 0.4)',
            blur: 15,
            offsetX: 3,
            offsetY: 3
        },
        metadata: { type: 'bar' }
    });
    
    const text = new fabric.Text('BAR', {
        fontSize: 16,
        fill: '#FFFFFF',
        fontFamily: 'Arial',
        fontWeight: 'bold',
        originX: 'center',
        originY: 'center',
        left: centerX,
        top: centerY,
        selectable: false,
        evented: false
    });
    
    const group = new fabric.Group([bar, text], {
        left: centerX,
        top: centerY,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'bar' }
    });
    
    addObjectWithMetadata(group, 'bar');
}

function addStage() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const stage = new fabric.Rect({
        width: 300,
        height: 100,
        left: centerX,
        top: centerY,
        fill: '#2C3E50',
        stroke: '#1A252F',
        strokeWidth: 4,
        rx: 6,
        ry: 6,
        originX: 'center',
        originY: 'center',
        shadow: {
            color: 'rgba(0, 0, 0, 0.5)',
            blur: 20,
            offsetX: 4,
            offsetY: 4
        },
        metadata: { type: 'stage' }
    });
    
    // Add stage lines for visual effect
    const line1 = new fabric.Line([centerX - 140, centerY - 30, centerX + 140, centerY - 30], {
        stroke: '#34495E',
        strokeWidth: 2,
        selectable: false,
        evented: false
    });
    const line2 = new fabric.Line([centerX - 140, centerY, centerX + 140, centerY], {
        stroke: '#34495E',
        strokeWidth: 2,
        selectable: false,
        evented: false
    });
    const line3 = new fabric.Line([centerX - 140, centerY + 30, centerX + 140, centerY + 30], {
        stroke: '#34495E',
        strokeWidth: 2,
        selectable: false,
        evented: false
    });
    
    const text = new fabric.Text('STAGE', {
        fontSize: 18,
        fill: '#FFFFFF',
        fontFamily: 'Arial',
        fontWeight: 'bold',
        originX: 'center',
        originY: 'center',
        left: centerX,
        top: centerY,
        selectable: false,
        evented: false
    });
    
    const group = new fabric.Group([stage, line1, line2, line3, text], {
        left: centerX,
        top: centerY,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'stage' }
    });
    
    addObjectWithMetadata(group, 'stage');
}

function addDancefloor() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const dancefloor = new fabric.Rect({
        width: 200,
        height: 200,
        left: centerX,
        top: centerY,
        fill: '#9B59B6',
        stroke: '#7D3C98',
        strokeWidth: 3,
        rx: 8,
        ry: 8,
        originX: 'center',
        originY: 'center',
        shadow: {
            color: 'rgba(155, 89, 182, 0.4)',
            blur: 15,
            offsetX: 3,
            offsetY: 3
        },
        metadata: { type: 'dancefloor' }
    });
    
    // Add checkered pattern effect
    const pattern = new fabric.Group([], {
        left: centerX,
        top: centerY,
        originX: 'center',
        originY: 'center',
        selectable: false,
        evented: false
    });
    
    for (let i = 0; i < 4; i++) {
        for (let j = 0; j < 4; j++) {
            if ((i + j) % 2 === 0) {
                const square = new fabric.Rect({
                    left: -100 + (i * 50),
                    top: -100 + (j * 50),
                    width: 50,
                    height: 50,
                    fill: 'rgba(255, 255, 255, 0.1)',
                    selectable: false,
                    evented: false
                });
                pattern.addWithUpdate(square);
            }
        }
    }
    
    const text = new fabric.Text('DANCE FLOOR', {
        fontSize: 16,
        fill: '#FFFFFF',
        fontFamily: 'Arial',
        fontWeight: 'bold',
        originX: 'center',
        originY: 'center',
        left: centerX,
        top: centerY,
        selectable: false,
        evented: false
    });
    
    const group = new fabric.Group([dancefloor, pattern, text], {
        left: centerX,
        top: centerY,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'dancefloor' }
    });
    
    addObjectWithMetadata(group, 'dancefloor');
}

function addBuffet() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const buffet = new fabric.Rect({
        width: 150,
        height: 80,
        left: centerX,
        top: centerY,
        fill: '#E67E22',
        stroke: '#D35400',
        strokeWidth: 3,
        rx: 6,
        ry: 6,
        originX: 'center',
        originY: 'center',
        shadow: {
            color: 'rgba(0, 0, 0, 0.3)',
            blur: 12,
            offsetX: 2,
            offsetY: 2
        },
        metadata: { type: 'buffet' }
    });
    
    // Add buffet lines
    const line1 = new fabric.Line([centerX - 70, centerY - 20, centerX + 70, centerY - 20], {
        stroke: '#D35400',
        strokeWidth: 2,
        selectable: false,
        evented: false
    });
    const line2 = new fabric.Line([centerX - 70, centerY + 20, centerX + 70, centerY + 20], {
        stroke: '#D35400',
        strokeWidth: 2,
        selectable: false,
        evented: false
    });
    
    const text = new fabric.Text('BUFFET', {
        fontSize: 14,
        fill: '#FFFFFF',
        fontFamily: 'Arial',
        fontWeight: 'bold',
        originX: 'center',
        originY: 'center',
        left: centerX,
        top: centerY,
        selectable: false,
        evented: false
    });
    
    const group = new fabric.Group([buffet, line1, line2, text], {
        left: centerX,
        top: centerY,
        originX: 'center',
        originY: 'center',
        metadata: { type: 'buffet' }
    });
    
    addObjectWithMetadata(group, 'buffet');
}

function addObjectWithMetadata(obj, type) {
    obj.set('type', type);
    obj.setControlsVisibility({
        mt: true, mb: true, ml: true, mr: true,
        tl: true, tr: true, bl: true, br: true,
        mtr: true
    });
    
    // Ensure object is within canvas bounds initially
    if (obj.left < 0) obj.set('left', 50);
    if (obj.top < 0) obj.set('top', 50);
    if (obj.left > canvas.width) obj.set('left', canvas.width - 100);
    if (obj.top > canvas.height) obj.set('top', canvas.height - 100);
    
    canvas.add(obj);
    canvas.setActiveObject(obj);
    canvas.renderAll();
    renderGrid();
    saveState();
    updateInspector();
}

// ============================================================================
// GRID & SNAP
// ============================================================================

function renderGrid() {
    if (!gridEnabled) {
        canvas.contextTop.clearRect(0, 0, canvas.width, canvas.height);
        return;
    }
    
    const gridSize = 20;
    const width = canvas.width;
    const height = canvas.height;
    const zoom = canvas.getZoom();
    const vpt = canvas.viewportTransform;
    
    canvas.contextTop.clearRect(0, 0, width, height);
    canvas.contextTop.save();
    canvas.contextTop.setTransform(1, 0, 0, 1, 0, 0);
    
    // Calculate visible grid area
    const offsetX = vpt[4] % (gridSize * zoom);
    const offsetY = vpt[5] % (gridSize * zoom);
    
    canvas.contextTop.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    canvas.contextTop.lineWidth = 1;
    
    // Draw vertical lines
    for (let x = -offsetX; x <= width; x += gridSize * zoom) {
        canvas.contextTop.beginPath();
        canvas.contextTop.moveTo(x, 0);
        canvas.contextTop.lineTo(x, height);
        canvas.contextTop.stroke();
    }
    
    // Draw horizontal lines
    for (let y = -offsetY; y <= height; y += gridSize * zoom) {
        canvas.contextTop.beginPath();
        canvas.contextTop.moveTo(0, y);
        canvas.contextTop.lineTo(width, y);
        canvas.contextTop.stroke();
    }
    
    // Draw major grid lines every 5 units
    canvas.contextTop.strokeStyle = 'rgba(242, 104, 34, 0.15)';
    canvas.contextTop.lineWidth = 1.5;
    
    for (let x = -offsetX; x <= width; x += gridSize * zoom * 5) {
        canvas.contextTop.beginPath();
        canvas.contextTop.moveTo(x, 0);
        canvas.contextTop.lineTo(x, height);
        canvas.contextTop.stroke();
    }
    
    for (let y = -offsetY; y <= height; y += gridSize * zoom * 5) {
        canvas.contextTop.beginPath();
        canvas.contextTop.moveTo(0, y);
        canvas.contextTop.lineTo(width, y);
        canvas.contextTop.stroke();
    }
    
    canvas.contextTop.restore();
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
    const center = canvas.getCenter();
    currentZoom *= factor;
    currentZoom = Math.max(0.1, Math.min(3, currentZoom));
    
    canvas.zoomToPoint(center, currentZoom);
    canvas.renderAll();
    updateZoomDisplay();
    renderGrid();
}

function resetZoom() {
    currentZoom = 1;
    canvas.setViewportTransform([1, 0, 0, 1, 0, 0]);
    canvas.setZoom(1);
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
        const obj = e.target;
        if (obj.type === 'group') {
            obj.set({
                left: snapToGrid(obj.left),
                top: snapToGrid(obj.top)
            });
        } else {
            obj.set({
                left: snapToGrid(obj.left),
                top: snapToGrid(obj.top)
            });
        }
    }
    renderGrid();
    saveState();
    updateInspector();
}

function onObjectMoving(e) {
    if (snapEnabled && e.target) {
        const obj = e.target;
        if (obj.type === 'group') {
            obj.set({
                left: snapToGrid(obj.left),
                top: snapToGrid(obj.top)
            });
        } else {
            obj.set({
                left: snapToGrid(obj.left),
                top: snapToGrid(obj.top)
            });
        }
    }
    renderGrid();
}

function onObjectScaling(e) {
    renderGrid();
    updateInspector();
}

function onObjectRotating(e) {
    renderGrid();
    updateInspector();
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
    
    // Get dimensions - handle groups
    let width, height, fill;
    if (activeObject.type === 'group') {
        const bounds = activeObject.getBoundingRect();
        width = Math.round(bounds.width);
        height = Math.round(bounds.height);
        // Try to get fill from first object in group
        const firstObj = activeObject.getObjects()[0];
        fill = firstObj ? (firstObj.fill || '#000000') : '#000000';
    } else {
        width = Math.round(activeObject.width * (activeObject.scaleX || 1));
        height = Math.round(activeObject.height * (activeObject.scaleY || 1));
        fill = activeObject.fill || '#000000';
    }
    
    let html = `
        <div class="inspector-content">
            <div class="inspector-section">
                <label>Type</label>
                <input type="text" value="${type}" readonly class="form-control-sm">
            </div>
            <div class="inspector-section">
                <label>Position (X, Y)</label>
                <div class="inspector-row">
                    <input type="number" id="insp-x" value="${Math.round(activeObject.left)}" class="form-control-sm" placeholder="X">
                    <input type="number" id="insp-y" value="${Math.round(activeObject.top)}" class="form-control-sm" placeholder="Y">
                </div>
            </div>
            <div class="inspector-section">
                <label>Size (W × H)</label>
                <div class="inspector-row">
                    <input type="number" id="insp-width" value="${width}" class="form-control-sm" placeholder="Width">
                    <input type="number" id="insp-height" value="${height}" class="form-control-sm" placeholder="Height">
                </div>
            </div>
            <div class="inspector-section">
                <label>Rotation</label>
                <input type="number" id="insp-rotation" value="${Math.round(activeObject.angle || 0)}" class="form-control-sm" min="0" max="360" step="1">
            </div>
    `;
    
    if (metadata.type === 'table') {
        html += `
            <div class="inspector-section">
                <label>Table Capacity</label>
                <input type="number" id="insp-capacity" value="${metadata.capacity || 8}" class="form-control-sm" min="1">
            </div>
        `;
    }
    
    html += `
            <div class="inspector-section">
                <label>Color</label>
                <input type="color" id="insp-color" value="${rgbToHex(fill)}" class="form-control-sm">
            </div>
            <div class="inspector-section">
                <label>Label</label>
                <input type="text" id="insp-label" value="${metadata.label || ''}" placeholder="Optional label" class="form-control-sm">
            </div>
            <div class="inspector-section" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                <button id="btn-duplicate" class="form-control-sm" style="background: #F26822; color: white; border: none; cursor: pointer; padding: 0.6rem; border-radius: 6px; margin-bottom: 0.5rem;">Duplicate (Ctrl+D)</button>
                <button id="btn-delete" class="form-control-sm" style="background: rgba(255, 107, 107, 0.2); color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.3); cursor: pointer; padding: 0.6rem; border-radius: 6px;">Delete</button>
            </div>
        </div>
    `;
    
    inspector.innerHTML = html;
    
    // Bind input events
    document.getElementById('insp-x').addEventListener('input', function() {
        activeObject.set('left', parseFloat(this.value) || 0);
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-y').addEventListener('input', function() {
        activeObject.set('top', parseFloat(this.value) || 0);
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-width').addEventListener('input', function() {
        const newWidth = parseFloat(this.value) || 1;
        if (activeObject.type === 'group') {
            const scale = newWidth / activeObject.getBoundingRect().width;
            activeObject.scaleX = activeObject.scaleX * scale;
        } else {
            const scale = newWidth / activeObject.width;
            activeObject.set('scaleX', scale);
        }
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-height').addEventListener('input', function() {
        const newHeight = parseFloat(this.value) || 1;
        if (activeObject.type === 'group') {
            const scale = newHeight / activeObject.getBoundingRect().height;
            activeObject.scaleY = activeObject.scaleY * scale;
        } else {
            const scale = newHeight / activeObject.height;
            activeObject.set('scaleY', scale);
        }
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-rotation').addEventListener('input', function() {
        activeObject.set('angle', parseFloat(this.value) || 0);
        canvas.renderAll();
        saveState();
    });
    
    if (document.getElementById('insp-capacity')) {
        document.getElementById('insp-capacity').addEventListener('input', function() {
            if (!activeObject.metadata) activeObject.metadata = {};
            activeObject.metadata.capacity = parseInt(this.value) || 1;
            saveState();
        });
    }
    
    document.getElementById('insp-color').addEventListener('input', function() {
        if (activeObject.type === 'group') {
            const objects = activeObject.getObjects();
            objects.forEach(obj => {
                if (obj.fill) {
                    obj.set('fill', this.value);
                }
            });
            activeObject.setCoords();
        } else {
            activeObject.set('fill', this.value);
        }
        canvas.renderAll();
        saveState();
    });
    
    document.getElementById('insp-label').addEventListener('input', function() {
        if (!activeObject.metadata) activeObject.metadata = {};
        activeObject.metadata.label = this.value;
        saveState();
    });
    
    // Duplicate button
    document.getElementById('btn-duplicate').addEventListener('click', duplicateSelected);
    
    // Delete button
    document.getElementById('btn-delete').addEventListener('click', removeSelected);
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

