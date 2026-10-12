import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToastContext } from '@/context/ToastContext';
import { Button, Card, ErrorState, PageHeader, Spinner } from '@/components/common';
import { ProductStatusBadge } from '@/components/products/ProductStatusBadge';
import { StockLevelBar } from '@/components/products/StockLevelBar';
import { StockAdjustModal } from '@/components/products/StockAdjustModal';
import { adjustStock, getProduct } from '@/api/product.api';
import { formatCurrency, formatDateTime } from '@/lib/format';
import { useDisclosure } from '@/hooks/useDisclosure';

/**
 * Product detail page.
 * @returns {React.ReactElement}
 */
export function ProductDetailPage() {
  const { productId } = useParams();
  const toast = useToastContext();
  const qc = useQueryClient();
  const stockModal = useDisclosure();

  const { data: product, isLoading, isError, refetch } = useQuery({
    queryKey: ['product', productId],
    queryFn: () => getProduct(productId),
    enabled: !!productId,
  });

  const stockMut = useMutation({
    mutationFn: (body) => adjustStock(productId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['product', productId] });
      toast.addToast('Stock adjusted.', 'success');
      stockModal.onClose();
    },
    onError: (err) => toast.addToast(err?.message || 'Failed to adjust stock.', 'error'),
  });

  if (isLoading) return <div className="page-loader"><Spinner size="lg" /></div>;
  if (isError) return <ErrorState onRetry={refetch} />;
  if (!product) return null;

  const profit = product.price - (product.costPrice || 0);
  const margin = product.costPrice ? ((profit / product.costPrice) * 100).toFixed(1) : null;

  return (
    <div className="page">
      <PageHeader
        title={product.name}
        subtitle={`SKU: ${product.sku}`}
        breadcrumbs={[
          { label: 'Products', to: '/products' },
          { label: product.name },
        ]}
        actions={
          <Button variant="secondary" onClick={stockModal.onOpen}>
            Adjust Stock
          </Button>
        }
      />

      <div className="detail-grid">
        <Card title="Details">
          <dl className="detail-list">
            <div className="detail-list__row"><dt>Category</dt><dd>{product.category?.name ?? '-'}</dd></div>
            <div className="detail-list__row"><dt>Unit</dt><dd>{product.unit}</dd></div>
            <div className="detail-list__row"><dt>Status</dt><dd><ProductStatusBadge status={product.status} /></dd></div>
            <div className="detail-list__row"><dt>Created</dt><dd>{formatDateTime(product.createdAt)}</dd></div>
            <div className="detail-list__row"><dt>Updated</dt><dd>{formatDateTime(product.updatedAt)}</dd></div>
            {product.description && (
              <div className="detail-list__row detail-list__row--full"><dt>Description</dt><dd>{product.description}</dd></div>
            )}
          </dl>
        </Card>

        <Card title="Pricing">
          <dl className="detail-list">
            <div className="detail-list__row"><dt>Selling Price</dt><dd>{formatCurrency(product.price)}</dd></div>
            <div className="detail-list__row"><dt>Cost Price</dt><dd>{formatCurrency(product.costPrice)}</dd></div>
            <div className="detail-list__row"><dt>Profit</dt><dd>{formatCurrency(profit)}</dd></div>
            {margin && <div className="detail-list__row"><dt>Margin</dt><dd>{margin}%</dd></div>}
          </dl>
        </Card>

        <Card title="Stock">
          <dl className="detail-list">
            <div className="detail-list__row">
              <dt>Current Stock</dt>
              <dd>
                <StockLevelBar stock={product.stock} reorderLevel={product.reorderLevel} />
              </dd>
            </div>
            <div className="detail-list__row"><dt>Reorder Level</dt><dd>{product.reorderLevel}</dd></div>
            <div className="detail-list__row">
              <dt>Status</dt>
              <dd className={product.stock <= product.reorderLevel ? 'text-warning' : 'text-success'}>
                {product.stock <= product.reorderLevel ? 'Low stock' : 'In stock'}
              </dd>
            </div>
          </dl>
        </Card>
      </div>

      <StockAdjustModal
        isOpen={stockModal.isOpen}
        onClose={stockModal.onClose}
        onSubmit={(body) => stockMut.mutate(body)}
        product={product}
        loading={stockMut.isPending}
      />
    </div>
  );
}
