import { Input, Select, Textarea } from '@/components/common';

/**
 * Shared form fields for create/edit product.
 * @param {{ values: object, errors: object, onChange: (e: React.ChangeEvent) => void, categories: Array, disabled?: boolean }} props
 * @returns {React.ReactElement}
 */
export function ProductFormFields({ values, errors, onChange, categories, disabled }) {
  return (
    <div className="form-grid">
      <Input
        label="SKU"
        id="sku"
        name="sku"
        value={values.sku || ''}
        onChange={onChange}
        error={errors?.sku}
        required
        disabled={disabled}
      />
      <Input
        label="Name"
        id="name"
        name="name"
        value={values.name || ''}
        onChange={onChange}
        error={errors?.name}
        required
        disabled={disabled}
      />
      <Select
        label="Category"
        id="categoryId"
        name="categoryId"
        value={values.categoryId || ''}
        onChange={onChange}
        error={errors?.categoryId}
        required
        disabled={disabled}
      >
        <option value="">Select category</option>
        {categories.map((c) => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </Select>
      <Input
        label="Unit"
        id="unit"
        name="unit"
        value={values.unit || ''}
        placeholder="e.g. pcs, kg, box"
        onChange={onChange}
        error={errors?.unit}
        required
        disabled={disabled}
      />
      <Input
        label="Selling Price"
        id="price"
        name="price"
        type="number"
        step="0.01"
        min="0"
        value={values.price ?? ''}
        onChange={onChange}
        error={errors?.price}
        required
        disabled={disabled}
      />
      <Input
        label="Cost Price"
        id="costPrice"
        name="costPrice"
        type="number"
        step="0.01"
        min="0"
        value={values.costPrice ?? ''}
        onChange={onChange}
        error={errors?.costPrice}
        disabled={disabled}
      />
      <Input
        label="Current Stock"
        id="stock"
        name="stock"
        type="number"
        min="0"
        value={values.stock ?? ''}
        onChange={onChange}
        error={errors?.stock}
        disabled={disabled}
      />
      <Input
        label="Reorder Level"
        id="reorderLevel"
        name="reorderLevel"
        type="number"
        min="0"
        value={values.reorderLevel ?? ''}
        onChange={onChange}
        error={errors?.reorderLevel}
        disabled={disabled}
      />
      <div className="form-grid__full">
        <Textarea
          label="Description"
          id="description"
          name="description"
          value={values.description || ''}
          onChange={onChange}
          rows={3}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
