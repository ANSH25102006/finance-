from typing import Dict, Any

BANK_FORMATS: Dict[str, Dict[str, Any]] = {
    "hdfc": {
        "name": "HDFC Bank Statement",
        "required_headers": ["Date", "Narration", "Withdrawal Amt.", "Deposit Amt."],
        "date_col": "Date",
        "desc_col": "Narration",
        "withdrawal_col": "Withdrawal Amt.",
        "deposit_col": "Deposit Amt.",
        "ref_col": "Chq./Ref. No.",
        "date_formats": ["%d/%m/%y", "%d/%m/%Y", "%d-%m-%Y", "%d-%m-%y"]
    },
    "icici": {
        "name": "ICICI Bank Statement",
        "required_headers": ["Transaction Date", "Description", "Withdrawal (Dr)", "Deposit (Cr)"],
        "date_col": "Transaction Date",
        "desc_col": "Description",
        "withdrawal_col": "Withdrawal (Dr)",
        "deposit_col": "Deposit (Cr)",
        "ref_col": "Cheque No.",
        "date_formats": ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"]
    },
    "generic": {
        "name": "Generic Transaction Statement",
        "required_headers": ["Date", "Description", "Amount"],
        "date_col": "Date",
        "desc_col": "Description",
        "amount_col": "Amount",
        "type_col": "Type",
        "ref_col": "Reference",
        "date_formats": ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]
    }
}
