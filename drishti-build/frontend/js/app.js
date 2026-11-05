import { Api, ApiError, FALLBACK_LANGUAGES, FALLBACK_MODES } from './api.js';
import { Speaker, listen, recognitionSupported } from './speech.js';

const $ = (id) => document.getElementById(id);
const DEFAULTS = {
  apiBase: location.port === '5000' ? '' : 'http://localhost:5000',
  language: 'en', mode: 'safety', engine: 'device', voice: 'neutral', rate: 1.05,
  autoSpeak: true, interval: 5, vibrate: true, quietClear: false, contrast: false, fontSize: 100,
};
const store = {
  load() { try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem('drishti.prefs') || '{}') }; } catch { return { ...DEFAULTS }; } },
  save(p) { try { localStorage.setItem('drishti.prefs', JSON.stringify(p)); } catch {} },
};

const state = {
  prefs: store.load(), languages: FALLBACK_LANGUAGES, modes: FALLBACK_MODES,
  stream: null, source: null /* 'camera' | 'photo' */, photoData: null,
  busy: false, auto: false, autoTimer: null, ctl: null,
  lastResult: null, lastSpoken: { text: '', at: 0 }, history: [], chatBusy: false, walkActive: false, walkPaused: false,
};

const api = new Api(() => state.prefs.apiBase);
const lang = () => state.languages.find(l => l.code === state.prefs.language) || state.languages[0];
const speaker = new Speaker(api, () => ({ ...state.prefs, bcp47: lang().bcp47 }));

function el(tag, props = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') n.className = v; else if (k === 'text') n.textContent = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v);
  }
  for (const k of kids.flat()) if (k != null) n.append(k.nodeType ? k : document.createTextNode(k));
  return n;
}
let toastT;
function toast(msg, ms = 5000) {
  const t = $('toast'); t.textContent = msg; t.hidden = false;
  clearTimeout(toastT); toastT = setTimeout(() => (t.hidden = true), ms);
}
const errMsg = (e) => (e instanceof ApiError || e instanceof Error ? e.message : String(e));
const say = (text, opts) => state.prefs.autoSpeak || opts?.force ? speaker.speak(text, opts) : null;
const persist = () => store.save(state.prefs);

/* ---------------------------------------------------------- tabs */
const tabs = ['vision', 'chat', 'settings'];
function showTab(name) {
  for (const t of tabs) {
    const sel = t === name;
    $('tab-' + t).setAttribute('aria-selected', sel);
    $('tab-' + t).tabIndex = sel ? 0 : -1;
    $('panel-' + t).hidden = !sel;
  }
  if (name !== 'vision' && state.auto) setAuto(false);
}
tabs.forEach((t) => {
  $('tab-' + t).addEventListener('click', () => showTab(t));
  $('tab-' + t).addEventListener('keydown', (e) => {
    const i = tabs.indexOf(t);
    const j = e.key === 'ArrowRight' ? (i + 1) % 3 : e.key === 'ArrowLeft' ? (i + 2) % 3 : -1;
    if (j >= 0) { showTab(tabs[j]); $('tab-' + tabs[j]).focus(); }
  });
});

