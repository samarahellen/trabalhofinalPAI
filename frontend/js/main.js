// ═══════════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════════
let nodes = {};       // id -> {type,x,y,data,el,inputPort,outputPort}
let connections = []; // [{from,to,path}]
let nodeCounter = 0;
let selectedNode = null;
let draggingNode = null;
let dragOffX = 0, dragOffY = 0;
let connectingFrom = null; // {nodeId, isOutput}

const API = 'http://127.0.0.1:5000/api';

const NODE_DEFS = {
  load:       { label:'Carregar PGM', icon:'📂', color:'#00e5a0', hasIn:false, hasOut:true  },
  display:    { label:'Exibir',        icon:'🖼',  color:'#38bdf8', hasIn:true,  hasOut:false },
  save:       { label:'Salvar PGM',    icon:'💾',  color:'#a3e635', hasIn:true,  hasOut:false },
  brightness: { label:'Brilho',        icon:'☀️',  color:'#f59e0b', hasIn:true,  hasOut:true  },
  threshold:  { label:'Limiarização',  icon:'⬛',  color:'#f59e0b', hasIn:true,  hasOut:true  },
  convolution:{ label:'Convolução',    icon:'🔲',  color:'#7c3aed', hasIn:true,  hasOut:true  },
  median:     { label:'Mediana',       icon:'🔵',  color:'#7c3aed', hasIn:true,  hasOut:true  },
  complement: { label:'Complemento',   icon:'🔄',  color:'#ec4899', hasIn:true,  hasOut:true  },
  histogram:  { label:'Histograma',    icon:'📊',  color:'#06b6d4', hasIn:true,  hasOut:false },
  difference: { label:'Diferença',     icon:'➖',  color:'#f97316', hasIn:true,  hasIn2:true, hasOut:true  },
  morphology: { label:'Morfologia',    icon:'🔷',  color:'#10b981', hasIn:true,  hasOut:true  },
};

// ═══════════════════════════════════════════════════════
//  NODE CREATION
// ═══════════════════════════════════════════════════════
function createNode(type, x, y) {
  const id = 'n' + (++nodeCounter);
  const def = NODE_DEFS[type];
  const el = document.createElement('div');
  el.className = 'node';
  el.style.left = x + 'px';
  el.style.top  = y + 'px';
  el.dataset.id = id;
  el.innerHTML = buildNodeHTML(id, type, def);
  document.getElementById('nodes-layer').appendChild(el);

  const node = { id, type, x, y, data: {}, el,
    inputPort: el.querySelector('.port.in'),
    inputPort2: el.querySelector('.port.in2'),
    outputPort: el.querySelector('.port.out'),
  };
  nodes[id] = node;

  // Header drag
  el.querySelector('.node-header').addEventListener('mousedown', e => startNodeDrag(e, id));
  // Select on click
  el.addEventListener('mousedown', e => selectNode(e, id));
  // Delete
  el.querySelector('.node-del').addEventListener('click', e => { e.stopPropagation(); deleteNode(id); });

  // Port events
  [el.querySelector('.port.in'), el.querySelector('.port.in2'), el.querySelector('.port.out')].forEach(p => {
    if (!p) return;
    const isOut = p.classList.contains('out');
    const isIn2 = p.classList.contains('in2');
    p.addEventListener('mousedown', e => { e.stopPropagation(); startConnection(e, id, isOut, isIn2); });
    p.addEventListener('mouseup',   e => { e.stopPropagation(); endConnection(id, isOut, isIn2); });
  });

  // Node-specific listeners
  setupNodeListeners(id, type, el);
  updateCanvas();
  return id;
}

