import { apiClient } from "./api"

export interface NormalizedTransactionPreview {
  date: string
  description: string
  amount: number
  transaction_type: "income" | "expense"
  merchant: string | null
  reference: string | null
  raw_data: Record<string, string>
}

export interface CSVPreviewResponse {
  bank_format: string
  total_parsed: number
  transactions: NormalizedTransactionPreview[]
}

export async function previewCSVImport(file: File, bankFormat: string): Promise<CSVPreviewResponse> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("bank_format", bankFormat)

  const { data } = await apiClient.post<CSVPreviewResponse>("/api/import/csv-preview", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  })
  return data
}

export interface CSVImportSummary {
  total_rows: number
  imported: number
  duplicates: number
  failed: number
  message: string
}

export async function importCSVTransactions(file: File, bankFormat: string, accountId: string): Promise<CSVImportSummary> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("bank_format", bankFormat)
  formData.append("account_id", accountId)

  const { data } = await apiClient.post<CSVImportSummary>("/api/import/import-transactions", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  })
  return data
}
