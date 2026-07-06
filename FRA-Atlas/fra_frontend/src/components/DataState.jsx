// Small presentational helpers for loading and live/bundled data status.
export function Loading({ label = 'Loading live data…' }) {
  return (
    <div className="data-loading" role="status" aria-live="polite">
      <span className="data-spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function SourceBanner({ source, error }) {
  if (source !== 'bundled') return null;
  return (
    <div className="data-banner" role="status">
      Showing bundled reference data — the live API was unreachable
      {error ? ` (${error})` : ''}. Figures update once the backend is connected.
    </div>
  );
}
