/**
 * Floor Plan Builder - Konva.js Implementation
 * Complete drag-and-drop floor plan designer with undo/redo, zoom, grid, snap-to-grid
 */

// Global state
let stage, layer;
let currentZoom = 1;
let gridEnabled = true;
let snapEnabled = true;
let snapSize = 20;
let undoStack = [];
let redoStack = [];
let maxUndoSteps = 50;
let selectedNode = null;
let transformer = null;
let isDragging = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Initialize default empty stage
    initializeCanvas();
    setupEventListeners();
    setupKeyboardShortcuts();
    
    // LOAD SAVED CANVAS
    if (EXISTING_JSON && EXISTING_JSON !== "") {
        try {
            const loaded = Konva.Node.create(EXISTING_JSON, "floorplan-canvas");
            stage.destroy();
            stage = loaded;
            layer = stage.getLayers()[0];
            
            // Ensure transformer exists
            transformer = layer.findOne('Transformer');
            if (!transformer) {
                transformer = new Konva.Transformer({
                    rotateEnabled: true,
                    borderStroke: '#D4AF37',
                    borderStrokeWidth: 2,
                    anchorFill: '#FF7A1A',
                    anchorStroke: '#0A1A44',
                    anchorSize: 10,
                    rotationSnap: 15,
                    enabledAnchors: ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'top-center', 'bottom-center', 'middle-left', 'middle-right']
                });
                layer.add(transformer);
            }
            
            // Setup events for all nodes
            layer.find('Group').forEach(node => {
                if (node.getType() !== 'Transformer') {
                    setupNodeEvents(node);
                }
            });
            layer.find('Circle').forEach(node => {
                if (node.getType() !== 'Transformer') {
                    setupNodeEvents(node);
                }
            });
            layer.find('Rect').forEach(node => {
                if (node.getType() !== 'Transformer') {
                    setupNodeEvents(node);
                }
            });
            layer.find('Text').forEach(node => {
                if (node.getType() !== 'Transformer') {
                    setupNodeEvents(node);
                }
            });
            
            drawGrid();
            layer.draw();
            saveState();
        } catch (err) {
            console.error("Cannot load JSON:", err);
        }
    }
    
    startAutosave();
});

function initializeCanvas() {
    // Create stage with default size
    stage = new Konva.Stage({
        container: 'floorplan-canvas',
        width: 1200,
        height: 700
    });
    
    layer = new Konva.Layer();
    stage.add(layer);
    
    // Create transformer for resizing/rotating
    transformer = new Konva.Transformer({
        rotateEnabled: true,
        borderStroke: '#D4AF37',
        borderStrokeWidth: 2,
        anchorFill: '#FF7A1A',
        anchorStroke: '#0A1A44',
        anchorSize: 10,
        rotationSnap: 15,
        enabledAnchors: ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'top-center', 'bottom-center', 'middle-left', 'middle-right']
    });
    layer.add(transformer);
    
    // Draw grid
    drawGrid();
    
    // Canvas events
    stage.on('click tap', function(e) {
        if (e.target === stage) {
            transformer.nodes([]);
            selectedNode = null;
            layer.draw();
        }
    });
    
    stage.on('dragend', function(e) {
        saveState();
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        const width = Math.max(1200, window.innerWidth - 300);
        const height = Math.max(700, window.innerHeight - 250);
        stage.width(width);
        stage.height(height);
        drawGrid();
        layer.draw();
    });
}

