import { useMemo, useState, useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { highlightCompliance } from '../../lib/compliance'
import { simpleMarkdown } from '../../lib/markdown'
import { Pencil, Check, X, Bold, Italic, List, ListOrdered, Heading1, Heading2, Quote, Code } from 'lucide-react'
import { Button } from '../ui/Button'

interface MarkdownBodyProps {
  body: string
  editable?: boolean
  onChange?: (body: string) => void
}

function isHtmlContent(text: string): boolean {
  return /<[a-z][\s\S]*>/i.test(text)
}

export function MarkdownBody({ body, editable = false, onChange }: MarkdownBodyProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(body || '')

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: '在此输入正文内容...',
      }),
    ],
    content: draft || '',
    onUpdate: ({ editor }) => {
      setDraft(editor.getHTML())
    },
  }, [])

  useEffect(() => {
    if (editor && isEditing) {
      editor.commands.setContent(body)
    }
  }, [isEditing, body, editor])

  useEffect(() => {
    if (!isEditing) return
    const id = requestAnimationFrame(() => setDraft(body))
    return () => cancelAnimationFrame(id)
  }, [isEditing, body])

  const { html: bodyHtml } = useMemo(() => highlightCompliance(body), [body])
  const bodyPreview = useMemo(() => {
    if (isHtmlContent(body)) {
      return body
    }
    return simpleMarkdown(bodyHtml)
  }, [body, bodyHtml])

  const startEdit = () => {
    setDraft(body)
    setIsEditing(true)
  }

  const commit = () => {
    if (draft !== body && onChange) {
      onChange(draft)
    }
    setIsEditing(false)
  }

  const cancel = () => {
    setDraft(body)
    setIsEditing(false)
  }

  return (
    <div className="relative">
      {editable && !isEditing && (
        <div className="absolute top-0 right-0 z-10">
          <Button size="sm" variant="ghost" onClick={startEdit} className="opacity-60 hover:opacity-100 transition-opacity">
            <Pencil className="w-3.5 h-3.5 mr-1" />
            编辑正文
          </Button>
        </div>
      )}

      {isEditing ? (
        <div className="space-y-2">
          <div className="border border-border rounded-lg overflow-hidden">
            {/* Toolbar */}
            <div className="flex items-center gap-1 px-2 py-1.5 border-b border-border bg-secondary/30">
              <ToolbarButton
                active={editor?.isActive('bold')}
                onClick={() => editor?.chain().focus().toggleBold().run()}
                icon={<Bold className="w-3.5 h-3.5" />}
                title="加粗"
              />
              <ToolbarButton
                active={editor?.isActive('italic')}
                onClick={() => editor?.chain().focus().toggleItalic().run()}
                icon={<Italic className="w-3.5 h-3.5" />}
                title="斜体"
              />
              <div className="w-px h-4 bg-border mx-1" />
              <ToolbarButton
                active={editor?.isActive('heading', { level: 1 })}
                onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}
                icon={<Heading1 className="w-3.5 h-3.5" />}
                title="标题1"
              />
              <ToolbarButton
                active={editor?.isActive('heading', { level: 2 })}
                onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
                icon={<Heading2 className="w-3.5 h-3.5" />}
                title="标题2"
              />
              <div className="w-px h-4 bg-border mx-1" />
              <ToolbarButton
                active={editor?.isActive('bulletList')}
                onClick={() => editor?.chain().focus().toggleBulletList().run()}
                icon={<List className="w-3.5 h-3.5" />}
                title="无序列表"
              />
              <ToolbarButton
                active={editor?.isActive('orderedList')}
                onClick={() => editor?.chain().focus().toggleOrderedList().run()}
                icon={<ListOrdered className="w-3.5 h-3.5" />}
                title="有序列表"
              />
              <div className="w-px h-4 bg-border mx-1" />
              <ToolbarButton
                active={editor?.isActive('blockquote')}
                onClick={() => editor?.chain().focus().toggleBlockquote().run()}
                icon={<Quote className="w-3.5 h-3.5" />}
                title="引用"
              />
              <ToolbarButton
                active={editor?.isActive('code')}
                onClick={() => editor?.chain().focus().toggleCode().run()}
                icon={<Code className="w-3.5 h-3.5" />}
                title="行内代码"
              />
            </div>
            {/* Editor */}
            <EditorContent
              editor={editor}
              className="prose prose-sm max-w-none dark:prose-invert p-3 min-h-[200px] outline-none"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="ghost" onClick={cancel}>
              <X className="w-3.5 h-3.5 mr-1" />
              取消
            </Button>
            <Button size="sm" onClick={commit}>
              <Check className="w-3.5 h-3.5 mr-1" />
              保存
            </Button>
          </div>
        </div>
      ) : (
        <div
          className="text-sm leading-relaxed whitespace-pre-wrap prose prose-sm max-w-none dark:prose-invert"
          dangerouslySetInnerHTML={{ __html: bodyPreview }}
        />
      )}
    </div>
  )
}

function ToolbarButton({
  active,
  onClick,
  icon,
  title,
}: {
  active?: boolean
  onClick: () => void
  icon: React.ReactNode
  title: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`p-1 rounded transition-colors ${
        active
          ? 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
      }`}
    >
      {icon}
    </button>
  )
}
