import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'

interface EmotionPoint {
  segment: number
  emotion: string
  intensity: number
}

interface EmotionCurveChartProps {
  data?: EmotionPoint[]
}

export function EmotionCurveChart({ data = [] }: EmotionCurveChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-24 flex items-center justify-center text-xs text-muted-foreground bg-secondary/30 rounded-lg">
        暂无情绪曲线数据
      </div>
    )
  }

  const chartData = data.map((d, i) => ({
    name: `段落${i + 1}`,
    intensity: Math.round(d.intensity * 100),
    emotion: d.emotion,
  }))

  return (
    <div className="h-24 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: -20 }}>
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              fontSize: 11,
              borderRadius: 8,
              border: '1px solid #e5e7eb',
              background: '#fff',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            }}
            formatter={(value, _name, props) => {
              const emotion = (props as { payload?: { emotion?: string } })?.payload?.emotion || ''
              return [`${value}%`, emotion]
            }}
          />
          <Line
            type="monotone"
            dataKey="intensity"
            stroke="#7c3aed"
            strokeWidth={2}
            dot={{ r: 3, fill: '#7c3aed', strokeWidth: 0 }}
            activeDot={{ r: 5, fill: '#7c3aed', stroke: '#fff', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
