import { Select } from '@/components/common';

/**
 * Category filter dropdown.
 * @param {{ value: string, onChange: (v: string) => void, categories: Array }} props
 * @returns {React.ReactElement}
 */
export function CategoryFilter({ value, onChange, categories }) {
  return (
    <Select
      label="Category"
      id="category-filter"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">All categories</option>
      {categories.map((c) => (
        <option key={c.id} value={c.id}>{c.name}</option>
      ))}
    </Select>
  );
}
