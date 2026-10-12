import { useCallback, useState } from 'react';

/**
 * Manages an open/closed boolean with helper toggles.
 * @param {boolean} [initialState]
 * @returns {{ isOpen: boolean, onOpen: () => void, onClose: () => void, onToggle: () => void }}
 */
export function useDisclosure(initialState = false) {
  const [isOpen, setIsOpen] = useState(initialState);

  const onOpen = useCallback(() => setIsOpen(true), []);
  const onClose = useCallback(() => setIsOpen(false), []);
  const onToggle = useCallback(() => setIsOpen((v) => !v), []);

  return { isOpen, onOpen, onClose, onToggle };
}