function buildNodeHTML(id, type, def) {
  const inp = def.hasIn  ? `<div class="port in"  title="Entrada A"></div><span class="port-label">in${def.hasIn2 ? " A" : ""}</span>` : `<div></div>`;
  const out = def.hasOut ? `<span class="port-label">out</span><div class="port out" title="Saída"></div>` : `<div></div>`;
  const inp2Row = def.hasIn2 ? `<div class="node-port-row"><div class="port in2" title="Entrada B"></div><span class="port-label">in B</span><div style="visibility: hidden">out</div><div></div></div>` : '';
  let body = buildNodeBody(id, type);
  return `
    <div class="node-header" style="border-left:3px solid ${def.color}">
      <span class="node-icon">${def.icon}</span>
      <span class="node-title">${def.label}</span>
      <button class="node-del" title="Remover">✕</button>
    </div>
    <div class="node-body">
      <div class="node-port-row">${inp}${out}</div>
      ${inp2Row}
      ${body}
    </div>`;
}

function buildNodeBody(id, type) {
  switch(type) {
    case 'load': return `
      <label class="tb-btn" for="file-${id}" style="width:100%;justify-content:center;margin:4px 0;font-size:11px">
        Escolher .pgm
      </label>
      <input type="file" id="file-${id}" accept=".pgm" style="display:none"/>
      <div class="node-preview-placeholder" id="prev-${id}">sem imagem</div>
      <div class="node-status" id="st-${id}"></div>`;

    case 'display': return `
      <div class="node-preview-placeholder" id="prev-${id}">aguardando entrada</div>
      <button class="node-run-btn" id="run-${id}">Atualizar</button>
      <div class="node-status" id="st-${id}"></div>`;

    case 'save': return `
      <button class="node-run-btn" id="run-${id}">Salvar</button>
      <div class="node-status" id="st-${id}"></div>`;

    case 'brightness': return `
      <div class="param-row">
        <span class="param-label">Delta (−255 a 255)</span>
        <input class="param-input" type="number" id="p-delta-${id}" value="30" min="-255" max="255"/>
      </div>
      <button class="node-run-btn" id="run-${id}">Processar</button>
      <div class="node-preview-placeholder" id="prev-${id}" style="height:70px">resultado</div>
      <div class="node-status" id="st-${id}"></div>`;

    case 'threshold': return `
      <div class="param-row">
        <span class="param-label">Limiar (0–255)</span>
        <input class="param-input" type="number" id="p-thresh-${id}" value="128" min="0" max="255"/>
      </div>
      <button class="node-run-btn" id="run-${id}">Processar</button>
      <div class="node-preview-placeholder" id="prev-${id}" style="height:70px">resultado</div>
      <div class="node-status" id="st-${id}"></div>`;

    case 'convolution': return `
      <div class="param-row">
        <span class="param-label">Máscara</span>
        <select class="param-input" id="p-preset-${id}">
          <option value="mean">Média</option>
          <option value="median_conv">–</option>
          <option value="laplacian">Laplaciano</option>
          <option value="sharpen">Nitidez</option>
          <option value="sobel_x">Sobel X</option>
          <option value="sobel_y">Sobel Y</option>
          <option value="custom">Personalizada</option>
        </select>
      </div>
      <div class="param-row">
        <span class="param-label">Tamanho</span>
        <input class="param-input" type="number" id="p-size-${id}" value="3" min="3" max="9" step="2"/>
      </div>
      <button class="node-run-btn" id="run-${id}">Processar</button>
      <div class="node-preview-placeholder" id="prev-${id}" style="height:70px">resultado</div>
      <div class="node-status" id="st-${id}"></div>`;

    case 'median': return `
      <div class="param-row">
        <span class="param-label">Tamanho da janela</span>
        <input class="param-input" type="number" id="p-size-${id}" value="3" min="3" max="9" step="2"/>
      </div>
      <button class="node-run-btn" id="run-${id}">Processar</button>
      <div class="node-preview-placeholder" id="prev-${id}" style="height:70px">resultado</div>
      <div class="node-status" id="st-${id}"></div>`;

    case 'complement': return `
      <button class="node-run-btn" id="run-${id}">Processar</button>
      <div class="node-preview-placeholder" id="prev-${id}" style="height:70px">resultado</div>
      <div class="node-status" id="st-${id}"></div>`;

    case 'histogram': return `
      <button class="node-run-btn" id="run-${id}">Calcular</button>
      <canvas class="hist-canvas" id="hist-${id}"></canvas>
      <div class="node-status" id="st-${id}"></div>`;

    case 'difference': return `
      <button class="node-run-btn" id="run-${id}">Calcular</button>
      <div class="node-preview-placeholder" id="prev-${id}" style="height:70px">resultado</div>
      <div class="node-status" id="st-${id}"></div>`;

    case 'morphology': return `
      <div class="param-row">
        <span class="param-label">Operação</span>
        <select class="param-input" id="p-op-${id}">
          <option value="erosion">Erosão</option>
          <option value="dilation">Dilatação</option>
          <option value="opening">Abertura</option>
          <option value="closing">Fechamento</option>
        </select>
      </div>
      <div class="param-row">
        <span class="param-label">Elem. estruturante</span>
        <select class="param-input" id="p-elem-${id}">
          <option value="square">Quadrado</option>
          <option value="vertical">Vertical</option>
          <option value="horizontal">Horizontal</option>
          <option value="diagonal_down">Diagonal para baixo</option>
          <option value="diagonal_up">Diagonal para cima</option>
          <option value="cross">Cruz +</option>
          <option value="x">Cruz x</option>
          <option value="circle">Circular</option>
          <option value="diamond">Diamante</option>
        </select>
      </div>
      <div class="param-row">
        <span class="param-label">Tamanho do elem. estruturante</span>
        <input class="param-input" type="number" id="p-size-${id}" value="3" min="3" max="9" step="2"/>
      </div>
      <!-- div class="toggle-row">
        <span class="param-label">Máscara uniforme</span>
        <label class="toggle-wrap" title="Aplicar pesos uniformes ao elemento estruturante">
          <input type="checkbox" id="p-flat-${id}"/>
          <div class="toggle-track"><div class="toggle-thumb"></div></div>
        </label>
      </div -->
      <button class="node-run-btn" id="run-${id}">Processar</button>
      <div class="node-preview-placeholder" id="prev-${id}" style="height:70px">resultado</div>
      <div class="node-status" id="st-${id}"></div>`;

    default: return '';
  }
}

