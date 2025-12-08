from .calling_codes import CALLING_CODES


def format_phone_number(raw_phone: str, country: str) -> str:
    if country not in CALLING_CODES:
        raise ValueError("Invalid country code.")

    raw_phone = raw_phone.strip()

    if not raw_phone.isdigit():
        raise ValueError("Phone number must contain digits only.")

    if not 8 <= len(raw_phone) <= 11:
        raise ValueError("Phone number length is invalid.")

    country_data = CALLING_CODES[country]
    prefix = country_data["code"]
    drop_zero = country_data["drop_zero"]

    # remove leading 0 if required
    if drop_zero and raw_phone.startswith("0"):
        raw_phone = raw_phone[1:]

    return prefix + raw_phone
