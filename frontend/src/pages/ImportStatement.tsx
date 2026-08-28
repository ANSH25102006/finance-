import { useState, useEffect } from "react"
import {
  FileSpreadsheet,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Database,
  ArrowRight,
  Plus
} from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"

import { Navbar } from "@/components/dashboard/Navbar"
import { UploadDropzone } from "@/components/import/UploadDropzone"
import { FileCard } from "@/components/import/FileCard"
import { PreviewTable } from "@/components/import/PreviewTable"
import { ImportStats } from "@/components/import/ImportStats"
import { getAccounts } from "@/services/accountService"
import { previewCSVImport, importCSVTransactions } from "@/services/importService"
import type { CSVPreviewResponse, CSVImportSummary } from "@/services/importService"
import { CreateAccountModal } from "@/components/import/CreateAccountModal"

export default function ImportStatement() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const [bankFormat, setBankFormat] = useState<string>("hdfc")
  const [file, setFile] = useState<File | null>(null)
  const [selectedAccountId, setSelectedAccountId] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const [previewData, setPreviewData] = useState<CSVPreviewResponse | null>(null)
  const [importSummary, setImportSummary] = useState<CSVImportSummary | null>(null)
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false)

  // 1. Fetch Accounts
  const { data: accounts = [] } = useQuery({
    queryKey: ["accounts"],
    queryFn: getAccounts,
  })

  // 2. Set default account when loaded
  useEffect(() => {
    if (accounts.length > 0 && !selectedAccountId) {
      setSelectedAccountId(accounts[0].id)
    }
  }, [accounts, selectedAccountId])

  // 3. Mutation for Database Insert
  const importMutation = useMutation({
    mutationFn: () => {
      if (!file || !selectedAccountId) {
        throw new Error("Please select a statement and destination account.")
      }
      return importCSVTransactions(file, bankFormat, selectedAccountId)
    },
    onSuccess: (summary) => {
      // Invalidate queries to trigger automated dashboard & cashflow refetches
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] })
      queryClient.invalidateQueries({ queryKey: ["analytics"] })

      setImportSummary(summary)
      // Reset temporary preview state
      setPreviewData(null)
      setErrorMsg(null)
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "An error occurred while importing transactions."
      setErrorMsg(msg)
    }
  })

  // Calculations for Stats
  const getPreviewStats = () => {
    if (!previewData) return { totalCount: 0, incomeTotal: 0, expenseTotal: 0 }

    let income = 0
    let expense = 0
    previewData.transactions.forEach((tx) => {
      if (tx.transaction_type === "income") {
        income += tx.amount
      } else {
        expense += tx.amount
      }
    })
    return {
      totalCount: previewData.transactions.length,
      incomeTotal: income,
      expenseTotal: expense
    }
  }

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    setErrorMsg(null)
    setPreviewData(null)
    setImportSummary(null)
  }

  const handleRemoveFile = () => {
    setFile(null)
    setErrorMsg(null)
    setPreviewData(null)
    setImportSummary(null)
  }

  const handlePreview = async () => {
    if (!file) return
    setLoading(true)
    setErrorMsg(null)
    setPreviewData(null)
    setImportSummary(null)

    try {
      const data = await previewCSVImport(file, bankFormat)
      setPreviewData(data)
    } catch (err: any) {
      const msg = err.response?.data?.detail || "An error occurred while parsing the CSV file."
      setErrorMsg(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleImport = () => {
    importMutation.mutate()
  }

  const handleResetWorkflow = () => {
    setFile(null)
    setPreviewData(null)
    setImportSummary(null)
    setErrorMsg(null)
  }

  const { totalCount, incomeTotal, expenseTotal } = getPreviewStats()

  return (
    <div className="relative min-h-screen bg-[#060709] text-white selection:bg-emerald-500/30 overflow-hidden">
      {/* Ambient backgrounds */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-900/5 mesh-blob" />
        <div className="absolute top-[30%] right-[-15%] w-[45%] h-[55%] rounded-full bg-cyan-900/5 mesh-blob" style={{ animationDelay: "-5s" }} />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] rounded-full bg-purple-900/5 mesh-blob" style={{ animationDelay: "-10s" }} />
        <div className="absolute inset-0 bg-noise" />
      </div>

      <Navbar />

      <main className="relative z-10 mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 pb-32 pt-28">

        {/* Header */}
        <div className="border-b border-white/5 pb-6">
          <h1 className="typo-display text-2xl font-bold">Import Statements</h1>
          <p className="typo-body text-gray-500 mt-1">Upload and merge statements into your database portfolio</p>
        </div>

        {/* 4. SUCCESS SCREEN */}
        {importSummary ? (
          <div className="max-w-2xl mx-auto mt-10 flex flex-col gap-6">
            <div className="os-card border border-emerald-500/25 bg-emerald-500/[0.02] p-8 flex flex-col items-center text-center">
              <div className="rounded-full bg-emerald-500/10 p-4 text-emerald-400 mb-4 animate-pulse">
                <CheckCircle className="h-10 w-10" />
              </div>
              <h2 className="text-xl font-bold text-white">Import Successful</h2>
              <p className="text-xs text-gray-400 mt-1 leading-normal max-w-sm">
                {importSummary.message} Duplicate transactions were automatically filtered to prevent double-logging.
              </p>

              {/* Stats grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full mt-8 border-t border-b border-white/5 py-6">
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Processed</span>
                  <p className="text-lg font-bold text-white font-mono mt-1">{importSummary.total_rows}</p>
                </div>
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Imported</span>
                  <p className="text-lg font-bold text-emerald-400 font-mono mt-1">{importSummary.imported}</p>
                </div>
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Duplicates</span>
                  <p className="text-lg font-bold text-amber-400 font-mono mt-1">{importSummary.duplicates}</p>
                </div>
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Failed</span>
                  <p className="text-lg font-bold text-red-400 font-mono mt-1">{importSummary.failed}</p>
                </div>
              </div>

              {/* CTA buttons */}
              <div className="flex flex-col sm:flex-row gap-3 w-full mt-8">
                <button
                  onClick={() => navigate("/transactions")}
                  className="h-10 flex-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 font-semibold text-xs text-black transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  View Transactions
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={handleResetWorkflow}
                  className="h-10 flex-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 font-semibold text-xs text-white transition-all cursor-pointer"
                >
                  Import Another File
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* WORKFLOW PANELS */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-6">

            {/* Left panel: Config Console */}
            <div className="lg:col-span-5 flex flex-col gap-6">

              <div className="os-card p-6 border border-white/5 flex flex-col gap-4">
                <h3 className="typo-heading text-sm font-semibold">Select Configuration</h3>
                {accounts.length === 0 ? (
                  <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 flex flex-col gap-3 text-amber-400 mt-2">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-5 w-5 shrink-0" />
                      <h4 className="text-xs font-semibold">No Accounts Available</h4>
                    </div>
                    <p className="text-[11px] text-amber-400/80 leading-relaxed">
                      You need a destination account to import transactions into. Please create an account to proceed.
                    </p>
                    <button
                      onClick={() => setIsAccountModalOpen(true)}
                      className="mt-2 h-8 rounded-lg bg-amber-500 hover:bg-amber-400 font-semibold text-[10px] text-black transition-all flex items-center justify-center gap-2 w-full"
                    >
                      <Plus className="h-3 w-3" />
                      Create Account
                    </button>
                  </div>
                ) : (
                  <>
                    {/* Format selection */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Bank Format</label>
                      <select
                        value={bankFormat}
                        onChange={(e) => setBankFormat(e.target.value)}
                        disabled={loading || importMutation.isPending}
                        className="h-10 rounded-lg bg-[#0c0e12] border border-white/5 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer disabled:opacity-50"
                      >
                        <option value="hdfc">HDFC Bank CSV Statement</option>
                        <option value="icici">ICICI Bank CSV Statement</option>
                        <option value="generic">Generic Transaction CSV</option>
                      </select>
                    </div>

                    {/* Account selection */}
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between">
                        <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Destination Account</label>
                        <button
                          onClick={() => setIsAccountModalOpen(true)}
                          className="text-[10px] text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors"
                        >
                          <Plus className="h-3 w-3" /> Add New
                        </button>
                      </div>
                      <select
                        value={selectedAccountId}
                        onChange={(e) => setSelectedAccountId(e.target.value)}
                        disabled={loading || importMutation.isPending}
                        className="h-10 rounded-lg bg-[#0c0e12] border border-white/5 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer disabled:opacity-50"
                      >
                        {accounts.map((acc) => (
                          <option key={acc.id} value={acc.id}>
                            {acc.name} (₹{acc.balance.toLocaleString()})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Dropzone or file card */}
                    <div className="mt-2">
                      {!file ? (
                        <UploadDropzone
                          onFileSelected={handleFileSelect}
                          onError={(msg) => setErrorMsg(msg)}
                        />
                      ) : (
                        <FileCard file={file} onRemove={handleRemoveFile} />
                      )}
                    </div>

                    {/* Action buttons */}
                    {file && (
                      <button
                        onClick={handlePreview}
                        disabled={loading || importMutation.isPending}
                        className="h-10 w-full rounded-lg bg-emerald-500 hover:bg-emerald-400 font-semibold text-xs text-black transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                      >
                        {loading ? (
                          <>
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            Parsing statement...
                          </>
                        ) : (
                          "Preview Transactions"
                        )}
                      </button>
                    )}
                  </>
                )}
              </div>

              {/* Error notifications */}
              {errorMsg && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 flex gap-3 text-red-400 animate-shake">
                  <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-semibold">Import Error</h4>
                    <p className="text-[10px] text-red-400/80 leading-normal mt-1">{errorMsg}</p>
                  </div>
                </div>
              )}

              {/* Import trigger panel */}
              {previewData && (
                <div className="os-card p-6 border border-emerald-500/20 bg-emerald-500/5 flex flex-col gap-4">
                  <div className="flex gap-3 text-emerald-400">
                    <CheckCircle className="h-5 w-5 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-semibold">Preview Loaded</h4>
                      <p className="text-[10px] text-emerald-400/80 leading-normal mt-1">
                        Review statement details before database persistence. Duplicate logic check is enabled.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleImport}
                    disabled={importMutation.isPending}
                    className="h-10 w-full rounded-lg bg-emerald-500 hover:bg-emerald-400 font-semibold text-xs text-black transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    {importMutation.isPending ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        Persisting transactions...
                      </>
                    ) : (
                      <>
                        <Database className="h-3.5 w-3.5" />
                        Import Transactions
                      </>
                    )}
                  </button>
                </div>
              )}

            </div>

            {/* Right panel: Preview ledger & statistics */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              {!previewData ? (
                <div className="os-card p-12 border border-white/5 flex flex-col items-center justify-center text-center h-[350px]">
                  <FileSpreadsheet className="h-12 w-12 text-gray-700 animate-bounce mb-4" />
                  <h3 className="text-sm font-semibold text-gray-400">No Statement Loaded</h3>
                  <p className="text-[11px] text-gray-500 max-w-[280px] mt-1.5">
                    Select a bank configuration, choose a destination account, and upload a CSV file.
                  </p>
                </div>
              ) : (
                <>
                  <ImportStats
                    totalCount={totalCount}
                    incomeTotal={incomeTotal}
                    expenseTotal={expenseTotal}
                  />

                  <div className="flex flex-col gap-3">
                    <h3 className="typo-subheading text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Normalized Transactions</h3>
                    <PreviewTable transactions={previewData.transactions} />
                  </div>
                </>
              )}
            </div>

          </div>
        )}

      </main>

      {isAccountModalOpen && (
        <CreateAccountModal onClose={() => setIsAccountModalOpen(false)} />
      )}
    </div>
  )
}
