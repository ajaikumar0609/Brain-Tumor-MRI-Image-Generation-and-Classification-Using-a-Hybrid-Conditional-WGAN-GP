import { Link } from 'react-router-dom'
import { CheckCircle2, ImageIcon, Microscope, BarChart3, XCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Caveats, ErrorBox, Loading, PageHeader, pct } from '@/components/Common'
import { CandidateBar, PerClassBar } from '@/components/Charts'
import { api } from '@/lib/api'
import { useAsync } from '@/lib/useAsync'

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <Card><CardContent className="pt-6">
      <p className="text-muted-foreground text-xs font-medium uppercase tracking-wide">{label}</p>
      <p className="text-primary mt-1 text-3xl font-bold">{value}</p>
      <p className="text-muted-foreground mt-1 text-xs">{sub}</p>
    </CardContent></Card>
  )
}

export default function Dashboard() {
  const m = useAsync(api.metrics)
  const s = useAsync(api.status)
  const e = useAsync(api.experiment)
  const ci = m.data?.bootstrap_95ci
  return (
    <>
      <PageHeader title="SVM research dashboard" subtitle="Brain tumour MRI classification with HOG features and a Support Vector Machine on a leakage-aware, cluster-disjoint split. Every number below is read from the saved SVM result files." />
      {m.loading && <Loading label="Loading saved results" />}
      {m.error && <ErrorBox error={m.error} />}
      {m.data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Test accuracy" value={pct(m.data.accuracy)} sub={ci ? `95% bootstrap interval ${pct(ci.accuracy[0])} to ${pct(ci.accuracy[1])}` : ''} />
            <Stat label="Test macro-F1" value={m.data.macro_f1.toFixed(3)} sub={ci ? `95% interval ${ci.macro_f1[0].toFixed(3)} to ${ci.macro_f1[1].toFixed(3)}` : ''} />
            <Stat label="Selected model" value={`${m.data.model.kernel.toUpperCase()} SVM`} sub={`${m.data.model.hog_variant}, ${m.data.model.n_features} HOG features`} />
            <Stat label="Test set" value={`${m.data.n_test} images`} sub={`${m.data.tumour_vs_notumor.n_notumor} no-tumour; majority-class baseline ${pct(m.data.majority_class_baseline_accuracy)}`} />
          </div>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <Card><CardHeader><CardTitle>Model selection</CardTitle><CardDescription>Three HOG variants x two kernels; chosen on validation macro-F1 (test set not used).</CardDescription></CardHeader>
              <CardContent><CandidateBar rows={m.data.candidates} /></CardContent></Card>
            <Card><CardHeader><CardTitle>Per-class results on the test partition</CardTitle><CardDescription>Evaluated once with the frozen model.</CardDescription></CardHeader>
              <CardContent><PerClassBar m={m.data} /></CardContent></Card>
          </div>
        </>
      )}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card><CardHeader><CardTitle>Model readiness</CardTitle><CardDescription>Is a real, evaluated SVM behind the classifier page?</CardDescription></CardHeader>
          <CardContent className="space-y-2">
            {s.loading && <Loading />}
            {s.error && <ErrorBox error={s.error} />}
            {s.data && (
              <div className="flex items-start gap-3 rounded-lg border p-3">
                {s.data.classifier.available ? <CheckCircle2 className="text-accent mt-0.5 h-5 w-5 shrink-0" aria-label="available" /> : <XCircle className="text-destructive mt-0.5 h-5 w-5 shrink-0" aria-label="unavailable" />}
                <div><p className="text-sm font-medium">MRI classification (SVM)</p>
                  <p className="text-muted-foreground text-xs">{s.data.classifier.available ? `${s.data.classifier.kernel?.toUpperCase()} kernel, ${s.data.classifier.n_support_vectors} support vectors; file matches the model evaluated on the test partition` : (s.data.classifier.error ?? 'unavailable')}</p></div>
              </div>)}
          </CardContent></Card>
        <Card><CardHeader><CardTitle>Explore</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            {[{ to: '/classify', icon: Microscope, t: 'Classify an MRI', d: 'Upload an image; real SVM output.' },
              { to: '/results', icon: BarChart3, t: 'SVM results', d: 'Metrics, confusion matrix, selection.' },
              { to: '/gallery', icon: ImageIcon, t: 'Figures', d: 'Plots from the saved outputs.' }].map(({ to, icon: I, t, d }) => (
              <Link key={to} to={to} className="hover:border-accent hover:bg-secondary rounded-lg border p-3 transition-colors">
                <I className="text-accent mb-1 h-5 w-5" aria-hidden /><p className="text-sm font-semibold">{t}</p><p className="text-muted-foreground text-xs">{d}</p>
              </Link>))}
          </CardContent></Card>
      </div>
      {e.data && <div className="mt-6"><Caveats title="Limits to keep in mind" items={e.data.limitations} /></div>}
    </>
  )
}
