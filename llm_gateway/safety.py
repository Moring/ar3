def check_prompt_safe(text: str) -> tuple[bool, str|None]:
    # Placeholder safety check
    if "DROP TABLE" in text.upper():
        return False, "Potentially unsafe DB instruction"
    return True, None
