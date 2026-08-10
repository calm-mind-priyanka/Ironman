# Compatibility module: AutoFilter search/callbacks live in handlers/search.py.
# Keeping this module makes the architecture easy to extend without a second
# plugin-registration mechanism.
def register(app):
    pass