function setupEventListeners() {
    // Toolbar buttons
    document.querySelectorAll('.tool').forEach(tool => {
        tool.addEventListener('click', function() {
            const type = this.dataset.type;
            const centerX = stage.width() / 2;
            const centerY = stage.height() / 2;
            addElement(type, centerX, centerY);
        });
    });
    
    // Controls
    document.getElementById('btn-undo').addEventListener('click', undo);
    document.getElementById('btn-redo').addEventListener('click', redo);
    document.getElementById('btn-clear').addEventListener('click', clearCanvas);
    document.getElementById('btn-zoom-in').addEventListener('click', () => zoom(1.2));
    document.getElementById('btn-zoom-out').addEventListener('click', () => zoom(0.8));
    document.getElementById('btn-save').addEventListener('click', saveFloorPlan);
    
    // Grid toggle (if exists)
    const gridToggle = document.getElementById('toggle-grid');
    if (gridToggle) {
        gridToggle.addEventListener('change', function() {
            gridEnabled = this.checked;
            drawGrid();
            layer.draw();
        });
    }
    
    // Snap toggle (if exists)
    const snapToggle = document.getElementById('toggle-snap');
    if (snapToggle) {
        snapToggle.addEventListener('change', function() {
            snapEnabled = this.checked;
        });
    }
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
        // Delete: Remove selected
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (selectedNode) {
                e.preventDefault();
                removeSelected();
            }
        }
    });
}

function addElement(type, x, y) {
    let node;
    const snapX = snapEnabled ? Math.round(x / snapSize) * snapSize : x;
    const snapY = snapEnabled ? Math.round(y / snapSize) * snapSize : y;
    
    switch(type) {
        case 'round-table':
            node = createRoundTable(snapX, snapY);
            break;
        case 'rect-table':
            node = createRectangularTable(snapX, snapY);
            break;
        case 'chair':
            node = createChair(snapX, snapY);
            break;
        case 'stage':
            node = createStage(snapX, snapY);
            break;
        case 'tent':
            node = createTent(snapX, snapY);
            break;
        case 'buffet':
            node = createBuffet(snapX, snapY);
            break;
        case 'dj-booth':
            node = createDJBooth(snapX, snapY);
            break;
        case 'text':
            node = createTextLabel(snapX, snapY);
            break;
        default:
            return;
    }
    
    if (node) {
        layer.add(node);
        selectNode(node);
        saveState();
        layer.draw();
    }
}

function createRoundTable(x, y) {
    const group = new Konva.Group({
        x: x,
        y: y,
        draggable: true,
        type: 'round-table'
    });
    
    const circle = new Konva.Circle({
        radius: 60,
        fill: '#0A1A44',
        stroke: '#D4AF37',
        strokeWidth: 3,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.4)',
        shadowOffset: { x: 2, y: 2 }
    });
    
    const text = new Konva.Text({
        text: 'Table',
        fontSize: 14,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: '#D4AF37',
        align: 'center',
        verticalAlign: 'middle',
        width: 120,
        height: 60,
        offsetX: 60,
        offsetY: 30
    });
    
    group.add(circle);
    group.add(text);
    
    setupNodeEvents(group);
    return group;
}

function createRectangularTable(x, y) {
    const group = new Konva.Group({
        x: x,
        y: y,
        draggable: true,
        type: 'rect-table'
    });
    
    const rect = new Konva.Rect({
        width: 120,
        height: 80,
        fill: '#0A1A44',
        stroke: '#D4AF37',
        strokeWidth: 3,
        cornerRadius: 8,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.4)',
        shadowOffset: { x: 2, y: 2 }
    });
    
    const text = new Konva.Text({
        text: 'Table',
        fontSize: 14,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: '#D4AF37',
        align: 'center',
        verticalAlign: 'middle',
        width: 120,
        height: 80,
        offsetX: 60,
        offsetY: 40
    });
    
    group.add(rect);
    group.add(text);
    
    setupNodeEvents(group);
    return group;
}

function createChair(x, y) {
    const circle = new Konva.Circle({
        x: x,
        y: y,
        radius: 15,
        fill: '#D4AF37',
        stroke: '#0A1A44',
        strokeWidth: 2,
        draggable: true,
        type: 'chair',
        shadowBlur: 5,
        shadowColor: 'rgba(0, 0, 0, 0.3)',
        shadowOffset: { x: 1, y: 1 }
    });
    
    setupNodeEvents(circle);
    return circle;
}

