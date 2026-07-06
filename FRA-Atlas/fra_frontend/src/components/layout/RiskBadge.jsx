import { RISK_COLORS, RISK_BG, RISK_ICONS } from '../../data/constants';
export default function RiskBadge({ level, size = 'md' }) {
  const s = size === 'sm' ? { fontSize: '11px', padding: '2px 7px' } : { fontSize: '12px', padding: '3px 9px' };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: RISK_BG[level], color: RISK_COLORS[level],
      fontWeight: 700, borderRadius: 20, ...s,
    }}>
      {RISK_ICONS[level]} {level}
    </span>
  );
}
