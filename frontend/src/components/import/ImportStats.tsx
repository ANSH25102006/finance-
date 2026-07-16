import { FileText, TrendingUp, TrendingDown, ArrowRightLeft } from "lucide-react"

interface ImportStatsProps {
  totalCount: number
  incomeTotal: number
  expenseTotal: number
}

export function ImportStats({ totalCount, incomeTotal, expenseTotal }: ImportStatsProps) {
  const netFlow = incomeTotal - expenseTotal

  const formatCurrency = (val: number) => {
    return `₹${val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {/* Total Transactions */}
      <div className="os-card p-5 border border-white/5 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="typo-subheading text-gray-500">Transactions Parsed</span>
          <FileText className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="mt-4">
          <h3 className="text-xl font-bold tabular-nums text-white">{totalCount}</h3>
          <p className="typo-caption text-gray-500 mt-1">Total items in statement</p>
        </div>
      </div>

      {/* Income Total */}
      <div className="os-card p-5 border border-white/5 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="typo-subheading text-gray-500">Income Inflow</span>
          <TrendingUp className="h-4 w-4 text-emerald-500" />
        </div>
        <div className="mt-4">
          <h3 className="text-xl font-bold tabular-nums text-emerald-400">{formatCurrency(incomeTotal)}</h3>
          <p className="typo-caption text-gray-500 mt-1">Sum of deposit values</p>
        </div>
      </div>

      {/* Expense Total */}
      <div className="os-card p-5 border border-white/5 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="typo-subheading text-gray-500">Expense Outflow</span>
          <TrendingDown className="h-4 w-4 text-cyan-400" />
        </div>
        <div className="mt-4">
          <h3 className="text-xl font-bold tabular-nums text-white">{formatCurrency(expenseTotal)}</h3>
          <p className="typo-caption text-gray-500 mt-1">Sum of withdrawal values</p>
        </div>
      </div>

      {/* Net Cash Flow */}
      <div className="os-card p-5 border border-white/5 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="typo-subheading text-gray-500">Statement Net Flow</span>
          <ArrowRightLeft className="h-4 w-4 text-purple-400" />
        </div>
        <div className="mt-4">
          <h3 className={`text-xl font-bold tabular-nums ${netFlow >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {netFlow >= 0 ? "+" : ""}{formatCurrency(netFlow)}
          </h3>
          <p className="typo-caption text-gray-500 mt-1">Net statement cash change</p>
        </div>
      </div>
    </div>
  )
}
