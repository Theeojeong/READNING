import { ActiveChunkDetector } from './detector.js';
import { AudioController } from './audio.js';

// Integration points
// - Manifest shape expected: { title, chunks: [{ id, title?, text, audioUrl, fadeMs? }] }
// - Backend should provide manifest.json (or pass JSON inline); audio URLs must be same-origin/allowed by CORS.

const state = {
  manifest: null,
  activeId: null,
  autoSwitch: true,
  audioEnabled: false,
};

const ui = {
  reader: document.getElementById('reader'),
  btnEnable: document.getElementById('enable-audio'),
  chkAuto: document.getElementById('auto-switch'),
  rangeVol: document.getElementById('volume'),
  btnMute: document.getElementById('mute'),
  dbg: document.getElementById('debug'),
  dbgActive: document.getElementById('dbg-active'),
  dbgList: document.getElementById('dbg-list'),
};

const audio = new AudioController();
let detector;

init();

async function init(){
  // Load manifest (replace with server-provided data as needed)
  const manifest = await fetch('manifest.json').then(r=>r.json()).catch(()=>null);
  if (!manifest) {
    ui.reader.innerHTML = '<p style="color:#f88">manifest.json 로드 실패</p>';
    return;
  }
  state.manifest = manifest;
  renderChunks(manifest);
  wireUI();

  detector = new ActiveChunkDetector({ dwellMs: 550 });
  Array.from(document.querySelectorAll('[data-chunk-id]')).forEach(el=>detector.observe(el));
  detector.onChange(onActiveChange);
}

function renderChunks(manifest){
  document.title = `${manifest.title} — Reading BGM`;
  const tpl = document.getElementById('chunk-template');
  ui.reader.innerHTML = '';
  manifest.chunks.forEach((c, idx)=>{
    const node = tpl.content.firstElementChild.cloneNode(true);
    node.dataset.chunkId = c.id;
    node.querySelector('.chunk-title').textContent = c.title || `청크 ${idx+1}`;
    node.querySelector('.chunk-text').textContent = c.text;
    ui.reader.appendChild(node);
  });
}

function wireUI(){
  ui.btnEnable.addEventListener('click', async()=>{
    await audio.unlock();
    state.audioEnabled = true;
    ui.btnEnable.textContent = '오디오 활성화됨';
    ui.btnEnable.disabled = true;

    // Preload current and neighbors if we already have an active
    const idx = currentIndex();
    if (idx >= 0) {
      audio.preloadNeighbors(mapAudioList(), idx);
      const ch = state.manifest.chunks[idx];
      audio.play(ch.id, ch.audioUrl, ch.fadeMs);
    }
  });

  ui.chkAuto.addEventListener('change', (e)=>{
    state.autoSwitch = e.target.checked;
    audio.setAutoSwitch(state.autoSwitch);
  });

  ui.rangeVol.addEventListener('input', (e)=>{
    audio.setVolume(parseFloat(e.target.value));
  });

  ui.btnMute.addEventListener('click', ()=>{
    audio.mute();
  });
}

function onActiveChange(id){
  const prev = state.activeId;
  state.activeId = id;
  highlightActive(prev, id);
  updateDebug();

  if (!state.audioEnabled) return; // wait until unlock
  if (!state.autoSwitch) return;

  const idx = currentIndex();
  if (idx < 0) return;
  const ch = state.manifest.chunks[idx];
  audio.preloadNeighbors(mapAudioList(), idx);
  audio.play(ch.id, ch.audioUrl, ch.fadeMs);
}

function currentIndex(){
  if (!state.manifest) return -1;
  return state.manifest.chunks.findIndex(c=>c.id === state.activeId);
}

function mapAudioList(){
  return state.manifest.chunks.map(c=>({ id: c.id, url: c.audioUrl }));
}

function highlightActive(prevId, nextId){
  if (prevId) {
    const prevEl = document.querySelector(`[data-chunk-id="${CSS.escape(prevId)}"]`);
    prevEl?.classList.remove('active');
  }
  if (nextId) {
    const el = document.querySelector(`[data-chunk-id="${CSS.escape(nextId)}"]`);
    el?.classList.add('active');
  }
}

function updateDebug(){
  if (!ui.dbg) return;
  ui.dbgActive.textContent = state.activeId || '-';
  // Optionally show more info; kept minimal here
}

