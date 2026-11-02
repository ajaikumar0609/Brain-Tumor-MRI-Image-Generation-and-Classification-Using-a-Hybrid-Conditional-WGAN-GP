import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Caveats, ErrorBox, Loading, PageHeader, pct } from '@/components/Common'
import { CandidateBar, PerClassBar } from '@/components/Charts'
import { api, CLASS_KEYS, CLASS_LABELS } from '@/lib/api'
import { useAsync } from '@/lib/useAsync'

const th = 'px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide'
const td = 'px-3 py-2 text-sm'

export default function Results() {
  const m = useAsync(api.metrics)
  const e = useAsync(api.experiment)
  const cm = m.data?.confusion_matrix.counts
  const maxCell = cm ? Math.max(...cm.flat()) : 1
  return (
    <>
      <PageHeader title="SVM results" subtitle="Model selection used training cross-validation and the validation partition; the test partition was evaluated once with the frozen model. Values are read from the saved result files." />
      {(m.loading || e.loading) && <Loading />}
      {m.error && <ErrorBox error={m.error} />}
      {m.data && (<div className="space-y-6">
        <Card><CardHeader><CardTitle>Test-set metrics ({m.data.n_test} images)</CardTitle>
          <CardDescription>{m.data.model.kernel.toUpperCase()} SVM, {m.data.model.hog_variant}, {m.data.model.n_features} HOG features, parameters {JSON.stringify(m.data.model.svc_params)}.</CardDescription></CardHeader>
          <CardContent className="overflow-x-auto"><table className="w-full">
            <thead className="bg-primary text-primary-foreground"><tr><th className={th}>Metric</th><th className={th}>Value</th><th className={th}>95% bootstrap interval</th></tr></thead>
            <tbody>
              <tr className="bg-muted"><td className={td}>Accuracy</td><td className={td}>{m.data.accuracy.toFixed(3)}</td><td className={td}>{m.data.bootstrap_95ci.accuracy.map((x) => x.toFixed(3)).join(' to ')}</td></tr>
              <tr className="bg-card"><td className={td}>Macro precision</td><td className={td}>{m.data.macro_precision.toFixed(3)}</td><td className={td}>–</td></tr>
              <tr className="bg-muted"><td className={td}>Macro recall</td><td className={td}>{m.data.macro_recall.toFixed(3)}</td><td className={td}>–</td></tr>
              <tr className="bg-card"><td className={td}>Macro-F1</td><td className={td}>{m.data.macro_f1.toFixed(3)}</td><td className={td}>{m.data.bootstrap_95ci.macro_f1.map((x) => x.toFixed(3)).join(' to ')}</td></tr>
              <tr className="bg-muted"><td className={td}>Majority-class baseline accuracy</td><td className={td}>{pct(m.data.majority_class_baseline_accuracy)}</td><td className={td}>(always predict glioma)</td></tr>
            </tbody></table></CardContent></Card>
        <div className="grid gap-4 lg:grid-cols-2">
          <Card><CardHeader><CardTitle>Confusion matrix</CardTitle><CardDescription>Rows = true class, columns = predicted class (test counts).</CardDescription></CardHeader>
            <CardContent className="overflow-x-auto"><table className="w-full text-center" aria-label="Confusion matrix">
              <thead><tr><th className={th}></th>{CLASS_KEYS.map((k) => <th key={k} className={th}>{CLASS_LABELS[k]}</th>)}</tr></thead>
              <tbody>{CLASS_KEYS.map((r, i) => (<tr key={r}><th className={th}>{CLASS_LABELS[r]}</th>
                {CLASS_KEYS.map((_c, j) => <td key={j} className={td} style={{ background: `rgba(31,58,95,${(cm![i][j] / maxCell) * 0.85})`, color: cm![i][j] / maxCell > 0.45 ? '#fff' : '#14213d' }}>{cm![i][j]}</td>)}</tr>))}</tbody></table></CardContent></Card>
          <Card><CardHeader><CardTitle>Per-class results</CardTitle><CardDescription>Sensitivity/specificity are one-vs-rest values derived from the saved predictions.</CardDescription></CardHeader>
            <CardContent className="overflow-x-auto"><table className="w-full">
              <thead className="bg-primary text-primary-foreground"><tr><th className={th}>Class (n)</th><th className={th}>P</th><th className={th}>R</th><th className={th}>F1</th><th className={th}>Spec.</th></tr></thead>
              <tbody>{CLASS_KEYS.map((k, i) => { const c = m.data!.per_class[k]; return (<tr key={k} className={i % 2 ? 'bg-card' : 'bg-muted'}><td className={td}>{CLASS_LABELS[k]} ({c.support})</td><td className={td}>{c.precision.toFixed(2)}</td><td className={td}>{c.recall.toFixed(2)}</td><td className={td}>{c.f1.toFixed(2)}</td><td className={td}>{c.specificity_ovr.toFixed(2)}</td></tr>) })}</tbody></table>
              <p className="text-muted-foreground mt-3 text-xs">Tumour vs no-tumour (any of three tumour classes): sensitivity {m.data.tumour_vs_notumor.sensitivity.toFixed(3)}, specificity {m.data.tumour_vs_notumor.specificity.toFixed(3)} (specificity rests on only {m.data.tumour_vs_notumor.n_notumor} images).</p></CardContent></Card>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Card><CardHeader><CardTitle>Model selection</CardTitle><CardDescription>{m.data.selection_rule}</CardDescription></CardHeader><CardContent><CandidateBar rows={m.data.candidates} /></CardContent></Card>
          <Card><CardHeader><CardTitle>Per-class chart</CardTitle></CardHeader><CardContent><PerClassBar m={m.data} /></CardContent></Card>
        </div>
      </div>)}
      {e.error && <ErrorBox error={e.error} />}
      {e.data && (<div className="mt-6 space-y-6">
        <Card><CardHeader><CardTitle>Method and data</CardTitle></CardHeader><CardContent className="space-y-2 text-sm">
          <ol className="list-decimal space-y-1 pl-5">{e.data.method.map((x) => <li key={x}>{x}</li>)}</ol>
          <p>{e.data.dataset.description}</p><p>{e.data.dataset.split}</p><p><strong>Provenance:</strong> {e.data.dataset.provenance}</p>
          {e.data.leakage_evidence && <p><strong>Leakage checks:</strong> {e.data.leakage_evidence.clusters_spanning_more_than_one_partition} of {e.data.leakage_evidence.n_clusters_checked} clusters span more than one partition; byte-identical files shared between partitions: {Object.values(e.data.leakage_evidence.byte_identical_files_shared_between_partitions).reduce((a, b) => a + b, 0)}. {e.data.leakage_evidence.caveat}</p>}
        </CardContent></Card>
        <Caveats title="Limitations and caveats" items={e.data.limitations} />
      </div>)}
    </>
  )
}
