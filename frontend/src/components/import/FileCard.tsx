import { FileText, Trash2 } from "lucide-react"

interface FileCardProps {
  file: File
  onRemove: () => void
}

export function FileCard({ file, onRemove }: FileCardProps) {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">
          <FileText className="h-5 w-5" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-white truncate max-w-[240px] sm:max-w-[350px]" title={file.name}>
            {file.name}
          </h4>
          <p className="text-[10px] text-gray-500 font-mono mt-0.5">{formatSize(file.size)}</p>
        </div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove()
        }}
        className="rounded-lg p-2 text-gray-500 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200"
        title="Remove file"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  )
}
