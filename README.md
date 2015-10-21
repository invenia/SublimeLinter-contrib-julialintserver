SublimeLinter-contrib-julialintserver
================================

[![Build Status](https://travis-ci.org/Invenia/SublimeLinter-contrib-julialintserver.svg?branch=master)](https://travis-ci.org/Invenia/SublimeLinter-contrib-julialintserver)

This linter plugin for [SublimeLinter][docs] provides an interface to [julialintserver](https://github.com/invenia/SublimeLinter-contrib-julialintserver.jl). It will be used with files that have the “julia” syntax.

## Installation
SublimeLinter 3 must be installed in order to use this plugin. If SublimeLinter 3 is not installed, please follow the instructions [here][installation].

### Linter installation
In order for this plugin to be functional you must have a `Julia Lintserver` running. To set one up locally do the following:

1. Have [`Julia`](http://julialang.org/) installed.

1. Add [`Lint`](https://github.com/tonyhffong/Lint.jl) to `Julia`
   ```Julia
   Pkg.add( "Lint" )
   ```

1. Launch and keep running a `lintsever`.  This plugin's default port is `2222`.
   ```Julia
   using Lint
   lintserver(2222)
   ```

**Note:** This plugin requires `Julia Lintserver` version `0.0.0` or later.

### Linter configuration

This plugin only works when I has access to a running `Julia Lintserver`.

### Plugin installation
Please use [Package Control][pc] to install the linter plugin. This will ensure that the plugin will be updated when new versions are available. If you want to install from source so you can modify the source code, you probably know what you are doing so we won’t cover that here.

To install via Package Control, do the following:

1. Within Sublime Text, bring up the [Command Palette][cmd] and type `install`. Among the commands you should see `Package Control: Install Package`. If that command is not highlighted, use the keyboard or mouse to select it. There will be a pause of a few seconds while Package Control fetches the list of available plugins.

1. When the plugin list appears, type `julialintserver`. Among the entries you should see `SublimeLinter-contrib-julialintserver`. If that entry is not highlighted, use the keyboard or mouse to select it.

## Settings
For general information on how SublimeLinter works with settings, please see [Settings][settings]. For information on generic linter settings, please see [Linter Settings][linter-settings].

|Setting|Description|Default|
|:------|:----------|:------------:|
|show_info_warnings|Show INFO Warnings.|false
|server_address|Server Address.|"localhost"
|server_port|Server Port.|2222

## Contributing
If you would like to contribute enhancements or fixes, please do the following:

1. Fork the plugin repository.
1. Hack on a separate topic branch created from the latest `master`.
1. Commit and push the topic branch.
1. Make a pull request.
1. Be patient.  ;-)

Please note that modifications should follow these coding guidelines:

- Indent is 4 spaces.
- Code should pass flake8 and pep257 linters.
- Vertical whitespace helps readability, don’t be afraid to use it.
- Please use descriptive variable names, no abbreviations unless they are very well known.

Thank you for helping out!

[docs]: http://sublimelinter.readthedocs.org
[installation]: http://sublimelinter.readthedocs.org/en/latest/installation.html
[locating-executables]: http://sublimelinter.readthedocs.org/en/latest/usage.html#how-linter-executables-are-located
[pc]: https://sublime.wbond.net/installation
[cmd]: http://docs.sublimetext.info/en/sublime-text-3/extensibility/command_palette.html
[settings]: http://sublimelinter.readthedocs.org/en/latest/settings.html
[linter-settings]: http://sublimelinter.readthedocs.org/en/latest/linter_settings.html
[inline-settings]: http://sublimelinter.readthedocs.org/en/latest/settings.html#inline-settings
