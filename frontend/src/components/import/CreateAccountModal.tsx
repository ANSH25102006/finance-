import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createAccount } from "@/services/accountService"
import { X, Plus, Wallet } from "lucide-react"

interface CreateAccountModalProps {
  onClose: () => void
}

export function CreateAccountModal({ onClose }: CreateAccountModalProps) {
  const queryClient = useQueryClient()
  
  const [name, setName] = useState("")
  const [type, setType] = useState("Savings")
  const [balance, setBalance] = useState("")
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => {
      if (!name.trim()) throw new Error("Account Name is required")
      return createAccount({
        name: name.trim(),
        institution: type,
        balance: balance ? parseFloat(balance) : 0,
        currency: "INR"
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] })
      onClose()
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || err.message || "Failed to create account")
    }
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="os-card w-full max-w-md border border-white/10 p-6 flex flex-col gap-6 relative shadow-2xl">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <Wallet className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Create Account</h2>
            <p className="text-xs text-gray-400">Add a destination for your transactions</p>
          </div>
        </div>

        {errorMsg && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-xs text-red-400">
            {errorMsg}
          </div>
        )}

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold">Account Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. HDFC Salary, Credit Card"
              className="h-10 rounded-lg bg-[#0c0e12] border border-white/5 px-3 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors"
              autoFocus
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold">Account Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="h-10 rounded-lg bg-[#0c0e12] border border-white/5 px-3 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors cursor-pointer"
            >
              <option value="Savings">Savings</option>
              <option value="Current">Current</option>
              <option value="Credit Card">Credit Card</option>
              <option value="Wallet">Wallet</option>
              <option value="Cash">Cash</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold">Opening Balance (Optional)</label>
            <input
              type="number"
              value={balance}
              onChange={(e) => setBalance(e.target.value)}
              placeholder="0.00"
              className="h-10 rounded-lg bg-[#0c0e12] border border-white/5 px-3 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors"
            />
          </div>
        </div>

        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="h-10 rounded-lg bg-emerald-500 hover:bg-emerald-400 font-semibold text-xs text-black transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
        >
          {mutation.isPending ? "Creating..." : (
            <>
              <Plus className="h-4 w-4" />
              Create Account
            </>
          )}
        </button>
      </div>
    </div>
  )
}
