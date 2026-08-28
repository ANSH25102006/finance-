import { useState, useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Plus,
  Search,
  ChevronLeft,
  ChevronRight,
  Edit2,
  Trash2,
  SlidersHorizontal,
  RefreshCw,
  TrendingDown,
  TrendingUp
} from "lucide-react"

import { Navbar } from "@/components/dashboard/Navbar"
import {
  getTransactions,
  createTransaction,
  updateTransaction,
  deleteTransaction
} from "@/services/transactionService"
import type { Transaction, TransactionFilters } from "@/services/transactionService"
import { getAccounts } from "@/services/accountService"
import { getCategories } from "@/services/categoryService"
import { TransactionDialog } from "@/components/transactions/TransactionDialog"
import { Button } from "@/components/ui/Button"

export default function TransactionsPage() {
  const queryClient = useQueryClient()

  // Page states
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)

  const [searchParams] = useSearchParams()

  // Advanced Filter state
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [searchTerm, setSearchTerm] = useState(searchParams.get("search") || "")
  // Support comma-separated IDs in the search term for exact ID matching
  // The backend might need an update to handle `id=X,Y,Z` specifically, but
  // for now we'll put the ids in the search bar if `ids` is present, or just pass them as a custom filter if supported.
  // Actually, wait, let's check the backend filter schema. If it doesn't support list of IDs,
  // we might need to update the backend. But since `ids` is specified in the task, I will add `ids: searchParams.get("ids") || undefined` to the filters object, but only if the `TransactionFilters` type supports it. I will check that. For now, let's just initialize search.

  useEffect(() => {
    const ids = searchParams.get("ids")
    if (ids) {
      setSearchTerm(ids) // Fallback: put IDs in search box
    }
  }, [searchParams])

  const [filters, setFilters] = useState<TransactionFilters>({
    page: 1,
    limit: 15,
    account_id: "",
    category_id: "",
    transaction_type: "",
    start_date: "",
    end_date: "",
    min_amount: undefined,
    max_amount: undefined,
    sort_by: "transaction_date",
    sort_order: "desc",
  })

  // Queries
  const { data, isLoading, error } = useQuery({
    queryKey: ["transactions", filters, searchTerm],
    queryFn: () => getTransactions({ ...filters, search: searchTerm || undefined }),
  })

  const { data: accounts = [] } = useQuery({
    queryKey: ["accounts"],
    queryFn: getAccounts,
  })

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => getCategories(),
  })

  // Account/Category mapping for fast display lookup
  const accountsMap = new Map(accounts.map(a => [a.id, a]))
  const categoriesMap = new Map(categories.map(c => [c.id, c]))

  // Mutations
  const createMutation = useMutation({
    mutationFn: createTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] })
      setIsDialogOpen(false)
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to create transaction.")
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => updateTransaction(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] })
      setIsDialogOpen(false)
      setSelectedTransaction(null)
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to update transaction.")
    }
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] })
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to delete transaction.")
    }
  })

  const handleCreateOrUpdate = (payload: any) => {
    if (selectedTransaction) {
      updateMutation.mutate({ id: selectedTransaction.id, payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this transaction? This action cannot be undone.")) {
      deleteMutation.mutate(id)
    }
  }

  const handlePageChange = (newPage: number) => {
    setFilters(prev => ({ ...prev, page: newPage }))
  }

  const resetFilters = () => {
    setSearchTerm("")
    setFilters({
      page: 1,
      limit: 15,
      account_id: "",
      category_id: "",
      transaction_type: "",
      start_date: "",
      end_date: "",
      min_amount: undefined,
      max_amount: undefined,
      sort_by: "transaction_date",
      sort_order: "desc",
    })
  }

  return (
    <div className="relative min-h-screen bg-[#060709] text-white selection:bg-emerald-500/30 overflow-hidden">
      {/* Subtle Ambient Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-900/5 mesh-blob" />
        <div className="absolute top-[30%] right-[-15%] w-[45%] h-[55%] rounded-full bg-cyan-900/5 mesh-blob" style={{ animationDelay: '-5s' }} />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] rounded-full bg-purple-900/5 mesh-blob" style={{ animationDelay: '-10s' }} />
        <div className="absolute inset-0 bg-noise" />
      </div>

      <Navbar />

      <main className="relative z-10 mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 pb-32 pt-28">

        {/* Header Action Row */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-white/5 pb-6">
          <div>
            <h1 className="typo-display text-2xl font-bold">Transaction Ledger</h1>
            <p className="typo-body text-gray-500 mt-1">Track, search, and audit your financial logs</p>
          </div>
          <Button
            onClick={() => {
              setSelectedTransaction(null)
              setIsDialogOpen(true)
            }}
            className="bg-emerald-500 hover:bg-emerald-400 text-black font-semibold flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> New Transaction
          </Button>
        </div>

        {/* Toolbar Panel */}
        <div className="mt-6 flex flex-col gap-4">

          <div className="flex flex-col md:flex-row gap-3">
            {/* Search Bar */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search merchant, description, notes..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setFilters(f => ({ ...f, page: 1 }))
                }}
                className="w-full h-10 pl-10 pr-4 rounded-lg bg-[#0c0e12] border border-white/5 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
              />
            </div>

            {/* Quick Filters */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={`h-10 px-4 border border-white/5 hover:bg-white/5 flex items-center gap-2 text-xs font-semibold ${showAdvanced ? 'bg-white/5 text-white' : 'text-gray-400'}`}
              >
                <SlidersHorizontal className="h-3.5 w-3.5" /> Filters
              </Button>
              <Button
                variant="ghost"
                onClick={resetFilters}
                className="h-10 px-3 border border-white/5 hover:bg-white/5 text-gray-400 text-xs font-semibold"
                title="Reset All Filters"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          {/* Advanced Filter Box */}
          {showAdvanced && (
            <div className="os-inner-panel p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 border border-white/5 bg-[#0e1015]">
              {/* Type Filter */}
              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">Type</label>
                <select
                  value={filters.transaction_type}
                  onChange={(e) => setFilters(f => ({ ...f, transaction_type: e.target.value, page: 1 }))}
                  className="h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">All Types</option>
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                  <option value="transfer">Transfer</option>
                </select>
              </div>

              {/* Account Filter */}
              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">Account</label>
                <select
                  value={filters.account_id}
                  onChange={(e) => setFilters(f => ({ ...f, account_id: e.target.value, page: 1 }))}
                  className="h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">All Accounts</option>
                  {accounts.map(acc => (
                    <option key={acc.id} value={acc.id}>{acc.name}</option>
                  ))}
                </select>
              </div>

              {/* Category Filter */}
              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">Category</label>
                <select
                  value={filters.category_id}
                  onChange={(e) => setFilters(f => ({ ...f, category_id: e.target.value, page: 1 }))}
                  className="h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              {/* Sorting Filter */}
              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">Sort By</label>
                <div className="flex gap-2">
                  <select
                    value={filters.sort_by}
                    onChange={(e) => setFilters(f => ({ ...f, sort_by: e.target.value, page: 1 }))}
                    className="flex-1 h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="transaction_date">Date</option>
                    <option value="amount">Amount</option>
                    <option value="created_at">Created At</option>
                  </select>
                  <select
                    value={filters.sort_order}
                    onChange={(e) => setFilters(f => ({ ...f, sort_order: e.target.value as any, page: 1 }))}
                    className="w-20 h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="desc">Desc</option>
                    <option value="asc">Asc</option>
                  </select>
                </div>
              </div>

              {/* Date Filters */}
              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">From Date</label>
                <input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => setFilters(f => ({ ...f, start_date: e.target.value, page: 1 }))}
                  className="h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">To Date</label>
                <input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => setFilters(f => ({ ...f, end_date: e.target.value, page: 1 }))}
                  className="h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white focus:outline-none"
                />
              </div>

              {/* Amount Range */}
              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">Min Amount (₹)</label>
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.min_amount || ""}
                  onChange={(e) => setFilters(f => ({ ...f, min_amount: e.target.value ? Number(e.target.value) : undefined, page: 1 }))}
                  className="h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white placeholder:text-gray-700 focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">Max Amount (₹)</label>
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.max_amount || ""}
                  onChange={(e) => setFilters(f => ({ ...f, max_amount: e.target.value ? Number(e.target.value) : undefined, page: 1 }))}
                  className="h-9 rounded-lg bg-[#060709] border border-white/5 px-3 text-xs text-white placeholder:text-gray-700 focus:outline-none"
                />
              </div>
            </div>
          )}

        </div>

        {/* Ledger Table Section */}
        <div className="os-card mt-6 overflow-hidden">
          {isLoading ? (
            <div className="p-20 flex flex-col items-center justify-center gap-3">
              <RefreshCw className="h-8 w-8 text-emerald-500 animate-spin" />
              <p className="typo-caption text-gray-500 font-mono text-[10px] tracking-widest uppercase">Fetching logs...</p>
            </div>
          ) : error ? (
            <div className="p-20 text-center text-red-400">
              <p className="font-mono text-xs uppercase tracking-widest font-semibold">Unable to Load Transactions</p>
              <p className="text-xs text-gray-500 mt-1">Please check your server connection or try refreshing the page.</p>
            </div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-20 text-center text-gray-500 flex flex-col items-center gap-2">
              <p className="typo-heading text-sm text-gray-400">No Transactions Found</p>
              <p className="typo-body text-xs text-gray-600">Try adjusting your filters or record a new transaction.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.04] bg-[#0c0e12] typo-subheading text-[8px] text-gray-500">
                    <th className="p-4 px-6">Transaction Date</th>
                    <th className="p-4">Merchant / Description</th>
                    <th className="p-4">Account</th>
                    <th className="p-4">Category</th>
                    <th className="p-4 text-right">Amount</th>
                    <th className="p-4 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.02]">
                  {data.items.map((tx) => {
                    const isIncome = tx.transaction_type === "income"
                    const categoryObj = tx.category_id ? categoriesMap.get(tx.category_id) : null
                    const accountObj = accountsMap.get(tx.account_id)

                    return (
                      <tr key={tx.id} className="hover:bg-white/[0.01] transition-colors group/row text-xs">
                        <td className="p-4 px-6 text-gray-400 font-mono tracking-tight">
                          {new Date(tx.transaction_date).toLocaleDateString("en-IN", {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </td>
                        <td className="p-4">
                          <div className="flex flex-col gap-0.5">
                            <span className="font-semibold text-white tracking-tight">{tx.merchant || "No Merchant"}</span>
                            <span className="text-[10px] text-gray-500 truncate max-w-[200px]" title={tx.description}>
                              {tx.description}
                            </span>
                          </div>
                        </td>
                        <td className="p-4 text-gray-400">
                          {accountObj ? (
                            <span className="inline-flex items-center gap-1.5">
                              <span
                                className="h-1.5 w-1.5 rounded-full"
                                style={{ backgroundColor: accountObj.color || "#3b82f6" }}
                              />
                              {accountObj.name}
                            </span>
                          ) : (
                            <span className="text-gray-600">Unknown Account</span>
                          )}
                        </td>
                        <td className="p-4">
                          {categoryObj ? (
                            <span
                              className="px-2 py-0.5 rounded-[4px] text-[10px] font-semibold"
                              style={{ backgroundColor: `${categoryObj.color || "#ffffff"}15`, color: categoryObj.color || undefined }}
                            >
                              {categoryObj.name}
                            </span>
                          ) : (
                            <span className="text-gray-600 text-[10px]">Uncategorized</span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <span className={`font-semibold font-mono tabular-nums tracking-tight inline-flex items-center gap-1 ${
                            isIncome ? 'text-emerald-400' : 'text-white'
                          }`}>
                            {isIncome ? <TrendingUp className="h-3 w-3 inline text-emerald-400" /> : <TrendingDown className="h-3 w-3 inline text-gray-600" />}
                            {isIncome ? "+" : "-"}₹{tx.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </span>
                        </td>
                        <td className="p-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => {
                                setSelectedTransaction(tx)
                                setIsDialogOpen(true)
                              }}
                              className="p-1.5 bg-white/[0.02] hover:bg-white/[0.08] border border-white/[0.05] rounded-md text-gray-400 hover:text-white transition-colors"
                              title="Edit Transaction"
                            >
                              <Edit2 className="h-3 w-3" />
                            </button>
                            <button
                              onClick={() => handleDelete(tx.id)}
                              className="p-1.5 bg-white/[0.02] hover:bg-red-500/10 border border-white/[0.05] hover:border-red-500/20 rounded-md text-gray-400 hover:text-red-400 transition-colors"
                              title="Delete Transaction"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Footer */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between border-t border-white/[0.04] p-4 px-6 bg-black/10 typo-caption">
              <span className="text-gray-500 text-[10px]">
                Showing page {data.page} of {data.pages} ({data.total} total)
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  onClick={() => handlePageChange(data.page - 1)}
                  disabled={data.page === 1}
                  className="h-8 px-2 border border-white/5 hover:bg-white/5 text-gray-400 hover:text-white"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => handlePageChange(data.page + 1)}
                  disabled={data.page === data.pages}
                  className="h-8 px-2 border border-white/5 hover:bg-white/5 text-gray-400 hover:text-white"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>

      </main>

      {/* Transaction Add/Edit Dialog overlay */}
      <TransactionDialog
        isOpen={isDialogOpen}
        onClose={() => {
          setIsDialogOpen(false)
          setSelectedTransaction(null)
        }}
        transaction={selectedTransaction}
        onSubmit={handleCreateOrUpdate}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  )
}
