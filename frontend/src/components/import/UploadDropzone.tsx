import { useState, useRef } from "react"
import type { DragEvent, ChangeEvent } from "react"
import { Upload } from "lucide-react"

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void
  onError: (msg: string) => void
}

export function UploadDropzone({ onFileSelected, onError }: UploadDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true)
    } else if (e.type === "dragleave") {
      setIsDragActive(false)
    }
  }

  const validateAndSelectFile = (file: File) => {
    const isCSV = file.name.toLowerCase().endsWith(".csv")
    const isPDF = file.name.toLowerCase().endsWith(".pdf")
    if (!isCSV && !isPDF) {
      onError("Invalid file type. Only CSV or PDF statement files are allowed.")
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      onError("File size exceeds 5MB limit. Please upload a smaller statement.")
      return
    }
    onFileSelected(file)
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelectFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0])
    }
  }

  const onButtonClick = () => {
    inputRef.current?.click()
  }

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={onButtonClick}
      className={`relative rounded-xl border-2 border-dashed p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 ${
        isDragActive
          ? "border-emerald-500 bg-emerald-500/5 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
          : "border-white/10 hover:border-white/20 hover:bg-white/[0.01]"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.pdf"
        className="hidden"
        onChange={handleChange}
      />
      <div className="rounded-full bg-white/5 p-4 mb-4 text-gray-400 group-hover:text-white transition-colors duration-300">
        <Upload className="h-6 w-6 animate-pulse text-emerald-400" />
      </div>
      
      <p className="text-sm font-medium text-white">
        Drag and drop your statement CSV/PDF here, or <span className="text-emerald-400 underline decoration-dotted">browse</span>
      </p>
      
      <p className="text-[10px] text-gray-500 mt-2 font-mono uppercase tracking-wider">
        CSV and PDF files up to 5MB are supported
      </p>
    </div>
  )
}
