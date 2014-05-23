def includeme(config): # pragma: no cover
    config.include('.')
    config.scan('.')
    YEAR = 86400 * 365
    config.add_static_view('pontusstatic', 'pontus.dace_ui_extension:static', cache_max_age=YEAR)
