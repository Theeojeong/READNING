// Web Audio based controller with crossfade, preload neighbors, and unlock flow.

export class AudioController {
  constructor({ fadeMs = 600 } = {}) {
    this.ctx = null; // lazy until unlock
    this.master = null; // GainNode
    this.tracks = new Map(); // id -> { buffer, gain, source, state }
    this.currentId = null;
    this.fadeMs = fadeMs;
    this.enabled = false;
    this.volume = 0.7;
    this.autoSwitch = true;
  }

  async unlock() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') await this.ctx.resume();
    this.enabled = true;
  }

  setVolume(v){
    this.volume = v;
    if (this.master) this._rampGain(this.master.gain, v, 150);
  }

  setAutoSwitch(on){ this.autoSwitch = on; }

  mute(){ this.setVolume(0); }

  async ensureLoaded(id, url){
    if (this.tracks.has(id) && this.tracks.get(id).buffer) return;
    if (!this.ctx) return; // not unlocked yet; defer
    try {
      const res = await fetch(url);
      const arr = await res.arrayBuffer();
      const buf = await this.ctx.decodeAudioData(arr);
      const gain = this.ctx.createGain();
      gain.gain.value = 0;
      gain.connect(this.master);
      this.tracks.set(id, { buffer: buf, gain, source: null, state: 'stopped', url });
    } catch (e) {
      console.warn('Audio load failed', id, e);
    }
  }

  async play(id, url, fadeMsOverride){
    if (!this.enabled) return;
    if (!this.ctx) return;
    if (!this.tracks.has(id)) await this.ensureLoaded(id, url);
    const tr = this.tracks.get(id);
    if (!tr || !tr.buffer) return;

    const fadeMs = fadeMsOverride ?? this.fadeMs;

    // Start new source for this track (looping ambient by default)
    const src = this.ctx.createBufferSource();
    src.buffer = tr.buffer;
    src.loop = true;
    src.connect(tr.gain);
    src.start(0);
    tr.source = src;
    tr.state = 'playing';

    // Crossfade from currentId to this id
    if (this.currentId && this.currentId !== id) {
      const prev = this.tracks.get(this.currentId);
      if (prev) {
        this._rampGain(prev.gain.gain, 0, fadeMs);
        setTimeout(()=>{
          try { prev.source?.stop(); } catch {}
          prev.source = null;
          prev.state = 'stopped';
        }, fadeMs + 30);
      }
    }

    // Fade in new
    tr.gain.gain.cancelScheduledValues(this.ctx.currentTime);
    this._rampGain(tr.gain.gain, 1, fadeMs);
    this.currentId = id;
  }

  stopAll(fadeMs = 300){
    if (!this.ctx) return;
    for (const [id, tr] of this.tracks) {
      this._rampGain(tr.gain.gain, 0, fadeMs);
      setTimeout(()=>{ try { tr.source?.stop(); } catch{}; tr.source=null; tr.state='stopped'; }, fadeMs+30);
    }
    this.currentId = null;
  }

  // Preload neighbors: accepts array of {id, url} and active index
  async preloadNeighbors(list, activeIdx){
    if (!this.ctx) return;
    const ids = [activeIdx-1, activeIdx, activeIdx+1].filter(i=>i>=0 && i<list.length);
    await Promise.all(ids.map(i=>this.ensureLoaded(list[i].id, list[i].url)));
  }

  _rampGain(param, target, ms){
    const now = this.ctx.currentTime;
    param.cancelScheduledValues(now);
    param.setValueAtTime(param.value, now);
    param.linearRampToValueAtTime(target, now + ms/1000);
  }
}

