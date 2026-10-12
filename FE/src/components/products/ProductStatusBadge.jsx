import { Badge } from '@/components/common';
import { PRODUCT_STATUS } from '@/lib/constants';

/**
 * Maps product status to badge variant.
 * @param {{ status: string }} props
 * @returns {React.ReactElement}
 */
export function ProductStatusBadge({ status }) {
  const variantMap = {
    [PRODUCT_STATUS.ACTIVE]: 'success',
    [PRODUCT_STATUS.INACTIVE]: 'warning',
    [PRODUCT_STATUS.ARCHIVED]: 'neutral',
  };
  return <Badge label={status} variant={variantMap[status] || 'neutral'} />;
}
