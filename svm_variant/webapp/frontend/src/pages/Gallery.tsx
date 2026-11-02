import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ErrorBox, Loading, PageHeader } from '@/components/Common'
import { api, type GalleryItem } from '@/lib/api'
import { useAsync } from '@/lib/useAsync'

const KIND: Record<GalleryItem['kind'], string> = { result: 'RESULT (from saved predictions)', data: 'DATASET IMAGES', audit: 'SPLIT AUDIT', diagram: 'DIAGRAM' }

export default function Gallery() {
  const g = useAsync(api.gallery)
  return (
    <>
      <PageHeader title="Figures" subtitle="Plots generated from the saved SVM outputs and the dataset." />
      {g.loading && <Loading />}
      {g.error && <ErrorBox error={g.error} />}
      {g.data && g.data.items.length === 0 && <p className="text-muted-foreground text-sm">No figures were found.</p>}
      <div className="grid gap-4 md:grid-cols-2">
        {g.data?.items.map((it) => (
          <Card key={it.id}>
            <CardHeader>
              <Badge className="w-fit" variant="outline">{KIND[it.kind]}</Badge>
              <CardTitle className="text-base">{it.title}</CardTitle>
              <CardDescription>{it.note}</CardDescription>
            </CardHeader>
            <CardContent><a href={it.url} target="_blank" rel="noreferrer"><img src={it.url} alt={it.title} loading="lazy" className="w-full rounded border bg-white" /></a></CardContent>
          </Card>))}
      </div>
      {g.data && <p className="text-muted-foreground mt-4 text-xs">{g.data.note}</p>}
    </>
  )
}