/* ---------------------------------------------------------- settings UI */
function applyDisplay() {
  document.documentElement.dataset.contrast = state.prefs.contrast ? 'high' : '';
  document.documentElement.style.fontSize = state.prefs.fontSize + '%';
  document.documentElement.lang = state.prefs.language;
}
function bindSettings() {
  const p = state.prefs;
  const bind = (id, key, { out, fmt = (v) => v, num = false } = {}) => {
    const n = $(id), isCheck = n.type === 'checkbox';
    isCheck ? (n.checked = p[key]) : (n.value = p[key]);
    if (out) $(out).textContent = fmt(p[key]);
    n.addEventListener('input', () => {
      p[key] = isCheck ? n.checked : num ? Number(n.value) : n.value;
      if (out) $(out).textContent = fmt(p[key]);
      persist(); applyDisplay();
      if (id === 'interval' && state.auto) setAuto(true);
    });
  };
  bind('apiBase', 'apiBase'); bind('engine', 'engine'); bind('voice', 'voice');
  bind('rate', 'rate', { out: 'rateOut', fmt: (v) => v.toFixed(2) + '×', num: true });
  bind('interval', 'interval', { out: 'intervalOut', fmt: (v) => v + 's', num: true });
  bind('fontSize', 'fontSize', { out: 'fontOut', fmt: (v) => v + '%', num: true });
  bind('autoSpeak', 'autoSpeak'); bind('vibrate', 'vibrate'); bind('quietClear', 'quietClear'); bind('contrast', 'contrast');
  $('apiBase').addEventListener('change', () => { refreshServerInfo(); });
  $('btnTest').addEventListener('click', () => refreshServerInfo(true));
  $('btnTestVoice').addEventListener('click', () => speaker.speak('Drishti voice test. Path is clear.'));
}

function renderLanguages() {
  const sel = $('language'); sel.replaceChildren();
  for (const l of state.languages) sel.append(el('option', { value: l.code, text: l.name === l.native ? l.name : `${l.name} — ${l.native}` }));
  sel.value = state.prefs.language;
}
$('language').addEventListener('change', (e) => { state.prefs.language = e.target.value; persist(); applyDisplay(); });

function renderModes() {
  const g = $('modes'); g.replaceChildren();
  state.modes.forEach((m, i) => {
    const b = el('button', { class: 'mode', role: 'radio', type: 'button', 'data-id': m.id, title: `${m.description} (${i + 1})` },
      el('strong', { text: shortTitle(m) }),
      el('small', { text: m.description }));
    b.addEventListener('click', () => setMode(m.id, true));
    g.append(b);
  });
  setMode(state.prefs.mode);
}
const shortTitle = (m) => ({ safety: 'Safety', read: 'Read text', currency: 'Currency', all: 'Everything' }[m.id] || m.title);
function setMode(id, announce) {
  if (!state.modes.some((m) => m.id === id)) id = 'safety';
  state.prefs.mode = id; persist();
  document.querySelectorAll('.mode').forEach((b) => { const on = b.dataset.id === id; b.setAttribute('aria-checked', on); b.tabIndex = on ? 0 : -1; });
  if (announce) say(shortTitle({ id }) + ' mode', { interrupt: true, force: true });
}

async function refreshServerInfo(verbose) {
  const pill = $('status'), out = $('testOut'), info = $('healthInfo');
  pill.textContent = 'Connecting…'; pill.dataset.state = '';
  try {
    const h = await api.health();
    const demo = h.aiConfig?.isDemoMode;
    pill.textContent = demo ? 'Demo mode' : 'Live AI'; pill.dataset.state = demo ? 'demo' : 'live';
    pill.title = demo ? 'No Gemini API key on the server — using simulated responses' : `Model: ${h.aiConfig.primaryModel}`;
    out.textContent = 'Connected ✓';
    info.replaceChildren(...[['Product', h.product], ['Version', h.version], ['Mode', demo ? 'Demo (simulated)' : 'Live Gemini'],
      ['Primary model', h.aiConfig?.primaryModel], ['Fallback model', h.aiConfig?.fallbackModel], ['Uptime', h.uptime]]
      .flatMap(([k, v]) => [el('dt', { text: k }), el('dd', { text: String(v ?? '—') })]));
    try {
      const [l, m] = await Promise.all([api.languages(), api.modes()]);
      if (l.languages?.length) { state.languages = l.languages; renderLanguages(); }
      if (m.modes?.length) { state.modes = m.modes; renderModes(); }
    } catch {}
  } catch (e) {
    pill.textContent = 'Offline'; pill.dataset.state = 'off'; pill.title = errMsg(e);
    out.textContent = errMsg(e); info.replaceChildren();
    if (verbose) toast(errMsg(e));
  }
}