function createStage(x, y) {
    const group = new Konva.Group({
        x: x,
        y: y,
        draggable: true,
        type: 'stage'
    });
    
    const rect = new Konva.Rect({
        width: 300,
        height: 100,
        fill: '#0A1A44',
        stroke: '#D4AF37',
        strokeWidth: 4,
        cornerRadius: 6,
        shadowBlur: 15,
        shadowColor: 'rgba(0, 0, 0, 0.5)',
        shadowOffset: { x: 3, y: 3 }
    });
    
    // Stage lines
    const line1 = new Konva.Line({
        points: [0, 30, 300, 30],
        stroke: '#D4AF37',
        strokeWidth: 2,
        listening: false
    });
    const line2 = new Konva.Line({
        points: [0, 50, 300, 50],
        stroke: '#D4AF37',
        strokeWidth: 2,
        listening: false
    });
    const line3 = new Konva.Line({
        points: [0, 70, 300, 70],
        stroke: '#D4AF37',
        strokeWidth: 2,
        listening: false
    });
    
    const text = new Konva.Text({
        text: 'STAGE',
        fontSize: 18,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: '#D4AF37',
        align: 'center',
        verticalAlign: 'middle',
        width: 300,
        height: 100,
        offsetX: 150,
        offsetY: 50
    });
    
    group.add(rect);
    group.add(line1);
    group.add(line2);
    group.add(line3);
    group.add(text);
    
    setupNodeEvents(group);
    return group;
}

function createTent(x, y) {
    const group = new Konva.Group({
        x: x,
        y: y,
        draggable: true,
        type: 'tent'
    });
    
    // Tent base
    const base = new Konva.Rect({
        width: 200,
        height: 150,
        fill: '#FF7A1A',
        stroke: '#D4AF37',
        strokeWidth: 3,
        cornerRadius: 8,
        shadowBlur: 12,
        shadowColor: 'rgba(255, 122, 26, 0.4)',
        shadowOffset: { x: 3, y: 3 }
    });
    
    // Tent top (triangle)
    const top = new Konva.Line({
        points: [100, 0, 0, 50, 200, 50],
        closed: true,
        fill: '#D4AF37',
        stroke: '#0A1A44',
        strokeWidth: 2,
        listening: false
    });
    
    // Tent poles
    const pole1 = new Konva.Line({
        points: [20, 50, 20, 150],
        stroke: '#0A1A44',
        strokeWidth: 3,
        listening: false
    });
    const pole2 = new Konva.Line({
        points: [180, 50, 180, 150],
        stroke: '#0A1A44',
        strokeWidth: 3,
        listening: false
    });
    
    const text = new Konva.Text({
        text: 'TENT',
        fontSize: 16,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: '#0A1A44',
        align: 'center',
        verticalAlign: 'middle',
        width: 200,
        height: 150,
        offsetX: 100,
        offsetY: 100
    });
    
    group.add(base);
    group.add(top);
    group.add(pole1);
    group.add(pole2);
    group.add(text);
    
    setupNodeEvents(group);
    return group;
}

function createBuffet(x, y) {
    const group = new Konva.Group({
        x: x,
        y: y,
        draggable: true,
        type: 'buffet'
    });
    
    const rect = new Konva.Rect({
        width: 150,
        height: 80,
        fill: '#D4AF37',
        stroke: '#0A1A44',
        strokeWidth: 3,
        cornerRadius: 6,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.4)',
        shadowOffset: { x: 2, y: 2 }
    });
    
    const line1 = new Konva.Line({
        points: [0, 30, 150, 30],
        stroke: '#0A1A44',
        strokeWidth: 2,
        listening: false
    });
    const line2 = new Konva.Line({
        points: [0, 50, 150, 50],
        stroke: '#0A1A44',
        strokeWidth: 2,
        listening: false
    });
    
    const text = new Konva.Text({
        text: 'BUFFET',
        fontSize: 14,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: '#0A1A44',
        align: 'center',
        verticalAlign: 'middle',
        width: 150,
        height: 80,
        offsetX: 75,
        offsetY: 40
    });
    
    group.add(rect);
    group.add(line1);
    group.add(line2);
    group.add(text);
    
    setupNodeEvents(group);
    return group;
}

