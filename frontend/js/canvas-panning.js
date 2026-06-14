const canvasWrap = document.getElementById("canvas-wrap");

const canvas = document.getElementById("canvas");
const reference = document.getElementById("canvas-reference");
const nodesLayer = document.getElementById("nodes-layer");

// let tmp = document.getElementById("tmp");
// let tmp2 = document.getElementById("tmp2");

let limits = {
  left: 0,
  top: 0,
  right: nodesLayer.scrollWidth,
  bottom: nodesLayer.scrollHeight,
}

function initCanvasPan(event) {
  if (event.button !== 0) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  document.addEventListener('mousemove', onCanvasPan);
  document.addEventListener('mouseup', endCanvasPan, {once: true});
}

/**
 * @param {MouseEvent} event
 */
function onCanvasPan(event) {
  const {clientWidth: mainWidth, clientHeight: mainHeight} = canvasWrap;

  const newX= clamp(canvas.offsetLeft + event.movementX, Math.min(canvas.offsetLeft, -limits.right + mainWidth), Math.max(canvas.offsetLeft, -limits.left));
  const newY = clamp(canvas.offsetTop + event.movementY, Math.min(canvas.offsetTop, -limits.bottom + mainHeight), Math.max(canvas.offsetTop, -limits.top));

  // const newX = canvas.offsetLeft + event.movementX;
  // const newY = canvas.offsetTop + event.movementY;

  // tmp.textContent = `${newX}; ${newY}`

  canvas.style.left = `${newX}px`;
  canvas.style.top = `${newY}px`;
  canvasWrap.style.setProperty("--bg-x", `${newX}px`);
  canvasWrap.style.setProperty("--bg-y", `${newY}px`);
}

function endCanvasPan() {
  document.removeEventListener('mousemove', onCanvasPan);
}

function updateCanvas() {
  const {clientWidth: mainWidth, clientHeight: mainHeight} = canvasWrap;

  let left = 0,
    top = 0;

  const right = nodesLayer.scrollWidth,
    bottom = nodesLayer.scrollHeight;

  for (let node of Object.values(nodes)) {
    left = Math.min(left, node.x)
    top = Math.min(top, node.y)
  }

  limits = {
    left: padIfNotDefault(left, 0, -16),
    top: padIfNotDefault(top, 0, -16),
    right: padIfNotDefault(right, mainWidth, 16),
    bottom: padIfNotDefault(bottom, mainHeight, 16),
  }

  // tmp2.textContent = `${limits.left}; ${limits.top}; ${limits.right}; ${limits.bottom}`
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function padIfNotDefault(value, original, padding) {
  return value === original ? original : value + padding;
}
