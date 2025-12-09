// Floor Planner PWA Bundle - Interactive canvas scaffold
// Uses plain canvas as placeholder for full implementation

document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('floor-app');
  if (!el) return;
  
  const canvas = document.createElement('canvas');
  canvas.width = Math.min(window.innerWidth - 40, 1200);
  canvas.height = 600;
  canvas.style.border = "1px solid rgba(255, 255, 255, 0.2)";
  canvas.style.borderRadius = "8px";
  canvas.style.background = "#1a1a1a";
  
  el.innerHTML = "";
  el.appendChild(canvas);
  
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = "#1a1a1a";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  ctx.font = "16px Arial";
  ctx.fillStyle = "#f5f5f5";
  ctx.textAlign = "center";
  ctx.fillText("Floor Planner Canvas (drag & drop UI to be implemented)", canvas.width / 2, canvas.height / 2);
  
  // Touch gesture support
  let isDragging = false;
  let lastX = 0;
  let lastY = 0;
  
  canvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    isDragging = true;
    const touch = e.touches[0];
    lastX = touch.clientX - canvas.offsetLeft;
    lastY = touch.clientY - canvas.offsetTop;
  });
  
  canvas.addEventListener('touchmove', (e) => {
    e.preventDefault();
    if (isDragging) {
      const touch = e.touches[0];
      const x = touch.clientX - canvas.offsetLeft;
      const y = touch.clientY - canvas.offsetTop;
      // Handle pan/zoom logic here
      lastX = x;
      lastY = y;
    }
  });
  
  canvas.addEventListener('touchend', (e) => {
    e.preventDefault();
    isDragging = false;
  });
  
  // Resize handler
  window.addEventListener('resize', () => {
    canvas.width = Math.min(window.innerWidth - 40, 1200);
    canvas.height = 600;
    ctx.fillStyle = "#1a1a1a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#f5f5f5";
    ctx.fillText("Floor Planner Canvas (drag & drop UI to be implemented)", canvas.width / 2, canvas.height / 2);
  });
});