function setupNodeListeners(id, type, el) {
  if (type === 'load') {
    el.querySelector(`#file-${id}`).addEventListener('change', e => uploadFile(id, e.target.files[0]));
  }
  const runBtn = el.querySelector(`#run-${id}`);
  if (runBtn) {
    runBtn.addEventListener('click', e => { e.stopPropagation(); runNode(id); });
  }
}

// ═══════════════════════════════════════════════════════
//  UPLOAD
// ═══════════════════════════════════════════════════════
async function uploadFile(id, file) {
  if (!file) return;
  setStatus(id, 'Enviando...', '');
  const fd = new FormData();
  fd.append('file', file);
  try {
    const r = await fetch(`${API}/upload`, { method:'POST', body:fd });
    const d = await r.json();
    if (d.error) { setStatus(id, d.error, 'err'); return; }
    nodes[id].data.file_id = d.file_id;
    nodes[id].data.output_id = d.file_id;
    setPreview(id, d.preview);
    setStatus(id, `${d.width}×${d.height}px`, 'ok');
    nodes[id].el.querySelector('.node-title').textContent = file.name.slice(0,20);
    toast(`Carregado: ${file.name}`, 'ok');
  } catch(e) { setStatus(id, 'Erro de conexão', 'err'); }
}

// Upload via topbar
document.getElementById('upload-input').addEventListener('change', async e => {
  for (const file of e.target.files) {
    const id = createNode('load', 60 + Math.random()*200, 80 + Math.random()*200);
    await uploadFile(id, file);
  }
  e.target.value = '';
});