/* ---------------------------------------------------------- camera */
const video = $('video'), still = $('still'), overlay = $('overlay'), stage = $('stage');

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) return toast('Camera is not available here. Use HTTPS or localhost, or upload a photo.');
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
    video.srcObject = state.stream; await video.play().catch(() => {});
    state.source = 'camera'; state.photoData = null;
    still.hidden = true; video.hidden = false; $('stageEmpty').hidden = true; $('btnStopCam').hidden = false;
    video.addEventListener('loadedmetadata', fitStage, { once: true }); fitStage();
    clearOverlay();
    say('Camera started', { force: true });
  } catch (e) {
    toast(e.name === 'NotAllowedError' ? 'Camera permission was denied.' : `Could not start the camera: ${e.message}`);
  }
}
function stopCamera() {
  state.walkActive = false; state.walkPaused = false; updateWalkState();
  state.stream?.getTracks().forEach((t) => t.stop()); state.stream = null; video.srcObject = null;
  if (state.source === 'camera') { state.source = null; $('stageEmpty').hidden = false; }
  $('btnStopCam').hidden = true; setAuto(false); clearOverlay();
}
function fitStage() {
  const w = video.videoWidth || still.naturalWidth || 16, h = video.videoHeight || still.naturalHeight || 9;
  stage.style.aspectRatio = `${w} / ${h}`;
  requestAnimationFrame(sizeOverlay);
}
function sizeOverlay() {
  const r = stage.getBoundingClientRect(), d = devicePixelRatio || 1;
  overlay.width = Math.round(r.width * d); overlay.height = Math.round(r.height * d);
  if (state.lastResult) drawBoxes(state.lastResult);
}
new ResizeObserver(sizeOverlay).observe(stage);

function loadPhoto(file) {
  if (!file) return;
  const rd = new FileReader();
  rd.onload = () => {
    stopCamera(); state.source = 'photo'; state.photoData = rd.result;
    still.onload = () => { fitStage(); };
    still.src = rd.result; still.hidden = false; video.hidden = true; $('stageEmpty').hidden = true;
    clearOverlay();
    analyze();
  };
  rd.readAsDataURL(file);
}

function captureFrame(maxW = 1024, quality = 0.72) {
  if (state.source === 'photo' && still.naturalWidth) return downscale(still, still.naturalWidth, still.naturalHeight, maxW, quality);
  if (state.source === 'camera' && video.videoWidth) return downscale(video, video.videoWidth, video.videoHeight, maxW, quality);
  return null;
}
function downscale(src, w, h, maxW, q) {
  const s = Math.min(1, maxW / w), c = document.createElement('canvas');
  c.width = Math.round(w * s); c.height = Math.round(h * s);
  c.getContext('2d').drawImage(src, 0, 0, c.width, c.height);
  return c.toDataURL('image/jpeg', q);
}

/* ---------------------------------------------------------- overlay boxes */
const SEV_COLOR = { none: '#4ade80', low: '#facc15', medium: '#fb923c', high: '#f87171' };
function clearOverlay() { overlay.getContext('2d').clearRect(0, 0, overlay.width, overlay.height); }
function drawBoxes(res) {
  const ctx = overlay.getContext('2d'), W = overlay.width, H = overlay.height, d = devicePixelRatio || 1;
  ctx.clearRect(0, 0, W, H);
  const draw = (box, color, label) => {
    if (!Array.isArray(box) || box.length !== 4) return;
    let [y1, x1, y2, x2] = box.map((n) => Math.max(0, Math.min(1000, Number(n) || 0)));
    const x = (x1 / 1000) * W, y = (y1 / 1000) * H, w = ((x2 - x1) / 1000) * W, h = ((y2 - y1) / 1000) * H;
    ctx.lineWidth = 3 * d; ctx.strokeStyle = color; ctx.strokeRect(x, y, w, h);
    ctx.font = `600 ${13 * d}px system-ui, sans-serif`;
    const t = label.length > 40 ? label.slice(0, 38) + '…' : label, tw = ctx.measureText(t).width + 10 * d, th = 20 * d;
    const ly = y - th < 0 ? y : y - th;
    ctx.fillStyle = color; ctx.fillRect(x, ly, tw, th);
    ctx.fillStyle = '#0b0f14'; ctx.textBaseline = 'middle'; ctx.fillText(t, x + 5 * d, ly + th / 2);
  };
  res.detectedObjects?.forEach((o) => draw(o.box2d, SEV_COLOR[o.severity] || SEV_COLOR.low, `${o.label} · ${o.clockPosition} · ${o.distanceMeters}m`));
  res.textReadings?.forEach((t) => draw(t.box2d, '#60a5fa', t.text));
}

