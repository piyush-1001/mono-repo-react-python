import { Card } from '@/components/common';

/**
 * Dashboard stat cards for inventory overview.
 * @param {{ totalProducts: number, totalValue: number, lowStockCount: number, activeProducts: number }} props
 * @returns {React.ReactElement}
 */
export function ProductStatsCards({ totalProducts, totalValue, lowStockCount, activeProducts }) {
  const stats = [
    {
      label: 'Total Products',
      value: totalProducts ?? 0,
      icon: '&#128230;',
      color: 'var(--color-info)',
    },
    {
      label: 'Inventory Value',
      value: new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(totalValue ?? 0),
      icon: '&#128176;',
      color: 'var(--color-success)',
    },
    {
      label: 'Low Stock Items',
      value: lowStockCount ?? 0,
      icon: '&#9888;',
      color: lowStockCount > 0 ? 'var(--color-warning)' : 'var(--color-muted)',
    },
    {
      label: 'Active Products',
      value: activeProducts ?? 0,
      icon: '&#10004;',
      color: 'var(--color-success)',
    },
  ];

  return (
    <div className="stats-grid">
      {stats.map((s) => (
        <Card key={s.label} className="stat-card">
          <div className="stat-card__icon" style={{ color: s.color }} aria-hidden="true"
            dangerouslySetInnerHTML={{ __html: s.icon }} />
          <div className="stat-card__body">
            <span className="stat-card__value">{s.value}</span>
            <span className="stat-card__label">{s.label}</span>
          </div>
        </Card>
      ))}
    </div>
  );
}