function createDJBooth(x, y) {
    const group = new Konva.Group({
        x: x,
        y: y,
        draggable: true,
        type: 'dj-booth'
    });
    
    const rect = new Konva.Rect({
        width: 120,
        height: 100,
        fill: '#0A1A44',
        stroke: '#FF7A1A',
        strokeWidth: 3,
        cornerRadius: 8,
        shadowBlur: 12,
        shadowColor: 'rgba(255, 122, 26, 0.4)',
        shadowOffset: { x: 3, y: 3 }
    });
    
    // DJ equipment symbols
    const speaker1 = new Konva.Circle({
        x: 30,
        y: 40,
        radius: 12,
        fill: '#FF7A1A',
        stroke: '#D4AF37',
        strokeWidth: 2,
        listening: false
    });
    const speaker2 = new Konva.Circle({
        x: 90,
        y: 40,
        radius: 12,
        fill: '#FF7A1A',
        stroke: '#D4AF37',
        strokeWidth: 2,
        listening: false
    });
    const mixer = new Konva.Rect({
        x: 45,
        y: 60,
        width: 30,
        height: 20,
        fill: '#D4AF37',
        cornerRadius: 2,
        listening: false
    });
    
    const text = new Konva.Text({
        text: 'DJ',
        fontSize: 16,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: '#FF7A1A',
        align: 'center',
        verticalAlign: 'middle',
        width: 120,
        height: 30,
        offsetX: 60,
        offsetY: 15
    });
    
    group.add(rect);
    group.add(speaker1);
    group.add(speaker2);
    group.add(mixer);
    group.add(text);
    
    setupNodeEvents(group);
    return group;
}

function createTextLabel(x, y) {
    const text = new Konva.Text({
        x: x,
        y: y,
        text: 'Label',
        fontSize: 16,
        fontFamily: 'Arial',
        fill: '#0A1A44',
        draggable: true,
        type: 'text',
        padding: 5
    });
    
    // Make text editable
    text.on('dblclick', function() {
        const textNode = this;
        const stage = textNode.getStage();
        const container = stage.container();
        
        const textarea = document.createElement('textarea');
        document.body.appendChild(textarea);
        
        textarea.value = textNode.text();
        textarea.style.position = 'absolute';
        textarea.style.top = (container.offsetTop + textNode.y()) + 'px';
        textarea.style.left = (container.offsetLeft + textNode.x()) + 'px';
        textarea.style.width = textNode.width() + 'px';
        textarea.style.height = textNode.height() + 'px';
        textarea.style.fontSize = textNode.fontSize() + 'px';
        textarea.style.fontFamily = textNode.fontFamily();
        textarea.style.border = '2px solid #D4AF37';
        textarea.style.padding = '5px';
        textarea.style.margin = '0px';
        textarea.style.overflow = 'hidden';
        textarea.style.background = 'white';
        textarea.style.outline = 'none';
        textarea.style.resize = 'none';
        textarea.style.borderRadius = '4px';
        
        textarea.focus();
        textarea.select();
        
        function removeTextarea() {
            textarea.parentNode.removeChild(textarea);
            window.removeEventListener('click', handleOutsideClick);
        }
        
        function setTextareaWidth() {
            textarea.style.width = textNode.width() + 'px';
        }
        
        textarea.addEventListener('keydown', function(e) {
            if (e.keyCode === 13 && !e.shiftKey) {
                textNode.text(textarea.value);
                removeTextarea();
                layer.draw();
                saveState();
            }
            if (e.keyCode === 27) {
                removeTextarea();
            }
        });
        
        function handleOutsideClick(e) {
            if (e.target !== textarea) {
                textNode.text(textarea.value);
                removeTextarea();
                layer.draw();
                saveState();
            }
        }
        
        setTimeout(() => {
            window.addEventListener('click', handleOutsideClick);
        }, 0);
    });
    
    setupNodeEvents(text);
    return text;
}

