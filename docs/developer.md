### Developer

This is documentation is intended for developers wishing to modify or extend Inkcut. 


### Plugins

Inkcut is designed entirely using plugins. You can define plugins and install them using python 
entry points. Inkcut loads external plugins from the `inkcut.plugin` entry point. Using this you can 
create python packages that when installed will extend Inkcut. The entry point implementation shall 
return an enaml `PluginManifest` factory (either the PluginManifest subclass or a function that
when called returns a PluginManifest instance).   

> See a nice intro on entry points here [using-plugins](https://docs.pylonsproject.org/projects/pylons-webframework/en/latest/advanced_pylons/entry_points_and_plugins.html#using-plugins)

Plugins can define:

- New dock items
- Menu items and commands
- Custom device drivers
- Custom device protocols
- Custom device connection types

These plugins can interact with all builtin plugins using the enaml workbench interface.