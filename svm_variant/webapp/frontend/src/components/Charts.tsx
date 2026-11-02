import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Candidate, Metrics } from '@/lib/api'
import { CLASS_KEYS, CLASS_LABELS } from '@/lib/api'

const BLUE = '#3d73b8', TEAL = '#1f9e8f', ORANGE = '#c2651a'

export function CandidateBar({ rows }: { rows: Candidate[] }) {
  const data = rows.map((r) => ({ name: `${r.hog_variant.replace('hog', '').replace('_cell', 'px/c')} ${r.kernel === 'linear' ? 'lin' : 'rbf'}`, cv: r.cv_macro_f1, val: r.val_macro_f1 }))
  return (
    <figure aria-label="Cross-validation and validation macro-F1 of the six candidate models">
      <figcaption className="mb-2 text-sm font-medium">Model selection: macro-F1 of each candidate</figcaption>
      <ResponsiveContainer width="100%" height={290}>
        <BarChart data={data} margin={{ top: 16, right: 12, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
          <YAxis domain={[0.5, 1]} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v) => (typeof v === 'number' ? v.toFixed(3) : String(v))} />
          <Legend verticalAlign="top" />
          <Bar isAnimationActive={false} dataKey="cv" name="5-fold CV macro-F1 (training)" fill={BLUE} radius={[4, 4, 0, 0]} />
          <Bar isAnimationActive={false} dataKey="val" name="Validation macro-F1" fill={ORANGE} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </figure>
  )
}

export function PerClassBar({ m }: { m: Metrics }) {
  const data = CLASS_KEYS.map((k) => ({ name: CLASS_LABELS[k], precision: m.per_class[k].precision, recall: m.per_class[k].recall, f1: m.per_class[k].f1 }))
  return (
    <figure aria-label="Per-class precision, recall and F1 on the test partition">
      <figcaption className="mb-2 text-sm font-medium">Per-class precision, recall and F1 (test partition)</figcaption>
      <ResponsiveContainer width="100%" height={290}>
        <BarChart data={data} margin={{ top: 16, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v) => (typeof v === 'number' ? v.toFixed(3) : String(v))} />
          <Legend verticalAlign="top" />
          <Bar isAnimationActive={false} dataKey="precision" name="Precision" fill={BLUE} radius={[4, 4, 0, 0]} />
          <Bar isAnimationActive={false} dataKey="recall" name="Recall" fill={TEAL} radius={[4, 4, 0, 0]} />
          <Bar isAnimationActive={false} dataKey="f1" name="F1" fill={ORANGE} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </figure>
  )
}
