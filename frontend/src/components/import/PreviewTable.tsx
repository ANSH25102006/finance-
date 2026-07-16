import { TrendingDown, TrendingUp } from "lucide-react"
import type { NormalizedTransactionPreview } from "@/services/importService"

interface PreviewTableProps {
  transactions: NormalizedTransactionPreview[]
}

export function PreviewTable({ transactions }: PreviewTableProps) {
  // Sort newest date first
  const sortedTransactions = [...transactions].sort((a, b) => {
    return new Date(b.date).getTime() - new Date(a.date).getTime()
  })

  const formatCurrency = (val: number) => {
    return `₹${val.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
  }

  return (
    <div className="w-full overflow-hidden border border-white/5 bg-[#0a0c10] rounded-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-white/[0.04] text-[9px] uppercase tracking-widest text-gray-500 font-bold bg-[#0c0f14]">
              <th className="p-4">Date</th>
              <th className="p-4">Merchant</th>
              <th className="p-4">Description</th>
              <th className="p-4">Type</th>
              <th className="p-4 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.02]">
            {sortedTransactions.map((tx, idx) => {
              const isIncome = tx.transaction_type === "income"
              return (
                <tr key={idx} className="hover:bg-white/[0.01] transition-colors">
                  <td className="p-4 text-gray-400 font-mono">
                    {new Date(tx.date).toLocaleDateString("en-IN")}
                  </td>
                  <td className="p-4 font-semibold text-white">
                    {tx.merchant || "No Merchant"}
                  </td>
                  <td className="p-4 text-gray-500 max-w-[200px] truncate" title={tx.description}>
                    {tx.description}
                  </td>
                  <td className="p-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[9px] font-bold capitalize ${
                        isIncome
                          ? "bg-emerald-500/10 text-emerald-400"
                          : "bg-cyan-500/10 text-cyan-400"
                      }`}
                    >
                      {isIncome ? (
                        <TrendingUp className="h-2.5 w-2.5" />
                      ) : (
                        <TrendingDown className="h-2.5 w-2.5" />
                      )}
                      {tx.transaction_type}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <span
                      className={`font-semibold font-mono tabular-nums tracking-tight ${
                        isIncome ? "text-emerald-400" : "text-white"
                      }`}
                    >
                      {isIncome ? "+" : "-"}
                      {formatCurrency(tx.amount)}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