/* ---------------------------------------------------------- vision analysis */
function setBusy(b) {
  state.busy = b; $('scanning').hidden = !b; $('btnAnalyze').disabled = b;
  $('btnAnalyze').textContent = b ? 'Analyzing…' : 'Analyze now';
}
async function analyze({ fromAuto = false } = {}) {
  if (state.busy) return;
  const image = captureFrame();
  if (!image) { if (!fromAuto) { toast('Start the camera or upload a photo first.'); say('Start the camera or upload a photo first', { force: true }); } return; }
  setBusy(true); state.ctl = new AbortController();
  try {
    const res = await api.vision({ image, mode: state.prefs.mode, language: state.prefs.language, userPrompt: $('userPrompt').value.trim() }, state.ctl.signal);
    state.lastResult = res.data; renderResult(res);
    drawBoxes(res.data);
    announce(res.data, fromAuto);
  } catch (e) {
    if (e.message !== 'Cancelled') { toast(errMsg(e)); if (!fromAuto) say('Sorry, analysis failed. ' + errMsg(e), { force: true }); }
    if (fromAuto && e instanceof ApiError && e.status === 0) setAuto(false);
  } finally { setBusy(false); }
}
function demoModeNotice() {
  const notices = {
    en: 'Demo mode is active. Camera-based safety guidance is unavailable. Please pause and use your usual mobility aid.',
    hi: 'डेमो मोड चालू है। कैमरे से सुरक्षा मार्गदर्शन उपलब्ध नहीं है। कृपया रुकें और अपने सामान्य सहायक साधन का उपयोग करें।',
    kn: 'ಡೆಮೋ ಮೋಡ್ ಸಕ್ರಿಯವಾಗಿದೆ. ಕ್ಯಾಮೆರಾ ಆಧಾರಿತ ಸುರಕ್ಷತಾ ಮಾರ್ಗದರ್ಶನ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಲ್ಲಿಸಿ, ನಿಮ್ಮ ಸಾಮಾನ್ಯ ಸಹಾಯಕ ಸಾಧನ ಬಳಸಿ.',
    te: 'డెమో మోడ్ ప్రారంభంలో ఉంది. కెమెరా ఆధారిత భద్రతా మార్గదర్శకం అందుబాటులో లేదు. దయచేసి ఆగి, మీ సాధారణ సహాయక పరికరాన్ని ఉపయోగించండి.',
    ta: 'டெமோ முறை இயங்குகிறது. கேமரா பாதுகாப்பு வழிகாட்டல் கிடைக்கவில்லை. தயவுசெய்து நின்று, உங்கள் வழக்கமான உதவி சாதனத்தைப் பயன்படுத்தவும்.',
    mr: 'डेमो मोड सुरू आहे. कॅमेरा-आधारित सुरक्षा मार्गदर्शन उपलब्ध नाही. कृपया थांबा आणि नेहमीचे सहाय्यक साधन वापरा.',
    bn: 'ডেমো মোড চালু আছে। ক্যামেরাভিত্তিক নিরাপত্তা নির্দেশনা পাওয়া যাচ্ছে না। দয়া করে থামুন এবং আপনার পরিচিত সহায়ক উপকরণ ব্যবহার করুন.',
    gu: 'ડેમો મોડ ચાલુ છે. કેમેરા આધારિત સુરક્ષા માર્ગદર્શન ઉપલબ્ધ નથી. કૃપા કરીને થોભો અને તમારા સામાન્ય સહાયક સાધનનો ઉપયોગ કરો.',
    ml: 'ഡെമോ മോഡ് പ്രവർത്തിക്കുന്നു. ക്യാമറ അടിസ്ഥാനത്തിലുള്ള സുരക്ഷാ നിർദ്ദേശം ലഭ്യമല്ല. ദയവായി നിർത്തി പതിവ് സഹായ ഉപകരണം ഉപയോഗിക്കുക.'
  };
  return notices[state.prefs.language] || notices.en;
}

