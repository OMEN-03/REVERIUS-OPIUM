import core.reverius_opium as app

print('core module imported')
try:
    loaded = app.load_plugins()
    print('loaded plugins:', loaded)
    print('plugin status:', app.get_plugin_status_text())
except Exception as e:
    print('plugin load failed:', type(e).__name__, e)
