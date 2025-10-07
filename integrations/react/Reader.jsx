import React, { useMemo } from 'react';
import { useActiveChunk } from './useActiveChunk';
import { useAudioController } from './useAudioController';

// Example integration component for your existing React app.
// Props:
// - manifest: { title, chunks: [{ id, title?, text, audioUrl, fadeMs? }] }

export function Reader({ manifest }) {
  const { activeId, registerChunkRef } = useActiveChunk({ dwellMs: 550 });
  const audio = useAudioController({ defaultFadeMs: 600 });

  const audioList = useMemo(() => manifest.chunks.map(c => ({ id: c.id, url: c.audioUrl })), [manifest]);
  const activeIndex = useMemo(() => manifest.chunks.findIndex(c => c.id === activeId), [manifest, activeId]);

  React.useEffect(() => {
    if (!audio.enabled || !audio.autoSwitch) return;
    if (activeIndex < 0) return;
    const ch = manifest.chunks[activeIndex];
    audio.preloadNeighbors(audioList, activeIndex);
    audio.play({ id: ch.id, url: ch.audioUrl, fadeMs: ch.fadeMs });
  }, [activeIndex, audio, manifest, audioList]);

  return (
    <div className="reader-root">
      <div className="controls">
        <button onClick={audio.enable} disabled={audio.enabled}>오디오 활성화</button>
        <label>
          자동 전환
          <input type="checkbox" checked={audio.autoSwitch} onChange={e => audio.setAutoSwitch(e.target.checked)} />
        </label>
        <label>
          음량
          <input type="range" min={0} max={1} step={0.01} value={audio.volume} onChange={e => audio.setVolume(parseFloat(e.target.value))} />
        </label>
        <button onClick={audio.mute}>음소거</button>
      </div>

      <div className="chunks">
        {manifest.chunks.map((c, i) => (
          <section
            key={c.id}
            ref={registerChunkRef(c.id)}
            data-chunk-id={c.id}
            className={`chunk ${c.id === activeId ? 'active' : ''}`}
          >
            <h2>{c.title || `청크 ${i + 1}`}</h2>
            <p style={{ whiteSpace: 'pre-wrap' }}>{c.text}</p>
          </section>
        ))}
      </div>
    </div>
  );
}

