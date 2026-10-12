import { Link } from 'react-router-dom';
import { IconButton } from '@/components/common';
import { ProductStatusBadge } from './ProductStatusBadge';
import { StockLevelBar } from './StockLevelBar';
import { formatCurrency, formatDateTime } from '@/lib/format';

/**
 * Single product table row.
 * @param {{ product: object, onEdit: (p: object) => void, onDelete: (p: object) => void, onAdjustStock: (p: object) => void }} props
 * @returns {React.ReactElement}
 */
export function ProductRow({ product, onEdit, onDelete, onAdjustStock }) {
  return (
    <tr className="table__row">
      <td className="table__cell">
        <Link to={`/products/${product.id}`} className="product-row__sku">{product.sku}</Link>
      </td>
      <td className="table__cell">{product.name}</td>
      <td className="table__cell">{product.category?.name ?? '-'}</td>
      <td className="table__cell table__cell--right">{formatCurrency(product.price)}</td>
      <td className="table__cell table__cell--right">
        <StockLevelBar stock={product.stock} reorderLevel={product.reorderLevel} />
      </td>
      <td className="table__cell">
        <ProductStatusBadge status={product.status} />
      </td>
      <td className="table__cell table__cell--muted">{formatDateTime(product.updatedAt)}</td>
      <td className="table__cell table__cell--actions">
        <IconButton icon="&#9998;" label="Edit" onClick={() => onEdit(product)} />
        <IconButton icon="&#8634;" label="Adjust stock" onClick={() => onAdjustStock(product)} />
        <IconButton icon="&#128465;" label="Delete" variant="danger" onClick={() => onDelete(product)} />
      </td>
    </tr>
  );
}