function announce(d, fromAuto) {
  // Never turn simulated sample objects into movement instructions during a walk.
  if (state.walkActive && d.isDemoMode) {
    const demoNotice = demoModeNotice();
    const dupDemo = demoNotice === state.lastSpoken.text && Date.now() - state.lastSpoken.at < 20000;
    if (!dupDemo) {
      state.lastSpoken = { text: demoNotice, at: Date.now() };
      say(demoNotice, { force: true });
    }
    return;
  }
  const alertText = d.spokenAlert || d.sceneSummary || '';
  const actionText = d.immediateAction || '';
  const text = actionText && !alertText.toLowerCase().includes(actionText.toLowerCase())
    ? `${alertText}. ${actionText}` : alertText;
  const hazard = d.hazardSeverity === 'high' || d.hazardSeverity === 'medium';
  if (state.prefs.vibrate && navigator.vibrate) navigator.vibrate(d.hazardSeverity === 'high' ? [300, 100, 300, 100, 300] : d.hazardSeverity === 'medium' ? [200, 100, 200] : 0);
  if (fromAuto) {
    if (state.prefs.quietClear && d.isPathClear && !hazard) return;
    const dup = text === state.lastSpoken.text && Date.now() - state.lastSpoken.at < 12000;
    if (dup && d.hazardSeverity !== 'high') return;
    if (speechSynthesis?.speaking && !hazard) return; // don't talk over ourselves
  }
  state.lastSpoken = { text, at: Date.now() };
  // In text-heavy modes, read the content aloud as well as the alert.
  let full = text;
  if (!fromAuto && d.textReadings?.length && state.prefs.mode !== 'safety') full += '. ' + d.textReadings.map((t) => t.text).join('. ');
  if (!fromAuto && d.currencyDetected?.present && d.currencyDetected.description) full += '. ' + d.currencyDetected.description;
  // Guided Walk always speaks safety instructions, even if general auto-speech is disabled.
  say(full, { force: state.walkActive });
}


