import { useState, useCallback } from 'react'

export function useCommandPalette() {
  const [open, setOpen] = useState(false)
  const toggle = useCallback(() => setOpen((v) => !v), [])
  return { open, setOpen, toggle }
}
