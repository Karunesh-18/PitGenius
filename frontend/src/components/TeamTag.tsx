interface TeamTagProps {
  name: string
  color?: string | null
}

export function TeamTag({ name, color }: TeamTagProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-steel text-[13px]">
      <span className="h-2 w-2 shrink-0" style={{ backgroundColor: color ?? '#4A5266' }} />
      {name}
    </span>
  )
}