function setupNodeEvents(node) {
    node.on('dragmove', function() {
        if (snapEnabled) {
            const snapX = Math.round(node.x() / snapSize) * snapSize;
            const snapY = Math.round(node.y() / snapSize) * snapSize;
            node.position({ x: snapX, y: snapY });
        }
        layer.draw();
    });
    
    node.on('dragend', function() {
        saveState();
    });
    
    node.on('click tap', function(e) {
        e.cancelBubble = true;
        selectNode(this);
    });
    
    node.on('transformend', function() {
        saveState();
    });
}

function selectNode(node) {
    selectedNode = node;
    transformer.nodes([node]);
    layer.draw();
}

function removeSelected() {
    if (selectedNode) {
        selectedNode.destroy();
        transformer.nodes([]);
        selectedNode = null;
        layer.draw();
        saveState();
    }
}

function drawGrid() {
    // Remove existing grid
    layer.find('.grid-line').forEach(line => line.destroy());
    
    if (!gridEnabled) return;
    
    const width = stage.width();
    const height = stage.height();
    
    // Vertical lines
    for (let x = 0; x <= width; x += snapSize) {
        const line = new Konva.Line({
            points: [x, 0, x, height],
            stroke: 'rgba(212, 175, 55, 0.2)',
            strokeWidth: 1,
            listening: false,
            name: 'grid-line'
        });
        layer.add(line);
    }
    
    // Horizontal lines
    for (let y = 0; y <= height; y += snapSize) {
        const line = new Konva.Line({
            points: [0, y, width, y],
            stroke: 'rgba(212, 175, 55, 0.2)',
            strokeWidth: 1,
            listening: false,
            name: 'grid-line'
        });
        layer.add(line);
    }
    
    // Move grid to back
    layer.find('.grid-line').forEach(line => {
        line.moveToBottom();
    });
}

function zoom(factor) {
    currentZoom *= factor;
    currentZoom = Math.max(0.1, Math.min(3, currentZoom));
    
    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition() || { x: stage.width() / 2, y: stage.height() / 2 };
    const mousePointTo = {
        x: (pointer.x - stage.x()) / oldScale,
        y: (pointer.y - stage.y()) / oldScale
    };
    
    const newScale = currentZoom;
    const newPos = {
        x: pointer.x - mousePointTo.x * newScale,
        y: pointer.y - mousePointTo.y * newScale
    };
    
    stage.scale({ x: newScale, y: newScale });
    stage.position(newPos);
    stage.batchDraw();
    
    updateZoomDisplay();
}

function updateZoomDisplay() {
    document.getElementById('zoom-level').textContent = Math.round(currentZoom * 100) + '%';
}

function clearCanvas() {
    if (confirm('Are you sure you want to clear the canvas? This cannot be undone.')) {
        layer.find(node => node.getType() !== 'Transformer' && !node.name().includes('grid')).forEach(node => {
            node.destroy();
        });
        transformer.nodes([]);
        selectedNode = null;
        layer.draw();
        saveState();
    }
}

function saveState() {
    const state = JSON.stringify(stage.toJSON());
    undoStack.push(state);
    if (undoStack.length > maxUndoSteps) {
        undoStack.shift();
    }
    redoStack = [];
}

function undo() {
    if (undoStack.length <= 1) return;
    
    const currentState = undoStack.pop();
    redoStack.push(currentState);
    
    if (undoStack.length > 0) {
        const state = JSON.parse(undoStack[undoStack.length - 1]);
        stage.destroy();
        initializeCanvas();
        stage = Konva.Node.create(state, 'floorplan-canvas');
        layer = stage.findOne('Layer');
        transformer = layer.findOne('Transformer');
        if (transformer) {
            transformer.nodes([]);
        }
        selectedNode = null;
        drawGrid();
        layer.draw();
    }
}

