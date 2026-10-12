import { Button } from './Button';
import { Modal } from './Modal';

/**
 * Confirmation dialog for destructive actions.
 * @param {{ isOpen: boolean, onClose: () => void, onConfirm: () => void, title: string, message: string, confirmLabel?: string, variant?: 'danger'|'secondary', loading?: boolean }} props
 * @returns {React.ReactElement}
 */
export function ConfirmDialog({
  isOpen, onClose, onConfirm, title, message, confirmLabel = 'Confirm', variant = 'danger', loading,
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <p className="confirm-dialog__message">{message}</p>
      <div className="confirm-dialog__actions">
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button variant={variant} onClick={onConfirm} loading={loading}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