function detectionGroup(label) {
  const s = String(label || '').toLowerCase();
  if (/\b(car|truck|bus|van|motorcycle|motorbike|scooter|bike|bicycle|auto|vehicle|train)\b/.test(s)) return 'Vehicles';
  if (/\b(person|people|pedestrian|man|woman|child|crowd|human)\b/.test(s)) return 'People';
  if (/\b(dog|cat|cow|goat|horse|animal|bird|monkey|cattle|sheep)\b/.test(s)) return 'Animals';
  return 'Obstacles';
}
function updateDetectionSummary(objects = []) {
  const groups = { Obstacles: 0, Vehicles: 0, People: 0, Animals: 0 };
  objects.forEach(o => { groups[detectionGroup(o.label)]++; });
  const summary = $('detectionSummary');
  if (!summary) return;
  summary.replaceChildren();
  const entries = Object.entries(groups).filter(([, count]) => count > 0);
  if (!entries.length) {
    summary.append(el('span', { text: 'No objects reported in the latest scan' }));
    return;
  }
  entries.forEach(([name, count]) => summary.append(el('span', { text: `${name}: ${count}` })));
}
function updateWalkState() {
  const pill = $('walkState'), pause = $('btnWalkPause'), end = $('btnWalkEnd'), start = $('btnWalkStart');
  if (!pill) return;
  pill.textContent = !state.walkActive ? 'Not started' : state.walkPaused ? 'Paused' : 'Scanning';
  pill.dataset.state = !state.walkActive ? 'off' : state.walkPaused ? 'demo' : 'live';
  pause.textContent = state.walkPaused ? 'Resume' : 'Pause';
  pause.disabled = !state.walkActive;
  end.disabled = !state.walkActive;
  start.disabled = state.walkActive;
  $('walkHelp').textContent = !state.walkActive
    ? 'Starting a walk turns on continuous safety scans. It does not provide GPS turn-by-turn navigation.'
    : state.walkPaused
      ? 'Scanning is paused. Resume when you are safely ready to continue.'
      : 'Safety scanning is active. Do not rely on this prototype as your only source of mobility or traffic awareness.';
}
async function startGuidedWalk() {
  if (state.source !== 'camera') {
    await startCamera();
    if (state.source !== 'camera') return;
  }
  setMode('safety', true);
  state.walkActive = true;
  state.walkPaused = false;
  updateWalkState();
  setAuto(true);
  say('Guided walk started. Please remain aware of your surroundings.', { force: true });
}
function pauseGuidedWalk() {
  if (!state.walkActive) return;
  state.walkPaused = !state.walkPaused;
  if (state.walkPaused) setAuto(false);
  else setAuto(true);
  updateWalkState();
  say(state.walkPaused ? 'Guided walk paused.' : 'Guided walk resumed.', { force: true });
}
function endGuidedWalk() {
  state.walkActive = false;
  state.walkPaused = false;
  setAuto(false);
  updateWalkState();
  say('Guided walk ended.', { force: true });
}

function renderResult(res) {
  const d = res.data, box = $('result');
  const sev = d.hazardSeverity || 'none';
  box.className = 'result sev-' + sev;
  const kids = [];
  kids.push(el('div', { class: 'hero' },
    el('span', { class: 'badge ' + (d.isPathClear ? 'ok' : 'bad'), text: d.isPathClear ? 'Path clear' : 'Path blocked' }),
    el('span', { class: 'badge sev', text: 'Hazard: ' + sev }),
    d.isDemoMode ? el('span', { class: 'badge demo', text: 'Demo' }) : null,
    el('h2', { class: 'alert', text: d.spokenAlert }),
    d.immediateAction ? el('p', { class: 'action' }, el('strong', { text: 'Recommended action: ' }), d.immediateAction) : null));
  if (d.detectedObjects?.length) kids.push(section('Detected objects', el('ul', { class: 'list' }, d.detectedObjects.map((o) =>
    el('li', {}, el('span', { class: 'dot', style: `background:${SEV_COLOR[o.severity] || SEV_COLOR.low}` }),
      el('strong', { text: o.label }), ` — ${o.clockPosition}, ${o.distanceMeters} m `, el('em', { text: `(${o.severity})` }))))));
  if (d.textReadings?.length) kids.push(section('Text found', el('ul', { class: 'list' }, d.textReadings.map((t) =>
    el('li', {}, el('span', { class: 'tag', text: t.category }), el('q', { text: t.text }), el('small', { text: ` ${Math.round((t.confidence ?? 0) * 100)}%` }))))));
  const c = d.currencyDetected;
  if (c?.present) kids.push(section('Currency', el('p', {}, el('strong', { text: `${c.currency || ''} ${c.denomination ?? ''}`.trim() }),
    c.confidence != null ? ` (${Math.round(c.confidence * 100)}% sure)` : '', c.description ? el('br') : null, c.description || '')));
  kids.push(section('Scene', el('p', { text: d.sceneSummary })));
  if (d.safetyNote) kids.push(section('Safety tip', el('p', { text: d.safetyNote })));
  const meta = [new Date(res.timestamp).toLocaleTimeString(), d.modelUsed, d.fallbackReason && `fallback: ${d.fallbackReason}`].filter(Boolean).join(' · ');
  kids.push(el('p', { class: 'meta', text: meta }));
  box.replaceChildren(...kids);
  updateDetectionSummary(d.detectedObjects || []);
}
const section = (title, body) => el('section', { class: 'sec' }, el('h3', { text: title }), body);


