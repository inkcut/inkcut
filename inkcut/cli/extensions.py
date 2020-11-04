"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 16, 2017

Based on my work from the https://github.com/codelv/enaml-native-cli

@author: jrm
"""
from atom.api import Str, Callable, List
from enaml.core.declarative import Declarative, d_


CLI_COMMAND_POINT = 'inkcut.cli.command'


class StopSystemExit(SystemExit):
    """ Tell the CLI Plugin to not exit 
    after running the command. 
    """


class CliCommand(Declarative):
    #: The cli sub command name `inkcut <name>`
    name = d_(Str())

    #: The cli short description for this sub command
    desc = d_(Str())

    #: The cli help text for this sub command
    help = d_(Str())

    #: List of 2 time tuples of command arguments this command accepts.
    #: These are passed to the ArgumentParser.add_argument(args, **kwargs)
    args = d_(List(tuple))

    #: Handler called when this command is invoked. It will be passed
    #: the `Command` instance that contains the parsed arguments
    #: and a reference to the workbench.
    handler = d_(Callable())
