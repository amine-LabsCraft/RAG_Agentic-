import { useState, useRef } from 'react'
import { Send } from 'lucide-react'
import { ThreadList, ThreadListRef } from '@/components/chat/ThreadList'
import { ChatView } from '@/components/chat/ChatView'
import { AppLayout } from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { createThread } from '@/lib/api'

export function ChatPage() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [initialMessage, setInitialMessage] = useState<string | undefined>(undefined)
  const [welcomeInput, setWelcomeInput] = useState('')
  const [creating, setCreating] = useState(false)
  const threadListRef = useRef<ThreadListRef>(null)

  const handleThreadTitleUpdate = (threadId: string, title: string) => {
    threadListRef.current?.updateThreadTitle(threadId, title)
  }

  const handleSelectThread = (threadId: string | null) => {
    setSelectedThreadId(threadId)
    setInitialMessage(undefined)
  }

  const handleWelcomeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!welcomeInput.trim() || creating) return

    const message = welcomeInput.trim()
    setCreating(true)
    try {
      const newThread = await createThread()
      threadListRef.current?.addThread(newThread)
      setInitialMessage(message)
      setSelectedThreadId(newThread.id)
      setWelcomeInput('')
    } catch (error) {
      console.error('Failed to create thread:', error)
    } finally {
      setCreating(false)
    }
  }

  return (
    <AppLayout
      sidebar={
        <ThreadList
          ref={threadListRef}
          selectedThreadId={selectedThreadId}
          onSelectThread={handleSelectThread}
        />
      }
    >
      {/* Main content */}
      <div className="flex h-full min-h-0 flex-1 flex-col">
        {selectedThreadId ? (
          <ChatView
            threadId={selectedThreadId}
            onThreadTitleUpdate={handleThreadTitleUpdate}
            initialMessage={initialMessage}
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center">
            <h1 className="text-2xl font-medium mb-8">What can I help with?</h1>
            <form onSubmit={handleWelcomeSubmit} className="w-full max-w-2xl px-4">
              <div className="flex gap-2">
                <Input
                  value={welcomeInput}
                  onChange={(e) => setWelcomeInput(e.target.value)}
                  placeholder="Ask anything"
                  disabled={creating}
                  className="flex-1 rounded-full px-4"
                />
                <Button
                  type="submit"
                  size="icon"
                  className="rounded-full"
                  disabled={!welcomeInput.trim() || creating}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