function installDetectionSummary() {
  const result = $('result');
  if (!result || $('detectionSummary')) return;
  const wrap = el('section', { class: 'sec' },
    el('h3', { text: 'Latest detection categories' }),
    el('div', { id: 'detectionSummary', class: 'object-summary', 'aria-live': 'polite' },
      el('span', { text: 'Waiting for the first scan' })));
  result.parentNode.insertBefore(wrap, result);
}

/* ---------------------------------------------------------- auto-scan */
function setAuto(on) {
  if (on && !state.source) { toast('Start the camera first.'); on = false; }
  if (on && state.source === 'photo') on = false;
  clearInterval(state.autoTimer); state.auto = on;
  $('btnAuto').setAttribute('aria-pressed', on); $('btnAuto').textContent = 'Auto-scan: ' + (on ? 'on' : 'off');
  $('btnAuto').classList.toggle('active', on);
  if (state.walkActive && !on && !state.walkPaused) { state.walkPaused = true; updateWalkState(); }
  if (state.walkActive && on && state.walkPaused) { state.walkPaused = false; updateWalkState(); }
  if (on) { analyze({ fromAuto: true }); state.autoTimer = setInterval(() => analyze({ fromAuto: true }), state.prefs.interval * 1000); }
}

/* ---------------------------------------------------------- voice input */
async function dictate(btn, input, then) {
  if (btn.classList.contains('listening')) return;
  speaker.stop();
  btn.classList.add('listening'); btn.setAttribute('aria-pressed', 'true');
  const old = input.placeholder; input.placeholder = 'Listening…';
  try {
    const t = await listen(lang().bcp47, { onInterim: (x) => (input.value = x) });
    if (t) { input.value = t; then?.(t); } else toast('I did not hear anything.');
  } catch (e) { toast(errMsg(e)); }
  finally { btn.classList.remove('listening'); btn.setAttribute('aria-pressed', 'false'); input.placeholder = old; }
}
const micVision = () => dictate($('btnMicPrompt'), $('userPrompt'), () => analyze());
const micChat = () => dictate($('btnMicChat'), $('chatInput'), () => sendChat());

/* ---------------------------------------------------------- chat */
function addMsg(role, text, extra) {
  const m = el('div', { class: 'msg ' + role }, el('div', { class: 'bubble ' + (extra?.urgency || '') }, text));
  if (extra?.note) m.firstChild.append(el('small', { class: 'note', text: extra.note }));
  $('chatLog').append(m); $('chatLog').scrollTop = $('chatLog').scrollHeight; return m;
}
function setChips(list) {
  const c = $('chips'); c.replaceChildren();
  (list || []).forEach((s) => c.append(el('button', { class: 'chip', type: 'button', onclick: () => { $('chatInput').value = s; sendChat(); } }, s)));
}
async function sendChat() {
  const msg = $('chatInput').value.trim();
  if (!msg || state.chatBusy) return;
  state.chatBusy = true; $('chatInput').value = ''; setChips([]);
  addMsg('user', msg);
  const pending = addMsg('model pending', 'Thinking…');
  const image = $('chatWithFrame').checked ? captureFrame(800, 0.65) : null;
  if ($('chatWithFrame').checked && !image) toast('No camera view available — sending text only.');
  try {
    const r = await api.chat({ message: msg, history: state.history.slice(-10), language: state.prefs.language, image });
    const d = r.data; pending.remove();
    addMsg('model', d.reply, { urgency: d.urgency, note: d.isDemoMode ? 'Demo response' : null });
    state.history.push({ role: 'user', text: msg }, { role: 'model', text: d.reply });
    setChips(d.suggestedActions);
    if (d.urgency === 'critical' && state.prefs.vibrate && navigator.vibrate) navigator.vibrate([300, 100, 300]);
    say(d.spokenText || d.reply);
  } catch (e) {
    pending.remove(); addMsg('model error', 'Sorry, something went wrong: ' + errMsg(e));
  } finally { state.chatBusy = false; }
}

