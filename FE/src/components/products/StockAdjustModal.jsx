import { useState } from 'react';
import { Button, Input, Modal, Select } from '@/components/common';
import { MOVEMENT_TYPE } from '@/lib/constants';

/**
 * Modal for recording a stock adjustment.
 * @param {{ isOpen: boolean, onClose: () => void, onSubmit: (data: object) => Promise<void>, product: object, loading?: boolean }} props
 * @returns {React.ReactElement}
 */
export function StockAdjustModal({ isOpen, onClose, onSubmit, product, loading }) {
  const [values, setValues] = useState({ quantity: '', movementType: MOVEMENT_TYPE.IN, reason: '' });
  const [errors, setErrors] = useState({});

  function handleChange(e) {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    await onSubmit({ ...values, quantity: Number(values.quantity) });
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Adjust Stock — ${product?.sku}`} size="sm">
      <form onSubmit={handleSubmit} noValidate>
        <div className="form-stack">
          <Select
            label="Movement Type"
            id="movementType"
            name="movementType"
            value={values.movementType}
            onChange={handleChange}
            disabled={loading}
            required
          >
            <option value={MOVEMENT_TYPE.IN}>Stock In (+)</option>
            <option value={MOVEMENT_TYPE.OUT}>Stock Out (-)</option>
            <option value={MOVEMENT_TYPE.ADJUST}>Adjust (set)</option>
          </Select>
          <Input
            label="Quantity"
            id="quantity"
            name="quantity"
            type="number"
            min="1"
            value={values.quantity}
            onChange={handleChange}
            error={errors?.quantity}
            required
            disabled={loading}
          />
          <Input
            label="Reason"
            id="reason"
            name="reason"
            value={values.reason}
            onChange={handleChange}
            placeholder="e.g. Received shipment, Damaged goods"
            disabled={loading}
          />
        </div>
        <div className="modal__footer">
          <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Record Adjustment
          </Button>
        </div>
      </form>
    </Modal>
  );
}
