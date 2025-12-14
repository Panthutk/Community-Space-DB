def validate_google_maps_url(value):
    allowed_prefixes = (
        "https://www.google.com/maps",
        "https://maps.google.com",
        "https://goo.gl/maps",
        "https://maps.app.goo.gl/",
    )

    # Check the link start with Allowed Prefix or not.
    if not value.startswith(allowed_prefixes):
        raise ValidationError("Please enter a Google Maps link.")