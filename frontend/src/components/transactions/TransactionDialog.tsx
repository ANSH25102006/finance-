import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { X, Loader2 } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"

import { getAccounts } from "@/services/accountService"
import { getCategories } from "@/services/categoryService"
import type { Transaction, TransactionCreate } from "@/services/transactionService"
import { Button } from "@/components/ui/Button"

const transactionSchema = z.object({
  amount: z.coerce.number().positive("Amount must be positive"),
  transaction_type: z.enum(["income", "expense", "transfer"]),
  category_id: z.string().uuid("Invalid category ID").nullable().or(z.literal("")),
  account_id: z.string().uuid("Account is required"),
  merchant: z.string().optional().or(z.literal("")),
  description: z.string().min(1, "Description is required"),
  transaction_date: z.string().refine((val) => {
    if (!val) return false
    const d = new Date(val)
    const today = new Date()
    // Compare dates ignoring times
    d.setHours(0,0,0,0)
    today.setHours(0,0,0,0)
    return d <= today
  }, "Future dates are not allowed"),
  notes: z.string().optional().or(z.literal("")),
})



interface TransactionDialogProps {
  isOpen: boolean
  onClose: () => void
  transaction?: Transaction | null
  onSubmit: (data: TransactionCreate) => void
  isSubmitting: boolean
}

