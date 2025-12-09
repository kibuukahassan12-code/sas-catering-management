/**
 * Floor Plan Builder - Konva.js Implementation
 * Features: Drag-and-drop, resize, rotate, undo/redo, zoom, grid, snap-to-grid
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
let dragOffset = { x: 0, y: 0 };

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeCanvas();
    setupEventListeners();
    setupKeyboardShortcuts();
    loadInitialData();
});

function initializeCanvas() {
    const container = document.getElementById('stage-container');
    const width = Math.max(1200, container.offsetWidth - 40);
    const height = Math.max(700, window.innerHeight - 400);
    
    stage = new Konva.Stage({
        container: 'stage-container',
        width: width,
        height: height
    });
    
    layer = new Konva.Layer();
    stage.add(layer);
    
    // Create transformer for resizing/rotating
    transformer = new Konva.Transformer({
        rotateEnabled: true,
        borderStroke: '#0A1A44',
        borderStrokeWidth: 2,
        anchorFill: '#D4AF37',
        anchorStroke: '#0A1A44',
        anchorSize: 10,
        rotationSnap: 15
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
    
    stage.on('dragstart', function(e) {
        isDragging = true;
        const node = e.target;
        dragOffset = {
            x: node.x() - stage.getPointerPosition().x,
            y: node.y() - stage.getPointerPosition().y
        };
    });
    
    stage.on('dragend', function(e) {
        isDragging = false;
        saveState();
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        const container = document.getElementById('stage-container');
        const width = Math.max(1200, container.offsetWidth - 40);
        const height = Math.max(700, window.innerHeight - 400);
        stage.width(width);
        stage.height(height);
        drawGrid();
        layer.draw();
    });
}

function setupEventListeners() {
    // Toolbar drag and drop
    document.querySelectorAll('.toolbar-item').forEach(item => {
        item.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text/plain', this.dataset.type);
            this.classList.add('dragging');
        });
        
        item.addEventListener('dragend', function() {
            this.classList.remove('dragging');
        });
    });
    
    // Canvas drop
    const container = document.getElementById('stage-container');
    container.addEventListener('dragover', function(e) {
        e.preventDefault();
    });
    
    container.addEventListener('drop', function(e) {
        e.preventDefault();
        const type = e.dataTransfer.getData('text/plain');
        if (type) {
            const pos = stage.getPointerPosition();
            addElement(type, pos.x, pos.y);
        }
    });
    
    // Controls
    document.getElementById('btn-undo').addEventListener('click', undo);
    document.getElementById('btn-redo').addEventListener('click', redo);
    document.getElementById('btn-clear').addEventListener('click', clearCanvas);
    document.getElementById('btn-zoom-in').addEventListener('click', () => zoom(1.2));
    document.getElementById('btn-zoom-out').addEventListener('click', () => zoom(0.8));
    document.getElementById('btn-reset-zoom').addEventListener('click', resetZoom);
    document.getElementById('toggle-grid').addEventListener('change', function() {
        gridEnabled = this.checked;
        drawGrid();
        layer.draw();
    });
    document.getElementById('toggle-snap').addEventListener('change', function() {
        snapEnabled = this.checked;
    });
    document.getElementById('btn-save').addEventListener('click', saveFloorPlan);
    
    if (document.getElementById('btn-assign')) {
        document.getElementById('btn-assign').addEventListener('click', showAssignModal);
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
        case 'table-round':
            node = createRoundTable(snapX, snapY);
            break;
        case 'table-rect':
            node = createRectangularTable(snapX, snapY);
            break;
        case 'chair':
            node = createChair(snapX, snapY);
            break;
        case 'stage':
            node = createStage(snapX, snapY);
            break;
        case 'buffet':
            node = createBuffet(snapX, snapY);
            break;
        case 'dancefloor':
            node = createDancefloor(snapX, snapY);
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
        type: 'table-round'
    });
    
    const circle = new Konva.Circle({
        radius: 60,
        fill: '#0A1A44',
        stroke: '#D4AF37',
        strokeWidth: 3,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.3)',
        shadowOffset: { x: 2, y: 2 }
    });
    
    const text = new Konva.Text({
        text: 'Table',
        fontSize: 14,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: 'white',
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
        type: 'table-rect'
    });
    
    const rect = new Konva.Rect({
        width: 120,
        height: 80,
        fill: '#0A1A44',
        stroke: '#D4AF37',
        strokeWidth: 3,
        cornerRadius: 8,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.3)',
        shadowOffset: { x: 2, y: 2 }
    });
    
    const text = new Konva.Text({
        text: 'Table',
        fontSize: 14,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: 'white',
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
        shadowColor: 'rgba(0, 0, 0, 0.2)',
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
        shadowColor: 'rgba(0, 0, 0, 0.4)',
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
        fill: 'white',
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
        shadowColor: 'rgba(0, 0, 0, 0.3)',
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

function createDancefloor(x, y) {
    const group = new Konva.Group({
        x: x,
        y: y,
        draggable: true,
        type: 'dancefloor'
    });
    
    const rect = new Konva.Rect({
        width: 200,
        height: 200,
        fill: '#D4AF37',
        stroke: '#0A1A44',
        strokeWidth: 3,
        cornerRadius: 8,
        shadowBlur: 12,
        shadowColor: 'rgba(212, 175, 55, 0.4)',
        shadowOffset: { x: 3, y: 3 }
    });
    
    // Checkered pattern
    for (let i = 0; i < 4; i++) {
        for (let j = 0; j < 4; j++) {
            if ((i + j) % 2 === 0) {
                const square = new Konva.Rect({
                    x: i * 50,
                    y: j * 50,
                    width: 50,
                    height: 50,
                    fill: 'rgba(255, 255, 255, 0.2)',
                    listening: false
                });
                group.add(square);
            }
        }
    }
    
    const text = new Konva.Text({
        text: 'DANCE FLOOR',
        fontSize: 16,
        fontFamily: 'Arial',
        fontStyle: 'bold',
        fill: '#0A1A44',
        align: 'center',
        verticalAlign: 'middle',
        width: 200,
        height: 200,
        offsetX: 100,
        offsetY: 100
    });
    
    group.add(rect);
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
            stroke: '#D9D9D9',
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
            stroke: '#D9D9D9',
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
    const pointer = stage.getPointerPosition();
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

function resetZoom() {
    currentZoom = 1;
    stage.scale({ x: 1, y: 1 });
    stage.position({ x: 0, y: 0 });
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
        stage = Konva.Node.create(state, 'stage-container');
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
    stage = Konva.Node.create(JSON.parse(state), 'stage-container');
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
    if (typeof INITIAL_DATA !== 'undefined' && INITIAL_DATA) {
        try {
            // If INITIAL_DATA is a full stage JSON, load it
            if (INITIAL_DATA.attrs && INITIAL_DATA.children) {
                // Full stage JSON
                const loadedStage = Konva.Node.create(INITIAL_DATA);
                const loadedLayer = loadedStage.findOne('Layer');
                if (loadedLayer) {
                    loadedLayer.find(node => node.getType() !== 'Transformer' && !node.name().includes('grid')).forEach(node => {
                        const newNode = Konva.Node.create(node.toJSON());
                        layer.add(newNode);
                        setupNodeEvents(newNode);
                    });
                }
            } else if (INITIAL_DATA.objects) {
                // Just objects array
                INITIAL_DATA.objects.forEach(objData => {
                    const node = Konva.Node.create(objData);
                    layer.add(node);
                    setupNodeEvents(node);
                });
            }
            layer.draw();
            saveState();
        } catch (e) {
            console.error('Error loading initial data:', e);
            saveState();
        }
    } else {
        saveState();
    }
}

function saveFloorPlan() {
    const name = document.getElementById('floor-plan-name').value.trim();
    if (!name) {
        alert('Please enter a floor plan name');
        return;
    }
    
    const canvasData = stage.toJSON();
    
    const data = {
        name: name,
        canvas_data: canvasData,
        event_id: (typeof EVENT_ID !== 'undefined' && EVENT_ID) ? EVENT_ID : null
    };
    
    const url = '/floor-plans/save';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Floor plan saved successfully!');
            // Update FLOOR_PLAN_ID if we got one back
            if (result.floor_plan_id) {
                window.FLOOR_PLAN_ID = result.floor_plan_id;
            }
            // Show assign button if no event is associated
            const assignBtn = document.getElementById('btn-assign');
            if (assignBtn && (typeof EVENT_ID === 'undefined' || !EVENT_ID)) {
                assignBtn.style.display = 'inline-block';
            }
        } else {
            alert('Error saving floor plan: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving floor plan: ' + error.message);
    });
}

function showAssignModal() {
    document.getElementById('assign-modal').style.display = 'flex';
}

function closeAssignModal() {
    document.getElementById('assign-modal').style.display = 'none';
}

function assignFloorPlan() {
    const eventId = document.getElementById('event-select').value;
    if (!eventId) {
        alert('Please select an event');
        return;
    }
    
    const floorPlanId = (typeof FLOOR_PLAN_ID !== 'undefined' && FLOOR_PLAN_ID) 
        ? FLOOR_PLAN_ID 
        : (typeof window.FLOOR_PLAN_ID !== 'undefined' ? window.FLOOR_PLAN_ID : null);
    
    if (!floorPlanId) {
        alert('Please save the floor plan first');
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
            alert(data.message);
            closeAssignModal();
            window.location.href = `/events/${eventId}`;
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error assigning floor plan: ' + error.message);
    });
}

// Export PNG functionality
window.exportPNG = function() {
    const dataURL = stage.toDataURL({ 
        pixelRatio: 2,
        mimeType: 'image/png',
        quality: 1
    });
    
    const link = document.createElement('a');
    link.download = (document.getElementById('floor-plan-name').value.trim() || 'floor-plan') + '.png';
    link.href = dataURL;
    link.click();
};

