import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePagination } from '@/hooks/usePagination';

describe('usePagination', () => {
  it('initializes with default page=1 and limit=20', () => {
    const { result } = renderHook(() => usePagination());
    expect(result.current.page).toBe(1);
    expect(result.current.limit).toBe(20);
  });

  it('accepts custom initial values', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 3, initialLimit: 50 }));
    expect(result.current.page).toBe(3);
    expect(result.current.limit).toBe(50);
  });

  it('computes totalPages correctly', () => {
    const { result } = renderHook(() => usePagination());
    act(() => result.current.setTotal(95));
    expect(result.current.totalPages).toBe(5); // ceil(95/20)
  });

  it('totalPages is at least 1', () => {
    const { result } = renderHook(() => usePagination({ total: 0 }));
    expect(result.current.totalPages).toBe(1);
  });

  it('canNext is false on the last page', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 1 }));
    act(() => result.current.setTotal(10));
    expect(result.current.canNext).toBe(false);
  });

  it('canPrev is false on page 1', () => {
    const { result } = renderHook(() => usePagination());
    expect(result.current.canPrev).toBe(false);
  });

  it('nextPage increments page when can next', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 1 }));
    act(() => result.current.setTotal(50));
    act(() => result.current.nextPage());
    expect(result.current.page).toBe(2);
  });

  it('nextPage does nothing when already on last page', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 3 }));
    act(() => result.current.setTotal(50)); // 3 pages total
    act(() => result.current.nextPage());
    expect(result.current.page).toBe(3);
  });

  it('prevPage decrements page', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 2 }));
    act(() => result.current.setTotal(50));
    act(() => result.current.prevPage());
    expect(result.current.page).toBe(1);
  });

  it('prevPage does nothing on page 1', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 1 }));
    act(() => result.current.prevPage());
    expect(result.current.page).toBe(1);
  });

  it('setPage jumps to arbitrary page', () => {
    const { result } = renderHook(() => usePagination());
    act(() => result.current.setTotal(100));
    act(() => result.current.setPage(4));
    expect(result.current.page).toBe(4);
  });

  it('setLimit resets to page 1', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 3 }));
    act(() => result.current.setLimit(50));
    expect(result.current.page).toBe(1);
    expect(result.current.limit).toBe(50);
  });

  it('reset restores initial values', () => {
    const { result } = renderHook(() => usePagination({ initialPage: 2 }));
    act(() => result.current.setTotal(50));
    act(() => result.current.setPage(3));
    act(() => result.current.reset());
    expect(result.current.page).toBe(2);
    expect(result.current.total).toBe(0);
  });
});
