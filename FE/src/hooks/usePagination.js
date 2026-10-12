import { useCallback, useMemo, useState } from 'react';
import { PAGINATION } from '@/lib/constants';

/**
 * Manages pagination state and helpers.
 * @param {{ initialPage?: number, initialLimit?: number, total?: number }} [options]
 * @returns {{ page: number, limit: number, totalPages: number, total: number, canNext: boolean, canPrev: boolean, nextPage: () => void, prevPage: () => void, setPage: (p: number) => void, setLimit: (l: number) => void, setTotal: (t: number) => void, reset: () => void }}
 */
export function usePagination(options = {}) {
  const {
    initialPage = PAGINATION.DEFAULT_PAGE,
    initialLimit = PAGINATION.DEFAULT_LIMIT,
    total: initialTotal = 0,
  } = options;

  const [page, setPage] = useState(initialPage);
  const [limit, setLimitState] = useState(initialLimit);
  const [total, setTotal] = useState(initialTotal);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / limit)), [total, limit]);
  const canNext = useMemo(() => page < totalPages, [page, totalPages]);
  const canPrev = useMemo(() => page > 1, [page]);

  const nextPage = useCallback(() => {
    if (canNext) setPage((p) => p + 1);
  }, [canNext]);

  const prevPage = useCallback(() => {
    if (canPrev) setPage((p) => p - 1);
  }, [canPrev]);

  const reset = useCallback(() => {
    setPage(initialPage);
    setTotal(initialTotal);
  }, [initialPage, initialTotal]);

  const setLimit = useCallback(
    (l) => {
      setLimitState(l);
      setPage(1);
    },
    [],
  );

  return {
    page,
    limit,
    totalPages,
    total,
    canNext,
    canPrev,
    nextPage,
    prevPage,
    setPage,
    setLimit,
    setTotal,
    reset,
  };
}
