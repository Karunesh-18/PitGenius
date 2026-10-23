import { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Panel } from './Panel'
import { ErrorState, LoadingState } from './StateViews'
import { useTireDegradationPrediction } from '../api/hooks'
import type { TireDegradationRequest } from '../api/types'

const COMPOUNDS: TireDegradationRequest['compound'][] = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']

export function TireDegradationPanel({ circuitRef }: { circuitRef: string }) {
  const [compound, setCompound] = useState<TireDegradationRequest['compound']>('MEDIUM')
  const [tyreLife, setTyreLife] = useState(15)
  // The slider tracks the drag immediately; the request only follows once the
  // value settles, so dragging 1 → 40 costs one SHAP inference instead of forty.
  const [committedTyreLife, setCommittedTyreLife] = useState(tyreLife)

  useEffect(() => {
    if (tyreLife === committedTyreLife) return
    const timer = setTimeout(() => setCommittedTyreLife(tyreLife), 250)
    return () => clearTimeout(timer)
  }, [tyreLife, committedTyreLife])

  const request: TireDegradationRequest = {
    circuit_ref: circuitRef,
    compound,
    tyre_life: committedTyreLife,
  }
  const prediction = useTireDegradationPrediction(request)
  const chartData = (prediction.data?.shap_contributions ?? []).map((c) => ({ name: c.feature, value: c.shap_value_s }))

  return (
    <Panel title="Tire Degradation">
      <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6">
        <div className="space-y-4 text-sm">
          <label className="block">
            <span className="text-steel text-xs block mb-1">Compound</span>
            <div className="grid grid-cols-3 gap-1.5">
              {COMPOUNDS.map((c) => (
                <button
                  key={c}
                  onClick={() => setCompound(c)}
                  className={`px-2 py-1.5 text-xs border ${
                    compound === c ? 'border-signal text-paper' : 'border-hairline text-steel'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </label>

          <label className="block">
            <span className="text-steel text-xs block mb-1">Tyre Life: {tyreLife} laps</span>
            <input
              type="range"
              min={1}
              max={40}
              value={tyreLife}
              onChange={(e) => setTyreLife(Number(e.target.value))}
              className="w-full accent-signal"
            />
          </label>

          {prediction.data && (
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">Predicted Lap</p>
                <p className="text-2xl font-900 tabular">{prediction.data.predicted_lap_time_s.toFixed(2)}s</p>
              </div>
              <div>
                <p className="text-[13px] text-steel tracking-[0.04em] uppercase mb-1">vs. Fresh</p>
                <p
                  className="text-2xl font-900 tabular"
                  style={{ color: prediction.data.degradation_vs_fresh_s >= 0 ? 'var(--color-signal)' : 'var(--color-green-best)' }}
                >
                  {prediction.data.degradation_vs_fresh_s >= 0 ? '+' : ''}
                  {prediction.data.degradation_vs_fresh_s.toFixed(2)}s
                </p>
              </div>
            </div>
          )}
        </div>

        <div>
          {prediction.isLoading && <LoadingState label="Predicting" />}
          {prediction.isError && <ErrorState message={(prediction.error as Error).message} />}
          {prediction.data && (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 12 }}>
                  <XAxis type="number" tick={{ fill: 'var(--color-steel)', fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={130} tick={{ fill: 'var(--color-steel)', fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: 'var(--color-graphite)', border: '1px solid var(--color-hairline)' }} />
                  <Bar dataKey="value">
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.value >= 0 ? 'var(--color-signal)' : 'var(--color-green-best)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="text-sm text-steel leading-relaxed mt-3">{prediction.data.explanation}</p>
            </>
          )}
        </div>
      </div>
    </Panel>
  )
}