function redo() {
    if (redoStack.length === 0) return;
    
    const state = redoStack.pop();
    undoStack.push(state);
    
    stage.destroy();
    initializeCanvas();
    stage = Konva.Node.create(JSON.parse(state), 'floorplan-canvas');
    layer = stage.findOne('Layer');
    transformer = layer.findOne('Transformer');
    if (transformer) {
        transformer.nodes([]);
    }
    selectedNode = null;
    drawGrid();
    layer.draw();
}

function loadInitialData() {
    if (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA && INITIAL_DATA !== null) {
        try {
            console.log('Loading initial data:', INITIAL_DATA);
            
            // Check if INITIAL_DATA is a string (needs parsing)
            let parsedData = INITIAL_DATA;
            if (typeof INITIAL_DATA === 'string') {
                parsedData = JSON.parse(INITIAL_DATA);
            }
            
            let nodesLoaded = 0;
            
            // If parsedData is a full stage JSON (from stage.toJSON())
            if (parsedData.attrs && parsedData.children && Array.isArray(parsedData.children)) {
                console.log('Detected full stage JSON format');
                // Find the Layer in the saved stage
                const layerData = parsedData.children.find(child => 
                    child.className === 'Layer' || child.className === 'Konva.Layer'
                );
                
                if (layerData && layerData.children && Array.isArray(layerData.children)) {
                    console.log('Found layer with', layerData.children.length, 'children');
                    // Load each node from the saved layer (excluding Transformer and grid lines)
                    layerData.children.forEach((nodeData, index) => {
                        const nodeType = nodeData.className || nodeData.nodeType || '';
                        const nodeName = (nodeData.name || '').toString();
                        
                        // Skip Transformer, grid lines, and empty nodes
                        const isTransformer = nodeType === 'Transformer' || nodeType === 'Konva.Transformer';
                        const isGridLine = nodeName.includes('grid') || nodeName.includes('Grid');
                        const isLine = nodeType === 'Line' && isGridLine; // Only skip grid lines, not all lines
                        
                        if (!isTransformer && !isGridLine && !isLine) {
                            try {
                                const node = Konva.Node.create(nodeData);
                                if (node) {
                                    layer.add(node);
                                    setupNodeEvents(node);
                                    nodesLoaded++;
                                    console.log(`Loaded node ${index + 1}:`, nodeType || nodeName || 'unknown');
                                }
                            } catch (e) {
                                console.warn('Could not load node at index', index, ':', nodeData, e);
                            }
                        } else {
                            console.log('Skipped node:', nodeType, nodeName);
                        }
                    });
                } else {
                    console.warn('Layer data not found or invalid');
                }
            } 
            // If parsedData has objects array (alternative format)
            else if (parsedData.objects && Array.isArray(parsedData.objects)) {
                console.log('Detected objects array format');
                parsedData.objects.forEach((objData, index) => {
                    try {
                        const node = Konva.Node.create(objData);
                        if (node) {
                            layer.add(node);
                            setupNodeEvents(node);
                            nodesLoaded++;
                            console.log(`Loaded object ${index + 1}`);
                        }
                    } catch (e) {
                        console.warn('Could not load object at index', index, ':', e);
                    }
                });
            }
            // If parsedData is an array of nodes directly
            else if (Array.isArray(parsedData)) {
                console.log('Detected direct array format');
                parsedData.forEach((objData, index) => {
                    try {
                        const node = Konva.Node.create(objData);
                        if (node) {
                            layer.add(node);
                            setupNodeEvents(node);
                            nodesLoaded++;
                            console.log(`Loaded node ${index + 1}`);
                        }
                    } catch (e) {
                        console.warn('Could not load object at index', index, ':', e);
                    }
                });
            }
            // If parsedData is a single node object
            else if (parsedData.className || parsedData.nodeType) {
                console.log('Detected single node format');
                try {
                    const node = Konva.Node.create(parsedData);
                    if (node) {
                        layer.add(node);
                        setupNodeEvents(node);
                        nodesLoaded++;
                        console.log('Loaded single node');
                    }
                } catch (e) {
                    console.warn('Could not load single node:', e);
                }
            } else {
                console.warn('Unknown data format:', parsedData);
            }
            
            layer.draw();
            saveState();
            console.log(`Initial data loaded successfully. ${nodesLoaded} nodes loaded.`);
        } catch (e) {
            console.error('Error loading initial data:', e);
            console.error('Error stack:', e.stack);
            console.error('Data was:', INITIAL_DATA);
            saveState();
        }
    } else {
        console.log('No initial data to load (INITIAL_DATA is', typeof INITIAL_DATA, ')');
        saveState();
    }
}

