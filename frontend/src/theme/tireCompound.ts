/** Maps a tire compound string (any casing) to its colorblind-safe design
 * token, defined in index.css but intentionally NOT registered in the
 * Tailwind @theme block — consumers read it via inline style + var(), the
 * same pattern already used for team colors (see TeamTag.tsx). */
const TIRE_COLOR_VARS: Record<string, string> = {
  soft: 'var(--color-tire-soft)',
  medium: 'var(--color-tire-medium)',
  hard: 'var(--color-tire-hard)',
  intermediate: 'var(--color-tire-inter)',
  inter: 'var(--color-tire-inter)',
  wet: 'var(--color-tire-wet)',
}

export function tireCompoundColor(compound: string | null | undefined): string {
  if (!compound) return 'var(--color-steel)'
  return TIRE_COLOR_VARS[compound.toLowerCase()] ?? 'var(--color-steel)'
}

export function tireCompoundLabel(compound: string | null | undefined): string {
  if (!compound) return '—'
  return compound.slice(0, 3).toUpperCase()
}
