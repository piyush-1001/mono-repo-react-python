import { EmptyState, ErrorState, Spinner } from '@/components/common';
import { ProductRow } from './ProductRow';

/**
 * Product data table.
 * @param {{ products: object[], isLoading: boolean, isError: boolean, onEdit: (p: object) => void, onDelete: (p: object) => void, onAdjustStock: (p: object) => void, onRetry?: () => void }} props
 * @returns {React.ReactElement}
 */
export function ProductTable({ products, isLoading, isError, onEdit, onDelete, onAdjustStock, onRetry }) {
  if (isLoading) {
    return (
      <div className="table-wrap">
        <table className="table" aria-busy="true">
          <thead><tr><th>Loading…</th></tr></thead>
        </table>
        <div className="table-wrap__overlay"><Spinner /></div>
      </div>
    );
  }

  if (isError) return <ErrorState onRetry={onRetry} />;
  if (!products || products.length === 0) {
    return <EmptyState title="No products found" description="Try adjusting your search or filters." />;
  }

  return (
    <div className="table-wrap">
      <table className="table" aria-label="Products">
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Category</th>
            <th className="table__col--right">Price</th>
            <th>Stock</th>
            <th>Status</th>
            <th>Updated</th>
            <th className="table__col--actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <ProductRow
              key={p.id}
              product={p}
              onEdit={onEdit}
              onDelete={onDelete}
              onAdjustStock={onAdjustStock}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
