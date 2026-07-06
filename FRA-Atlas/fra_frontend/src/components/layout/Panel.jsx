export function Panel({ children, className = '' }) {
  return <div className={`panel ${className}`}>{children}</div>;
}
export function PanelHeader({ title, icon, actions, subtitle }) {
  return (
    <div className="panel-header">
      <div className="panel-title">
        {icon && <span className="panel-icon">{icon}</span>}
        {title}
        {subtitle && <span className="panel-subtitle">{subtitle}</span>}
      </div>
      {actions && <div className="panel-actions">{actions}</div>}
    </div>
  );
}
export function PanelBody({ children, noPad = false }) {
  return <div className={`panel-body${noPad ? ' no-pad' : ''}`}>{children}</div>;
}
