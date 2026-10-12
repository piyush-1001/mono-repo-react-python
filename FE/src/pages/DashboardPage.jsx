import { useQuery } from '@tanstack/react-query';
import { listProducts } from '@/api/product.api';
import { PageHeader } from '@/components/common';
import { ProductStatsCards } from '@/components/products/ProductStatsCards';
import { ProductTable } from '@/components/products/ProductTable';
import { formatCurrency } from '@/lib/format';

/**
 * Dashboard overview page.
 * @returns {React.ReactElement}
 */
export function DashboardPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['dashboard-products'],
    queryFn: () => listProducts({ limit: 5 }),
  });

  const products = data?.items || [];

  const totalValue = products.reduce((sum, p) => sum + (p.price * p.stock), 0);
  const lowStockCount = products.filter((p) => p.stock <= p.reorderLevel).length;
  const activeCount = products.filter((p) => p.status === 'ACTIVE').length;

  return (
    <div className="page">
      <PageHeader title="Dashboard" subtitle="Inventory overview" />

      <ProductStatsCards
        totalProducts={data?.total || 0}
        totalValue={totalValue}
        lowStockCount={lowStockCount}
        activeProducts={activeCount}
      />

      <section className="page__section">
        <h2 className="section-title">Low Stock Alerts</h2>
        <ProductTable
          products={products.filter((p) => p.stock <= p.reorderLevel)}
          isLoading={isLoading}
          isError={isError}
          onEdit={() => {}}
          onDelete={() => {}}
          onAdjustStock={() => {}}
          onRetry={refetch}
        />
      </section>
    </div>
  );
}
