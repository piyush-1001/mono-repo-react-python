/**
 * Visual bar showing stock level relative to reorder point.
 * @param {{ stock: number, reorderLevel: number, maxDisplay?: number }} props
 * @returns {React.ReactElement}
 */
export function StockLevelBar({ stock, reorderLevel, maxDisplay }) {
  const max = maxDisplay || Math.max(stock, reorderLevel * 2);
  const pct = Math.min(100, (stock / max) * 100);
  const reorderPct = (reorderLevel / max) * 100;
  const isLow = stock <= reorderLevel;

  return (
    <div className="stock-bar" aria-label={`Stock: ${stock}, reorder level: ${reorderLevel}`}>
      <div className="stock-bar__track">
        <div
          className={`stock-bar__fill ${isLow ? 'stock-bar__fill--low' : ''}`}
          style={{ width: `${pct}%` }}
        />
        <div
          className="stock-bar__reorder-line"
          style={{ left: `${reorderPct}%` }}
          aria-hidden="true"
          title={`Reorder level: ${reorderLevel}`}
        />
      </div>
      <span className={`stock-bar__label ${isLow ? 'stock-bar__label--low' : ''}`}>
        {stock}
      </span>
    </div>
  );
}
