// Typed client for the SVM FastAPI backend. In dev, /api is proxied to http://127.0.0.1:8000 (see vite.config.ts).
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

export class ApiError extends Error {
  status: number
  code: string
  detail?: string
  constructor(status: number, code: string, message: string, detail?: string) {
    super(message)
    this.status = status
    this.code = code
    this.detail = detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, init)
  } catch {
    throw new ApiError(0, 'network', 'Cannot reach the backend. Is it running on port 8000?')
  }
  const text = await res.text()
  let body: unknown = null
  try { body = text ? JSON.parse(text) : null } catch { /* non-JSON error body */ }
  if (!res.ok) {
    const e = (body as { error?: { code?: string; message?: string; detail?: string } } | null)?.error
    throw new ApiError(res.status, e?.code ?? 'http_error', e?.message ?? `Request failed (${res.status})`, e?.detail)
  }
  return body as T
}

export type ClassKey = 'glioma' | 'meningioma' | 'notumor' | 'pituitary'
export const CLASS_LABELS: Record<ClassKey, string> = { glioma: 'Glioma', meningioma: 'Meningioma', notumor: 'No tumour', pituitary: 'Pituitary tumour' }
export const CLASS_KEYS = Object.keys(CLASS_LABELS) as ClassKey[]

export interface ModelStatus {
  disclaimer: string
  classifier: {
    name: string; available: boolean; error: string | null; license: string; classes: ClassKey[]
    kernel?: string; hog_variant?: string; n_features?: number; image_size?: number; n_support_vectors?: number; model_sha256?: string; matches_evaluated_model?: boolean
    svc_params?: Record<string, unknown>
  }
  generator: { available: boolean; reason: string }
}
export interface PerClass { precision: number; recall: number; f1: number; support: number; sensitivity_ovr: number; specificity_ovr: number }
export interface Candidate { hog_variant: string; kernel: string; n_features: number; best_params: Record<string, unknown>; cv_macro_f1: number; cv_accuracy: number; val_macro_f1: number; val_accuracy: number }
export interface Metrics {
  n_test: number; classes: ClassKey[]
  model: { hog_variant: string; kernel: string; svc_params: Record<string, unknown>; n_features: number; image_size: number }
  accuracy: number; balanced_accuracy: number; macro_precision: number; macro_recall: number; macro_f1: number; weighted_f1: number
  per_class: Record<ClassKey, PerClass>
  confusion_matrix: { labels: ClassKey[]; counts: number[][] }
  tumour_vs_notumor: { sensitivity: number; specificity: number; n_tumour: number; n_notumor: number }
  bootstrap_95ci: { accuracy: [number, number]; macro_f1: [number, number] }
  majority_class_baseline_accuracy: number
  runtime_seconds: Record<string, number>
  candidates: Candidate[]; selected: Candidate; selection_rule: string
  sources: string[]; notes: string
}
export interface Experiment {
  title: string; status: string; method: string[]
  dataset: { description: string; provenance: string; split: string }
  limitations: string[]
  leakage_evidence: {
    clusters_spanning_more_than_one_partition: number; n_clusters_checked: number
    byte_identical_files_shared_between_partitions: Record<string, number>
    max_similarity_of_val_and_test_images_to_train_images: Record<string, { max_similarity_to_any_train_image: number }>
    caveat: string
  } | null
}
export interface ClassifyResult {
  predicted_class: ClassKey; predicted_label: string
  decision_scores: { class: ClassKey; label: string; score: number }[]
  margin_top1_minus_top2: number; model: string; kernel: string; input_size: [number, number]; inference_ms: number; disclaimer: string; caveats: string[]
}
export interface GalleryItem { id: string; title: string; kind: 'result' | 'data' | 'audit' | 'diagram'; note: string; url: string }

export const api = {
  health: () => request<{ status: string }>('/api/health'),
  status: () => request<ModelStatus>('/api/models/status'),
  metrics: () => request<Metrics>('/api/metrics'),
  experiment: () => request<Experiment>('/api/experiment'),
  gallery: () => request<{ items: GalleryItem[]; note: string }>('/api/gallery'),
  classify: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request<ClassifyResult>('/api/classify', { method: 'POST', body: fd })
  },
}
