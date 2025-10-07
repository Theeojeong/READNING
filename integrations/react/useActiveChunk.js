import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

// React hook: detect active chunk while reading (IntersectionObserver + dwell time)
// Usage:
// const { activeId, registerChunkRef } = useActiveChunk({ dwellMs: 550 });
// <section ref={registerChunkRef(chunk.id)}> ... </section>

export function useActiveChunk({ dwellMs = 550, root = null, rootMargin = '0px', thresholds = [0, 0.25, 0.5, 0.75, 1] } = {}) {
  const [activeId, setActiveId] = useState(null);
  const visibilityRef = useRef(new Map()); // id -> ratio
  const topRef = useRef(new Map()); // id -> proximity score helper
  const candidateRef = useRef({ id: null, since: 0 });
  const nodesRef = useRef(new Map()); // id -> element
  const ioRef = useRef(null);

  const measureRect = useCallback((id, el) => {
    if (!el) return;
    const r = el.getBoundingClientRect();
    const delta = Math.abs(r.top - window.innerHeight * 0.2);
    topRef.current.set(id, delta);
  }, []);

  const recompute = useCallback(() => {
    const now = performance.now();
    let bestId = null;
    let bestScore = -1;
    const vis = visibilityRef.current;
    const tops = topRef.current;
    const viewportRef = window.innerHeight * 0.2 + 1;
    for (const [id, ratio] of vis.entries()) {
      const d = tops.get(id) ?? 1e9;
      const prox = Math.max(0, 1 - Math.min(1, d / viewportRef));
      const score = ratio * 0.7 + prox * 0.3;
      if (score > bestScore) { bestScore = score; bestId = id; }
    }
    if (!bestId) return;
    if (candidateRef.current.id !== bestId) {
      candidateRef.current = { id: bestId, since: now };
    }
    const stable = now - candidateRef.current.since >= dwellMs;
    if (stable && activeId !== candidateRef.current.id) {
      setActiveId(candidateRef.current.id);
    }
  }, [activeId, dwellMs]);

  useEffect(() => {
    const handleScroll = () => {
      for (const [id, el] of nodesRef.current.entries()) measureRect(id, el);
      recompute();
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, [measureRect, recompute]);

  useEffect(() => {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        const id = e.target?.dataset?.chunkId;
        if (!id) continue;
        visibilityRef.current.set(id, e.intersectionRatio || 0);
        measureRect(id, e.target);
      }
      recompute();
    }, { root, rootMargin, threshold: thresholds });
    ioRef.current = io;
    for (const [, el] of nodesRef.current.entries()) io.observe(el);
    return () => { io.disconnect(); ioRef.current = null; };
  }, [root, rootMargin, thresholds, measureRect, recompute]);

  const registerChunkRef = useCallback((id) => (el) => {
    if (el) {
      nodesRef.current.set(id, el);
      el.dataset.chunkId = id;
      ioRef.current?.observe(el);
      measureRect(id, el);
    } else {
      const prev = nodesRef.current.get(id);
      if (prev) ioRef.current?.unobserve(prev);
      nodesRef.current.delete(id);
      visibilityRef.current.delete(id);
      topRef.current.delete(id);
    }
  }, [measureRect]);

  return useMemo(() => ({ activeId, registerChunkRef }), [activeId, registerChunkRef]);
}

