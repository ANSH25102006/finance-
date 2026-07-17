import re

def normalize_description(desc: str) -> str:
    """
    Normalizes transaction descriptions by stripping UPI/IMPS/NEFT/RTGS prefixes,
    reference numbers, slashes, hyphens, and collapsing extra whitespaces.
    All operations are case-insensitive.
    """
    if not desc:
        return ""

    # 1. Convert to lowercase
    val = desc.lower()

    # 2. Strip UPI, IMPS, NEFT, RTGS prefixes at the start
    # Matches patterns like: upi/12345/..., upi/..., imps/..., neft/..., rtgs/...
    val = re.sub(r'^(upi|imps|neft|rtgs)/[^/]*/', ' ', val)
    val = re.sub(r'^(upi|imps|neft|rtgs)/', ' ', val)

    # 3. Ignore standalone prefixes/keywords
    val = re.sub(r'\b(upi|imps|neft|rtgs)\b', ' ', val)

    # 4. Replace slashes and hyphens with spaces
    val = val.replace('/', ' ').replace('-', ' ')

    # 5. Remove numbers (digits) and reference IDs
    val = re.sub(r'\d+', ' ', val)

    # 6. Remove extra whitespaces
    val = re.sub(r'\s+', ' ', val).strip()

    return val
