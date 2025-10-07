import { useCallback, useMemo, useRef, useState } from 'react';

// React hook wrapping Web Audio crossfade player.
// Returns control methods and state to play per-chunk BGM.

export function useAudioController({ defaultFadeMs = 600 } = {}) {
  const ctxRef = useRef(null);
  const masterRef = useRef(null);
  const tracksRef = useRef(new Map()); // id -> { buffer, gain, source, url }
  const currentIdRef = useRef(null);

  const [enabled, setEnabled] = useState(false);
  const [volume, setVol] = useState(0.7);
  const [autoSwitch, setAutoSwitch] = useState(true);

  const ensureContext = useCallback(async () => {
    if (!ctxRef.current) {
      ctxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      masterRef.current = ctxRef.current.createGain();
      masterRef.current.gain.value = volume;
      masterRef.current.connect(ctxRef.current.destination);
    }
    if (ctxRef.current.state === 'suspended') await ctxRef.current.resume();
  }, [volume]);

  const enable = useCallback(async () => {
    await ensureContext();
    setEnabled(true);
  }, [ensureContext]);

  const setVolume = useCallback((v) => {
    setVol(v);
    if (masterRef.current) rampGain(masterRef.current.gain, v, 150, ctxRef.current);
  }, []);

  const mute = useCallback(() => setVolume(0), [setVolume]);

  const ensureLoaded = useCallback(async (id, url) => {
    if (tracksRef.current.has(id) && tracksRef.current.get(id).buffer) return;
    if (!ctxRef.current) return;
    const res = await fetch(url);
    const arr = await res.arrayBuffer();
    const buf = await ctxRef.current.decodeAudioData(arr);
    const gain = ctxRef.current.createGain();
    gain.gain.value = 0;
    gain.connect(masterRef.current);
    tracksRef.current.set(id, { buffer: buf, gain, source: null, url });
  }, []);

  const play = useCallback(async ({ id, url, fadeMs }) => {
    if (!enabled) return;
    await ensureContext();
    await ensureLoaded(id, url);
    const ctx = ctxRef.current;
    const tr = tracksRef.current.get(id);
    if (!tr?.buffer) return;
    const src = ctx.createBufferSource();
    src.buffer = tr.buffer;
    src.loop = true;
    src.connect(tr.gain);
    src.start(0);
    tr.source = src;

    const prevId = currentIdRef.current;
    if (prevId && prevId !== id) {
      const prev = tracksRef.current.get(prevId);
      if (prev) {
        rampGain(prev.gain.gain, 0, fadeMs ?? defaultFadeMs, ctx);
        setTimeout(() => { try { prev.source?.stop(); } catch {} prev.source = null; }, (fadeMs ?? defaultFadeMs) + 30);
      }
    }
    rampGain(tr.gain.gain, 1, fadeMs ?? defaultFadeMs, ctx);
    currentIdRef.current = id;
  }, [enabled, ensureContext, ensureLoaded, defaultFadeMs]);

  const stopAll = useCallback((fadeMs = 300) => {
    const ctx = ctxRef.current; if (!ctx) return;
    for (const [, tr] of tracksRef.current) {
      rampGain(tr.gain.gain, 0, fadeMs, ctx);
      setTimeout(() => { try { tr.source?.stop(); } catch {} tr.source = null; }, fadeMs + 30);
    }
    currentIdRef.current = null;
  }, []);

  const preloadNeighbors = useCallback(async (list, activeIndex) => {
    if (!ctxRef.current) return;
    const indices = [activeIndex - 1, activeIndex, activeIndex + 1].filter(i => i >= 0 && i < list.length);
    await Promise.all(indices.map(i => ensureLoaded(list[i].id, list[i].url)));
  }, [ensureLoaded]);

  return useMemo(() => ({
    enabled,
    enable,
    volume,
    setVolume,
    mute,
    autoSwitch,
    setAutoSwitch,
    play,
    preloadNeighbors,
    stopAll,
  }), [enabled, enable, volume, setVolume, mute, autoSwitch, setAutoSwitch, play, preloadNeighbors, stopAll]);
}

function rampGain(param, target, ms, ctx) {
  const now = ctx.currentTime;
  param.cancelScheduledValues(now);
  param.setValueAtTime(param.value, now);
  param.linearRampToValueAtTime(target, now + ms / 1000);
}

