interface ViralScoreRingProps {
  value?: number
  size?: number
  stroke?: number
}

export function ViralScoreRing({ value = 0, size = 80, stroke = 6 }: ViralScoreRingProps) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c - (Math.min(value, 100) / 100) * c

  const getColor = (v: number) => {
    if (v >= 80) return '#16a34a' // success
    if (v >= 60) return '#d97706' // warning
    return '#dc2626' // destructive
  }

  const color = getColor(value)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-foreground leading-none">{value}</span>
        <span className="text-[9px] text-muted-foreground">分</span>
      </div>
    </div>
  )
}