function saveFloorPlan() {
    // Use FLOORPLAN_ID if available, otherwise fallback to FLOOR_PLAN_ID
    const planId = (typeof FLOORPLAN_ID !== 'undefined' && FLOORPLAN_ID) 
        ? FLOORPLAN_ID 
        : (typeof FLOOR_PLAN_ID !== 'undefined' && FLOOR_PLAN_ID)
        ? FLOOR_PLAN_ID
        : null;
    
    // If we have a plan ID, use the direct save route
    if (planId) {
        const json = stage.toJSON();
        
        fetch(`/floor-plans/save/${planId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: json })
        })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                console.log("Saved successfully", result);
                // Silent save - no notifications
            } else {
                console.error("Save failed:", result.error);
            }
        })
        .catch(err => {
            console.error("Save failed:", err);
        });
    } else {
        // Create new floor plan (fallback for new floor plans)
        const name = document.getElementById('floor-plan-name').value.trim();
        if (!name) {
            // Silent validation - just return
            return;
        }
        
        const canvasData = stage.toJSON();
        const data = {
            name: name,
            canvas_data: canvasData,
            event_id: (typeof EVENT_ID !== 'undefined' && EVENT_ID) ? EVENT_ID : null
        };
        
        fetch('/floor-plans/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // Silent save - no notifications
                if (result.floor_plan_id) {
                    window.FLOOR_PLAN_ID = result.floor_plan_id;
                    if (typeof FLOOR_PLAN_ID !== 'undefined') {
                        FLOOR_PLAN_ID = result.floor_plan_id;
                    }
                }
            }
            // Silent error handling - no alerts
        })
        .catch(error => {
            console.error('Error saving floor plan:', error);
            // Silent error handling
        });
    }
}

// Autosave every 10 seconds
let autosaveInterval = null;

function startAutosave() {
    if (autosaveInterval) {
        clearInterval(autosaveInterval);
    }
    autosaveInterval = setInterval(function() {
        const name = document.getElementById('floor-plan-name').value.trim();
        if (name) {
            saveFloorPlan();
        }
    }, 10000); // 10 seconds
}

function stopAutosave() {
    if (autosaveInterval) {
        clearInterval(autosaveInterval);
        autosaveInterval = null;
    }
}

window.showAssignModal = function() {
    document.getElementById('assign-modal').style.display = 'flex';
};

window.closeAssignModal = function() {
    document.getElementById('assign-modal').style.display = 'none';
};

function assignFloorPlan() {
    const eventId = document.getElementById('event-select').value;
    if (!eventId) {
        // Silent validation
        return;
    }
    
    const floorPlanId = (typeof FLOOR_PLAN_ID !== 'undefined' && FLOOR_PLAN_ID) 
        ? FLOOR_PLAN_ID 
        : (typeof window.FLOOR_PLAN_ID !== 'undefined' ? window.FLOOR_PLAN_ID : null);
    
    if (!floorPlanId) {
        // Silent validation - save first
        saveFloorPlan();
        setTimeout(() => {
            if (window.FLOOR_PLAN_ID) {
                assignFloorPlan();
            }
        }, 500);
        return;
    }
    
    fetch(`/events/${eventId}/assign-floor-plan`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ floor_plan_id: floorPlanId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Silent assignment - redirect
            closeAssignModal();
            window.location.href = `/events/${eventId}`;
        }
        // Silent error handling
    })
    .catch(error => {
        console.error('Error assigning floor plan:', error);
        // Silent error handling
    });
}

