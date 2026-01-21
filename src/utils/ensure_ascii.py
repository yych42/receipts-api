import urllib.parse


def ensure_ascii(input_dict: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Ensure all values in a dictionary are URL encoded.
    If a value is a list, join the list into a comma-separated string.
    Nested dictionaries are flattened into keys with a 'path.to.final.key' format.
    """
    result = {}
    for k, v in input_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            result.update(ensure_ascii(v, new_key, sep=sep))
        elif isinstance(v, list):
            v = ", ".join(map(str, v))
            result[new_key] = urllib.parse.quote(v)
        else:
            result[new_key] = urllib.parse.quote(str(v))
    return result