export function TransactionDialog({
  isOpen,
  onClose,
  transaction,
  onSubmit,
  isSubmitting,
}: TransactionDialogProps) {
  // Queries
  const { data: accounts = [] } = useQuery({
    queryKey: ["accounts"],
    queryFn: getAccounts,
    enabled: isOpen,
  })

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => getCategories(),
    enabled: isOpen,
  })

  const isEditMode = !!transaction

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<any>({
    resolver: zodResolver(transactionSchema) as any,
    defaultValues: {
      amount: 0,
      transaction_type: "expense",
      category_id: "",
      account_id: "",
      merchant: "",
      description: "",
      transaction_date: new Date().toISOString().split("T")[0],
      notes: "",
    },
  })

  const selectedType = watch("transaction_type")

  // Filter categories by type
  const filteredCategories = categories.filter(
    (c) => c.type.toLowerCase() === selectedType.toLowerCase()
  )

  // Prefill form in edit mode
  useEffect(() => {
    if (isOpen) {
      if (transaction) {
        reset({
          amount: transaction.amount,
          transaction_type: transaction.transaction_type,
          category_id: transaction.category_id || "",
          account_id: transaction.account_id,
          merchant: transaction.merchant || "",
          description: transaction.description,
          transaction_date: transaction.transaction_date,
          notes: transaction.notes || "",
        })
      } else {
        reset({
          amount: 0,
          transaction_type: "expense",
          category_id: "",
          account_id: accounts.length > 0 ? accounts[0].id : "",
          merchant: "",
          description: "",
          transaction_date: new Date().toISOString().split("T")[0],
          notes: "",
        })
      }
    }
  }, [isOpen, transaction, reset, accounts])

  const onFormSubmit = (values: any) => {
    onSubmit({
      ...values,
      category_id: values.category_id === "" ? null : values.category_id,
      merchant: values.merchant === "" ? null : values.merchant,
      notes: values.notes === "" ? null : values.notes,
    } as TransactionCreate)
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
          />

          {/* Modal Content */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 15 }}
            transition={{ type: "spring", duration: 0.4 }}
            className="os-card relative z-10 w-full max-w-lg overflow-hidden border border-white/10 bg-[#0c0e12] p-6 shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <h3 className="typo-heading text-lg font-semibold">
                  {isEditMode ? "Edit Transaction" : "New Transaction"}
                </h3>
                <p className="typo-caption mt-0.5 text-gray-500">
                  {isEditMode ? "Modify details below" : "Add financial details"}
                </p>
              </div>
              <button
                onClick={onClose}
                className="rounded-full p-1.5 text-gray-500 transition-colors hover:bg-white/5 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit(onFormSubmit)} className="mt-5 space-y-4">
              {/* Type Selector Tabs */}
              <div className="grid grid-cols-3 gap-1 rounded-lg bg-black/25 p-1 border border-white/5">
                {(["expense", "income", "transfer"] as const).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setValue("transaction_type", type)}
                    className={`rounded-md py-1.5 text-center typo-badge text-[8px] transition-all capitalize ${
                      selectedType === type
                        ? "bg-white/5 text-white border border-white/10 shadow-inner"
                        : "text-gray-500 hover:text-gray-300"
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>

              {/* Grid Inputs */}
              <div className="grid grid-cols-2 gap-4">
                {/* Amount */}
                <div className="flex flex-col gap-1.5">
                  <label className="typo-caption text-gray-400 font-medium">Amount (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    className="h-10 rounded-lg bg-[#060709] border border-white/5 px-3 text-sm text-white placeholder:text-gray-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    {...register("amount")}
                  />
                  {errors.amount && (
                    <span className="text-[10px] text-red-500">{errors.amount.message as string}</span>
                  )}
                </div>

                {/* Date */}
                <div className="flex flex-col gap-1.5">
                  <label className="typo-caption text-gray-400 font-medium">Date</label>
                  <input
                    type="date"
                    className="h-10 rounded-lg bg-[#060709] border border-white/5 px-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    {...register("transaction_date")}
                  />
                  {errors.transaction_date && (
                    <span className="text-[10px] text-red-500">{errors.transaction_date.message as string}</span>
                  )}
                </div>
              </div>

              {/* Grid 2 */}
              <div className="grid grid-cols-2 gap-4">
                {/* Account */}
                <div className="flex flex-col gap-1.5">
                  <label className="typo-caption text-gray-400 font-medium">Account</label>
                  <select
                    className="h-10 rounded-lg bg-[#060709] border border-white/5 px-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    {...register("account_id")}
                  >
                    <option value="" disabled className="text-gray-700">Select Account</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.name} (₹{acc.balance.toLocaleString("en-IN")})
                      </option>
                    ))}
                  </select>
                  {errors.account_id && (
                    <span className="text-[10px] text-red-500">{errors.account_id.message as string}</span>
                  )}
                </div>

                {/* Category */}
                <div className="flex flex-col gap-1.5">
                  <label className="typo-caption text-gray-400 font-medium">Category</label>
                  <select
                    className="h-10 rounded-lg bg-[#060709] border border-white/5 px-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    {...register("category_id")}
                  >
                    <option value="">Uncategorized</option>
                    {filteredCategories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                  {errors.category_id && (
                    <span className="text-[10px] text-red-500">{errors.category_id.message as string}</span>
                  )}
                </div>
              </div>

              {/* Merchant & Description */}
              <div className="grid grid-cols-2 gap-4">
                {/* Merchant */}
                <div className="flex flex-col gap-1.5">
                  <label className="typo-caption text-gray-400 font-medium">Merchant</label>
                  <input
                    type="text"
                    placeholder="e.g. Starbucks"
                    className="h-10 rounded-lg bg-[#060709] border border-white/5 px-3 text-sm text-white placeholder:text-gray-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    {...register("merchant")}
                  />
                </div>

                {/* Description */}
                <div className="flex flex-col gap-1.5">
                  <label className="typo-caption text-gray-400 font-medium">Description</label>
                  <input
                    type="text"
                    placeholder="e.g. Morning coffee"
                    className="h-10 rounded-lg bg-[#060709] border border-white/5 px-3 text-sm text-white placeholder:text-gray-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    {...register("description")}
                  />
                  {errors.description && (
                    <span className="text-[10px] text-red-500">{errors.description.message as string}</span>
                  )}
                </div>
              </div>

              {/* Notes */}
              <div className="flex flex-col gap-1.5">
                <label className="typo-caption text-gray-400 font-medium">Notes</label>
                <textarea
                  placeholder="Additional notes..."
                  rows={2}
                  className="rounded-lg bg-[#060709] border border-white/5 p-3 text-sm text-white placeholder:text-gray-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-none"
                  {...register("notes")}
                />
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 border-t border-white/5 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onClose}
                  className="text-gray-400 hover:text-white"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-black font-semibold hover:from-emerald-400 hover:to-cyan-400 shadow-md"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                      Saving...
                    </>
                  ) : isEditMode ? (
                    "Save Changes"
                  ) : (
                    "Add Transaction"
                  )}
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