/* ---------------------------------------------------------- wiring */
$('btnCamera').addEventListener('click', startCamera);
$('btnWalkStart').addEventListener('click', startGuidedWalk);
$('btnWalkPause').addEventListener('click', pauseGuidedWalk);
$('btnWalkEnd').addEventListener('click', endGuidedWalk);
$('btnStopCam').addEventListener('click', stopCamera);
$('btnAnalyze').addEventListener('click', () => analyze());
$('btnAuto').addEventListener('click', () => setAuto(!state.auto));
$('fileInput').addEventListener('change', (e) => { loadPhoto(e.target.files[0]); e.target.value = ''; });
$('userPrompt').addEventListener('keydown', (e) => { if (e.key === 'Enter') analyze(); });
$('btnMicPrompt').addEventListener('click', micVision);
$('btnMicChat').addEventListener('click', micChat);
$('btnRepeat').addEventListener('click', () => { const t = state.lastSpoken.text; t ? speaker.speak(t) : toast('Nothing to repeat yet.'); });
$('btnStop').addEventListener('click', () => speaker.stop());
$('chatForm').addEventListener('submit', (e) => { e.preventDefault(); sendChat(); });
$('btnClearChat').addEventListener('click', () => {
  state.history = []; setChips([]);
  $('chatLog').replaceChildren(el('div', { class: 'msg model' }, el('div', { class: 'bubble', text: 'Conversation cleared.' })));
});
$('modes').addEventListener('keydown', (e) => {
  const ids = state.modes.map((m) => m.id), i = ids.indexOf(state.prefs.mode);
  const j = ['ArrowRight', 'ArrowDown'].includes(e.key) ? (i + 1) % ids.length : ['ArrowLeft', 'ArrowUp'].includes(e.key) ? (i + ids.length - 1) % ids.length : -1;
  if (j >= 0) { e.preventDefault(); setMode(ids[j], true); document.querySelector(`.mode[data-id="${ids[j]}"]`).focus(); }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { speaker.stop(); return; }
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const tag = e.target.tagName;
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;
  const k = e.key.toLowerCase(), onChat = !$('panel-chat').hidden, onVision = !$('panel-vision').hidden;
  if (k === 'm' && (onVision || onChat)) { e.preventDefault(); (onChat ? micChat : micVision)(); }
  if (!onVision) return;
  if (k === 'a') { e.preventDefault(); analyze(); }
  else if (k === 's') setAuto(!state.auto);
  else if (k === 'r') $('btnRepeat').click();
  else if (/^[1-9]$/.test(k) && state.modes[+k - 1]) setMode(state.modes[+k - 1].id, true);
});
window.addEventListener('beforeunload', () => { speaker.stop(); stopCamera(); });
document.addEventListener('visibilitychange', () => { if (document.hidden && state.auto) setAuto(false); });

if (!recognitionSupported()) ['btnMicPrompt', 'btnMicChat'].forEach((id) => { $(id).title = 'Voice input needs Chrome or Edge'; $(id).classList.add('unsupported'); });

bindSettings(); applyDisplay(); renderLanguages(); renderModes(); installDetectionSummary(); updateWalkState(); showTab('vision'); refreshServerInfo();
if ('speechSynthesis' in window) speechSynthesis.getVoices();
