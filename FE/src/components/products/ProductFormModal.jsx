import { useState } from 'react';
import { Button, Modal } from '@/components/common';
import { ProductFormFields } from './ProductFormFields';

/**
 * Modal for creating or editing a product.
 * @param {{ isOpen: boolean, onClose: () => void, onSubmit: (data: object) => Promise<void>, product?: object | null, categories: Array, loading?: boolean }} props
 * @returns {React.ReactElement}
 */
export function ProductFormModal({ isOpen, onClose, onSubmit, product, categories, loading }) {
  const isEdit = !!product;
  const [values, setValues] = useState({});
  const [errors, setErrors] = useState({});

  function handleChange(e) {
    const { name, value, type } = e.target;
    setValues((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value,
    }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    await onSubmit(values);
  }

  const initialValues = isEdit
    ? {
        sku: product.sku,
        name: product.name,
        categoryId: product.category?.id || '',
        unit: product.unit,
        price: product.price,
        costPrice: product.costPrice,
        stock: product.stock,
        reorderLevel: product.reorderLevel,
        description: product.description || '',
      }
    : {
        sku: '', name: '', categoryId: '', unit: '', price: '', costPrice: '', stock: '', reorderLevel: '', description: '',
      };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Edit Product' : 'New Product'}
      size="lg"
    >
      <form onSubmit={handleSubmit} noValidate>
        <ProductFormFields
          values={isEdit ? initialValues : (Object.keys(values).length ? values : initialValues)}
          errors={errors}
          onChange={handleChange}
          categories={categories}
          disabled={loading}
        />
        <div className="modal__footer">
          <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            {isEdit ? 'Save Changes' : 'Create Product'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
