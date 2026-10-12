import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToastContext } from '@/context/ToastContext';
import { Button, ConfirmDialog, PageHeader, Pagination, Select } from '@/components/common';
import { CategoryFilter } from '@/components/products/CategoryFilter';
import { ProductFormModal } from '@/components/products/ProductFormModal';
import { ProductTable } from '@/components/products/ProductTable';
import { StockAdjustModal } from '@/components/products/StockAdjustModal';
import { adjustStock, createProduct, listProducts, removeProduct, updateProduct } from '@/api/product.api';
import { listCategories } from '@/api/category.api';
import { usePagination } from '@/hooks/usePagination';
import { useDisclosure } from '@/hooks/useDisclosure';
import { useDebounce } from '@/hooks/useDebounce';
import { PRODUCT_STATUS } from '@/lib/constants';

/**
 * Products listing page with search, filters, pagination, CRUD modals.
 * @returns {React.ReactElement}
 */
export function ProductsPage() {
  const toast = useToastContext();
  const qc = useQueryClient();
  const { page, limit, setPage, setLimit, setTotal } = usePagination();

  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 400);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [stockProduct, setStockProduct] = useState(null);
  const [deleteProduct, setDeleteProduct] = useState(null);

  const formModal = useDisclosure();
  const stockModal = useDisclosure();
  const deleteDialog = useDisclosure();

  const params = {
    search: debouncedSearch || undefined,
    category: categoryFilter || undefined,
    status: statusFilter || undefined,
    page,
    limit,
    sortBy: 'name',
    sortOrder: 'asc',
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['products', params],
    queryFn: () => listProducts(params),
    placeholderData: (prev) => prev,
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: listCategories,
  });

  const total = data?.total || 0;

  // Sync total into pagination
  useEffect(() => { setTotal(total); }, [total, setTotal]);

  const createMut = useMutation({
    mutationFn: (body) => createProduct(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['products'] });
      toast.addToast('Product created.', 'success');
      formModal.onClose();
    },
    onError: (err) => toast.addToast(err?.message || 'Failed to create product.', 'error'),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, body }) => updateProduct(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['products'] });
      toast.addToast('Product updated.', 'success');
      formModal.onClose();
      setSelectedProduct(null);
    },
    onError: (err) => toast.addToast(err?.message || 'Failed to update product.', 'error'),
  });

  const deleteMut = useMutation({
    mutationFn: (id) => removeProduct(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['products'] });
      toast.addToast('Product deleted.', 'success');
      deleteDialog.onClose();
      setDeleteProduct(null);
    },
    onError: (err) => toast.addToast(err?.message || 'Failed to delete product.', 'error'),
  });

  const stockMut = useMutation({
    mutationFn: ({ id, body }) => adjustStock(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['products'] });
      toast.addToast('Stock adjusted.', 'success');
      stockModal.onClose();
      setStockProduct(null);
    },
    onError: (err) => toast.addToast(err?.message || 'Failed to adjust stock.', 'error'),
  });

  function openEdit(product) {
    setSelectedProduct(product);
    formModal.onOpen();
  }

  function openCreate() {
    setSelectedProduct(null);
    formModal.onOpen();
  }

  async function handleFormSubmit(values) {
    if (selectedProduct) {
      await updateMut.mutateAsync({ id: selectedProduct.id, body: values });
    } else {
      await createMut.mutateAsync(values);
    }
  }

  async function handleStockSubmit(values) {
    await stockMut.mutateAsync({ id: stockProduct.id, body: values });
  }

  return (
    <div className="page">
      <PageHeader
        title="Products"
        actions={<Button onClick={openCreate}>+ New Product</Button>}
      />

      <div className="filters-bar">
        <input
          type="search"
          className="field__input"
          placeholder="Search by SKU or name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search products"
        />
        <CategoryFilter
          value={categoryFilter}
          onChange={setCategoryFilter}
          categories={categories}
        />
        <Select
          label="Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value={PRODUCT_STATUS.ACTIVE}>Active</option>
          <option value={PRODUCT_STATUS.INACTIVE}>Inactive</option>
          <option value={PRODUCT_STATUS.ARCHIVED}>Archived</option>
        </Select>
      </div>

      <ProductTable
        products={data?.items || []}
        isLoading={isLoading}
        isError={isError}
        onEdit={openEdit}
        onDelete={(p) => { setDeleteProduct(p); deleteDialog.onOpen(); }}
        onAdjustStock={(p) => { setStockProduct(p); stockModal.onOpen(); }}
        onRetry={refetch}
      />

      <Pagination
        page={page}
        totalPages={Math.max(1, Math.ceil(total / limit))}
        total={total}
        limit={limit}
        onPageChange={setPage}
        onLimitChange={setLimit}
      />

      <ProductFormModal
        isOpen={formModal.isOpen}
        onClose={formModal.onClose}
        onSubmit={handleFormSubmit}
        product={selectedProduct}
        categories={categories}
        loading={createMut.isPending || updateMut.isPending}
      />

      {stockProduct && (
        <StockAdjustModal
          isOpen={stockModal.isOpen}
          onClose={stockModal.onClose}
          onSubmit={handleStockSubmit}
          product={stockProduct}
          loading={stockMut.isPending}
        />
      )}

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={deleteDialog.onClose}
        onConfirm={() => deleteProduct && deleteMut.mutate(deleteProduct.id)}
        title="Delete Product"
        message={`Are you sure you want to delete "${deleteProduct?.name}"? This action cannot be undone.`}
        loading={deleteMut.isPending}
      />
    </div>
  );
}
