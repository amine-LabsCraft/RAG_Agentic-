import { useAuth } from '@/hooks/useAuth'
import { useRealtimeDocuments } from '@/hooks/useRealtimeDocuments'
import { DocumentUpload } from '@/components/documents/DocumentUpload'
import { DocumentList } from '@/components/documents/DocumentList'
import { AppLayout } from '@/components/layout/AppLayout'

export function DocumentsPage() {
  const { user } = useAuth()
  const { documents, loading, refetch } = useRealtimeDocuments(user?.id)

  return (
    <AppLayout>
      {/* Main content */}
      <div className="h-full overflow-auto">
        <div className="max-w-3xl mx-auto p-8 space-y-8">
          <div>
            <h1 className="text-2xl font-bold">Documents</h1>
            <p className="text-muted-foreground mt-1">
              Upload documents to use as context in your chats.
            </p>
          </div>

          <DocumentUpload onUploadComplete={refetch} />
          <DocumentList documents={documents} loading={loading} />
        </div>
      </div>
    </AppLayout>
  )
}
