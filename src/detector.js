// Active chunk detector using IntersectionObserver with dwell-time stabilization.

export class ActiveChunkDetector {
  constructor({ root = null, rootMargin = "0px", thresholds = [0, 0.25, 0.5, 0.75, 1], dwellMs = 500 } = {}) {
    this.visibility = new Map(); // id -> ratio
    this.rectTop = new Map(); // id -> top px (for tie-break)
    this.dwellMs = dwellMs;
    this._candidate = null;
    this._candidateSince = 0;
    this._active = null;
    this._listeners = new Set();

    this._observer = new IntersectionObserver(this._onIntersect.bind(this), {
      root,
      rootMargin,
      threshold: thresholds,
    });

    this._onScrollBound = this._onScroll.bind(this);
    window.addEventListener("scroll", this._onScrollBound, { passive: true });
    window.addEventListener("resize", this._onScrollBound);
  }

  observe(el) {
    const id = el.dataset.chunkId;
    if (!id) return;
    this._observer.observe(el);
    this._measureRect(el);
  }

  disconnect() {
    this._observer.disconnect();
    window.removeEventListener("scroll", this._onScrollBound);
    window.removeEventListener("resize", this._onScrollBound);
  }

  onChange(fn) { this._listeners.add(fn); return () => this._listeners.delete(fn); }

  getActive() { return this._active; }

  _onIntersect(entries) {
    for (const entry of entries) {
      const id = entry.target.dataset.chunkId;
      const ratio = entry.intersectionRatio || 0;
      this.visibility.set(id, ratio);
      this._measureRect(entry.target);
    }
    this._recomputeCandidate();
  }

  _onScroll() {
    // Rect top updates help tie-break by proximity to top.
    document.querySelectorAll('[data-chunk-id]').forEach((el)=>this._measureRect(el));
    this._recomputeCandidate();
  }

  _measureRect(el){
    const id = el.dataset.chunkId;
    const r = el.getBoundingClientRect();
    this.rectTop.set(id, Math.abs(r.top - window.innerHeight * 0.2)); // 20% from top sentinel
  }

  _recomputeCandidate(){
    const now = performance.now();
    let bestId = null;
    let bestScore = -1;

    for (const [id, ratio] of this.visibility.entries()) {
      const topDelta = this.rectTop.get(id) ?? 1e9;
      // Score combines visibility (weight 0.7) and proximity to sentinel (weight 0.3)
      const prox = Math.max(0, 1 - Math.min(1, topDelta / (window.innerHeight * 0.2 + 1)));
      const score = ratio * 0.7 + prox * 0.3;
      if (score > bestScore) {
        bestScore = score;
        bestId = id;
      }
    }

    if (!bestId) return;

    if (this._candidate !== bestId) {
      this._candidate = bestId;
      this._candidateSince = now;
    }

    const stable = now - this._candidateSince >= this.dwellMs;
    if (stable && this._active !== this._candidate) {
      this._active = this._candidate;
      for (const fn of this._listeners) fn(this._active);
    }
  }
}

