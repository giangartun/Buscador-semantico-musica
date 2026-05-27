'use client';

import { FormEvent } from 'react';

interface SearchBarProps {
  value: string;
  onValueChange: (value: string) => void;
  onSearch: (query: string) => void;
  onClearInput: () => void;
  placeholder?: string;
  isLoading?: boolean;
}

export default function SearchBar({
  value,
  onValueChange,
  onSearch,
  onClearInput,
  placeholder = 'Buscar...',
  isLoading = false,
}: SearchBarProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const termino = value.trim();

    if (termino && !isLoading) {
      onSearch(termino);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          placeholder={placeholder}
          className="w-full px-4 py-3 pr-24 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
        />

        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
          {value && (
            <button
              type="button"
              onClick={onClearInput}
              className="px-2 py-1 text-gray-400 hover:text-gray-600 text-sm"
              aria-label="Vaciar texto"
            >
              ✕
            </button>
          )}

          <button
            type="submit"
            disabled={!value.trim() || isLoading}
            className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400 text-sm font-medium transition"
          >
            {isLoading ? '...' : 'Buscar'}
          </button>
        </div>
      </div>
    </form>
  );
}