// ═══════════════════════════════════════════════════════
//  PROCESS
// ═══════════════════════════════════════════════════════
function getInputId(nodeId, useIn2 = false) {
  const conn = connections.find(c => c.to === nodeId && (c.toIn2 || false) === useIn2);
  if (!conn) return null;
  return nodes[conn.from]?.data?.output_id || null;
}

async function runNode(id) {
  const node = nodes[id];
  const type = node.type;
  const el   = node.el;

  if (type === 'save') {
    const inputId = getInputId(id);
    if (!inputId) { setStatus(id, 'Conecte uma entrada', 'err'); return; }
    const a = document.createElement('a');
    a.href = `${API}/download/${inputId}`;
    a.download = `${inputId}.pgm`;
    a.click();
    setStatus(id, 'Download iniciado', 'ok');
    return;
  }

  if (type === 'display') {
    const inputId = getInputId(id);
    if (!inputId) { setStatus(id, 'Conecte uma entrada', 'err'); return; }
    const src = await fetchPreview(inputId);
    if (src) { setPreview(id, src); setStatus(id, 'Exibindo', 'ok'); }
    return;
  }

  const inputId = getInputId(id);
  if (!inputId) { setStatus(id, 'Conecte uma entrada', 'err'); return; }

  setStatus(id, 'Processando...', '');
  const params = gatherParams(id, type, el);

  let body = { block: type, input_id: inputId, params };

  if (type === 'difference') {
    const bId = getInputId(id, true);
    if (!bId) { setStatus(id, 'Conecte a entrada B', 'err'); return; }
    params.input_b_id = bId;
  }

  try {
    const r = await fetch(`${API}/process`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const d = await r.json();
    if (d.error) { setStatus(id, d.error, 'err'); return; }

    if (d.histogram) {
      drawHistogram(id, d.histogram);
      setStatus(id, 'Histograma gerado', 'ok');
      return;
    }

    node.data.output_id = d.output_id;
    setPreview(id, d.preview);
    setStatus(id, `${d.width}×${d.height}px`, 'ok');
    propagateDown(id);
  } catch(e) { setStatus(id, 'Erro de conexão', 'err'); }
}

function gatherParams(id, type, el) {
  const get = sel => el.querySelector(sel)?.value;
  switch(type) {
    case 'brightness':  return { delta: parseInt(get(`#p-delta-${id}`) || 30) };
    case 'threshold':   return { threshold: parseInt(get(`#p-thresh-${id}`) || 128) };
    case 'convolution': return { preset: get(`#p-preset-${id}`), size: parseInt(get(`#p-size-${id}`) || 3) };
    case 'median':      return { size: parseInt(get(`#p-size-${id}`) || 3) };
    case 'morphology':  return {
      op: get(`#p-op-${id}`),
      size: parseInt(get(`#p-size-${id}`) || 3),
      elem: get(`#p-elem-${id}`) || 'rect',
      // flat: el.querySelector(`#p-flat-${id}`)?.checked || false
    };
    default: return {};
  }
}

async function fetchPreview(fileId) {
  // We re-run a display block to get preview – or store in node data
  for (const [nid, n] of Object.entries(nodes)) {
    if (n.data.output_id === fileId || n.data.file_id === fileId) {
      const img = n.el.querySelector(`#prev-${nid}`);
      if (img && img.tagName === 'IMG') return img.src.split(',')[1];
    }
  }
  return null;
}

function propagateDown(fromId) {
  const downConns = connections.filter(c => c.from === fromId);
  downConns.forEach(c => {
    const n = nodes[c.to];
    if (n && ['display','brightness','threshold','convolution','median','complement','histogram','difference','morphology'].includes(n.type)) {
      // auto-run display nodes
      if (n.type === 'display') runNode(c.to);
    }
  });
}

// ═══════════════════════════════════════════════════════
//  HISTOGRAM DRAWING
// ═══════════════════════════════════════════════════════
function drawHistogram(id, hist) {
  const cv = document.getElementById(`hist-${id}`);
  if (!cv) return;
  const ctx = cv.getContext('2d');
  const W = cv.width = cv.offsetWidth;
  const H = cv.height = cv.offsetHeight;
  ctx.clearRect(0,0,W,H);
  const max = Math.max(...hist);
  ctx.fillStyle = '#00e5a0';
  const bw = W / 256;
  for (let i = 0; i < 256; i++) {
    const h = (hist[i] / max) * H;
    ctx.fillRect(i * bw, H - h, bw, h);
  }
}

// ═══════════════════════════════════════════════════════
//  CONNECTIONS
// ═══════════════════════════════════════════════════════
let tempLine = null;
let tempMouseHandler = null;

function startConnection(e, nodeId, isOutput, isIn2 = false) {
  e.preventDefault();
  connectingFrom = { nodeId, isOutput, isIn2 };
  const svg = document.getElementById('svg-connections');
  tempLine = document.createElementNS('http://www.w3.org/2000/svg','path');
  tempLine.setAttribute('stroke', isOutput ? '#7c3aed' : isIn2 ? '#f97316' : '#00e5a0');
  tempLine.setAttribute('stroke-width','2');
  tempLine.setAttribute('fill','none');
  tempLine.setAttribute('stroke-dasharray','6,4');
  svg.appendChild(tempLine);

  tempMouseHandler = ev => {
    const rect = document.getElementById('canvas').getBoundingClientRect();
    const port = getPortPos(nodeId, isOutput, isIn2);
    const mx = ev.clientX - rect.left;
    const my = ev.clientY - rect.top;
    tempLine.setAttribute('d', bezierPath(port.x, port.y, mx, my));
  };
  document.addEventListener('mousemove', tempMouseHandler);
  document.addEventListener('mouseup', cancelConnection, {once:true});
}

function endConnection(nodeId, isOutput, isIn2 = false) {
  if (!connectingFrom) return;
  document.removeEventListener('mousemove', tempMouseHandler);
  const svg = document.getElementById('svg-connections');
  if (tempLine) { svg.removeChild(tempLine); tempLine = null; }

  const from = connectingFrom;
  connectingFrom = null;

  // Determine which is output, which is input
  let fromId, toId, toIn2;
  if (from.isOutput && !isOutput) { fromId = from.nodeId; toId = nodeId; toIn2 = isIn2; }
  else if (!from.isOutput && isOutput) { fromId = nodeId; toId = from.nodeId; toIn2 = from.isIn2; }
  else { return; }

  if (fromId === toId) return;
  // Remove existing connection to the same port on toId
  connections = connections.filter(c => {
    if (c.to === toId && c.toIn2 === toIn2) {
      svg.removeChild(c.path);
      return false;
    }
    return true;
  });

  const path = document.createElementNS('http://www.w3.org/2000/svg','path');
  path.classList.add('conn-path');
  path.setAttribute('stroke', toIn2 ? '#f97316' : '#00e5a0');
  svg.appendChild(path);
  connections.push({ from:fromId, to: toId, toIn2: toIn2 || false, path });
  updateConnections();
  toast('Conectado!', 'ok');
}

function cancelConnection() {
  if (tempMouseHandler) document.removeEventListener('mousemove', tempMouseHandler);
  if (tempLine) {
    document.getElementById('svg-connections').removeChild(tempLine);
    tempLine = null;
  }
  connectingFrom = null;
}

function getPortPos(nodeId, isOutput, isIn2 = false) {
  const n = nodes[nodeId];
  const port = isOutput ? n.outputPort : (isIn2 ? n.inputPort2 : n.inputPort);
  if (!port) return {x:n.x, y:n.y};
  const wr = document.getElementById('canvas').getBoundingClientRect();
  const pr = port.getBoundingClientRect();
  return { x: pr.left - wr.left + pr.width/2, y: pr.top - wr.top + pr.height/2 };
}

function bezierPath(x1, y1, x2, y2) {
  const cx = (x1 + x2) / 2;
  return `M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}`;
}

function updateConnections() {
  connections.forEach(c => {
    if (!nodes[c.from] || !nodes[c.to]) return;
    const p1 = getPortPos(c.from, true);
    const p2 = getPortPos(c.to, false, c.toIn2);
    if (p1 && p2) c.path.setAttribute('d', bezierPath(p1.x, p1.y, p2.x, p2.y));
  });
}

// ═══════════════════════════════════════════════════════
//  NODE DRAG
// ═══════════════════════════════════════════════════════
function startNodeDrag(e, id) {
  e.preventDefault()
  draggingNode = id;
  const n = nodes[id];
  dragOffX = e.clientX - n.x;
  dragOffY = e.clientY - n.y;
  document.addEventListener('mousemove', onNodeDrag);
  document.addEventListener('mouseup', stopNodeDrag, {once:true});
}
function onNodeDrag(e) {
  if (!draggingNode) return;
  const n = nodes[draggingNode];
  n.x = e.clientX - dragOffX;
  n.y = e.clientY - dragOffY;
  n.el.style.left = n.x + 'px';
  n.el.style.top  = n.y + 'px';
  updateConnections();
  updateCanvas();
}
function stopNodeDrag() {
  document.removeEventListener('mousemove', onNodeDrag);
  draggingNode = null;
}

// ═══════════════════════════════════════════════════════
//  DROP FROM PALETTE
// ═══════════════════════════════════════════════════════
let dragType = null;
document.querySelectorAll('.p-item').forEach(el => {
  el.addEventListener('dragstart', e => { dragType = el.dataset.type; });
  el.addEventListener('dragend', () => { dragType = null; });
});
function onCanvasDrop(e) {
  if (!dragType) return;
  const rect = document.getElementById('canvas').getBoundingClientRect();
  const x = e.clientX - rect.left - 110;
  const y = e.clientY - rect.top  - 30;
  createNode(dragType, x, y);
}

// ═══════════════════════════════════════════════════════
//  SELECT / DELETE
// ═══════════════════════════════════════════════════════
function selectNode(e, id) {
  e.stopImmediatePropagation()
  if (selectedNode) nodes[selectedNode]?.el?.classList.remove('selected');
  selectedNode = id;
  nodes[id]?.el?.classList.add('selected');
  renderProps(id);
}

function deleteNode(id) {
  const svg = document.getElementById('svg-connections');
  connections = connections.filter(c => {
    if (c.from === id || c.to === id) { svg.removeChild(c.path); return false; }
    return true;
  });
  nodes[id]?.el?.remove();
  delete nodes[id];
  if (selectedNode === id) { selectedNode = null; renderProps(null); }
  updateCanvas();
}

function clearCanvas() {
  Object.keys(nodes).forEach(id => deleteNode(id));
  nodes = {}; connections = []; nodeCounter = 0;
}

// ═══════════════════════════════════════════════════════
//  RUN ALL
// ═══════════════════════════════════════════════════════
async function runAll() {
  // Topological sort
  const order = topoSort();
  for (const id of order) {
    if (['brightness','threshold','convolution','median','complement','histogram','difference','morphology','display'].includes(nodes[id]?.type)) {
      await runNode(id);
    }
  }
  toast('Pipeline executado!', 'ok');
}

function topoSort() {
  const visited = new Set();
  const result  = [];
  function visit(id) {
    if (visited.has(id)) return;
    visited.add(id);
    const upConns = connections.filter(c => c.to === id);
    upConns.forEach(c => visit(c.from));
    result.push(id);
  }
  Object.keys(nodes).forEach(id => visit(id));
  return result;
}

// ═══════════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════════
function setStatus(id, msg, cls) {
  const el = document.getElementById(`st-${id}`);
  if (!el) return;
  el.textContent = msg;
  el.className = 'node-status' + (cls ? ' ' + cls : '');
}

function setPreview(id, b64) {
  const wrap = document.getElementById(`prev-${id}`);
  if (!wrap) return;
  const src = 'data:image/png;base64,' + b64;
  if (wrap.tagName === 'IMG') { wrap.src = src; return; }
  const img = document.createElement('img');
  img.className = 'node-preview';
  img.id = `prev-${id}`;
  img.src = src;
  img.title = 'Clique para ampliar';
  img.style.cursor = 'zoom-in';
  img.addEventListener('click', e => { e.stopPropagation(); openLightbox(img, NODE_DEFS[nodes[id]?.type]?.label || ''); });
  wrap.replaceWith(img);
}

function renderProps(id) {
  const p = document.getElementById('props-panel');
  if (!id || !nodes[id]) {
    p.innerHTML = '<h3>Propriedades</h3><p class="prop-empty">Selecione um nó para ver suas propriedades</p>';
    return;
  }
  const n = nodes[id];
  p.innerHTML = `
    <h3>Propriedades</h3>
    <div style="font-size:13px;font-weight:600">${NODE_DEFS[n.type].icon} ${NODE_DEFS[n.type].label}</div>
    <div style="font-size:11px;color:var(--text2)">ID: ${id}</div>
    ${n.data.output_id ? `<div style="font-size:11px;color:var(--accent)">Output: ${n.data.output_id.slice(0,12)}…</div>` : ''}
    ${n.data.file_id   ? `<div style="font-size:11px;color:var(--text2)">File: ${n.data.file_id.slice(0,12)}…</div>` : ''}
    <hr style="border-color:var(--border)"/>
    <div style="font-size:11px;color:var(--text2)">
      Conexões de entrada: ${connections.filter(c=>c.to===id).length}<br/>
      Conexões de saída: ${connections.filter(c=>c.from===id).length}
    </div>`;
}

function toast(msg, cls='ok') {
  const el = document.createElement('div');
  el.className = `toast ${cls}`;
  el.textContent = msg;
  document.getElementById('toast-area').appendChild(el);
  setTimeout(() => el.remove(), 2800);
}

// ═══════════════════════════════════════════════════════
//  LIGHTBOX
// ═══════════════════════════════════════════════════════
function openLightbox(elem, label) {
  const src = elem.src;
  let lb = document.getElementById('lightbox');
  if (!lb) {
    lb = document.createElement('div');
    lb.id = 'lightbox';
    lb.innerHTML = `
      <div id="lb-backdrop"></div>
      <div id="lb-box">
        <div id="lb-header">
          <span id="lb-title"></span>
          <div id="lb-actions">
            <a id="lb-download" title="Baixar imagem">⬇ Baixar</a>
            <button id="lb-close" title="Fechar (Esc)">✕</button>
          </div>
        </div>
        <div id="lb-img-wrap">
          <img id="lb-img" alt="Visualização ampliada"/>
        </div>
      </div>`;
    document.body.appendChild(lb);
    document.getElementById('lb-backdrop').addEventListener('click', closeLightbox);
    document.getElementById('lb-close').addEventListener('click', closeLightbox);
  }
  document.getElementById('lb-title').textContent = label;
  const img = document.getElementById('lb-img');
  img.src = src;
  const dl = document.getElementById('lb-download');
  dl.href = src;
  dl.download = `${label || 'imagem'}.png`;
  lb.classList.add('open');
}

function closeLightbox() {
  document.getElementById('lightbox')?.classList.remove('open');
}


document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeLightbox(); return; }
  if ((e.key === 'Delete' || e.key === 'Backspace') && selectedNode &&
    !['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)) {
    deleteNode(selectedNode);
  }
});

// Redraw connections on scroll/resize
window.addEventListener('resize', updateConnections);
