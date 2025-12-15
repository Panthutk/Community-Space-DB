from .calling_codes import CALLING_CODES
from django.core.validators import RegexValidator

# Validator enforcing international (E.164) phone format.
# Accepts optional "+" and 10–15 digits total.
format_rule = RegexValidator(
    regex=r'^\+?[1-9]\d{9,14}$',
    message="Incorrect phone number"
)

def format_phone_number(raw_phone: str, country: str) -> str:
    """
    Normalize a raw phone number using country-specific rules.
    Leading zeros may be removed depending on the country's configuration.
    Returns the number combined with its international prefix.
    """
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

    # drop 0 based on the country's rule.
    if drop_zero and raw_phone.startswith("0"):
        raw_phone = raw_phone[1:]

    return prefix + raw_phone


def deformat_phone_number(instance):
    """
    Converts an E.164 phone number stored on the model back into:
    - country code
    - local phone (raw format)
    """
    full_phone = instance.phone

    for country_key, cfg in CALLING_CODES.items():
        prefix = cfg["code"]

        if full_phone.startswith(prefix):
            raw = full_phone[len(prefix):]

            # Restore leading zero if the country's rule drops it.
            if cfg.get("drop_zero") and not raw.startswith("0"):
                raw = "0" + raw

            return {
                "country": country_key,
                "phone": raw,
            }

    raise ValueError("Could not match phone number to any country prefix.")
