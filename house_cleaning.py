from collections.abc import Iterable


def combine_values(*args):
    """
    Safely combine multiple values into a flattened list.
    """

    def flatten(item):
        if item is None:
            return []
        elif isinstance(item, str):
            return [item]
        elif isinstance(item, int):
            return [item]
        elif isinstance(item, Iterable):
            return [sub_item for i in item for sub_item in flatten(i)]
        else:
            return [item]

    return [item for arg in args for item in flatten(arg)]


def safe_get(data, *keys, default=None):
    """
    Safely get a value from nested dictionaries or lists.
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        elif isinstance(data, list):
            try:
                data = data[int(key)] if key.isdigit() else default
            except (IndexError, ValueError):
                return default
        else:
            return default

        if data is None:
            return default

    return data

def safe_get_multiple(data, base_key, *sub_keys, default=None):
    """
     Get multiple values from nested dictionaries or lists in a list without errors
    """
    base = safe_get(data, base_key)
    if base is None:
        return [default] * len(sub_keys)

    return [safe_get(base, sub_key, default=default) for sub_key in sub_keys]



