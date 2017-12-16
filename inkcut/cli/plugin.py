"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 16, 2017

Based on my work from the https://github.com/codelv/enaml-native-cli

@author: jrm
"""
import sys
import traceback
from atom.api import Atom, Instance, List
from argparse import ArgumentParser, Namespace, ArgumentError
from enaml.workbench.api import Plugin, Workbench
from inkcut.core.utils import log
from . import extensions


class CommandParser(ArgumentParser):
    """ Modified from "Rob Crowie" answer from
    https://stackoverflow.com/questions/5943249/

    This only exists when an actual parser error occurs ignoring errors when
    no arguments are passed.

    """

    def error(self, message):
        """ Only exit if an argument is given and doesn't match. """
        exc = sys.exc_info()[1]
        if exc:
            raise exc

    def exit_with_error(self, message):
        super(CommandParser, self).error(message)


class Command(Atom):
    """ Base class for a CLI command. """

    #: Reference to the declaration of this command
    declaration = Instance(extensions.CliCommand)

    #: Reference to the CliPlugin
    workbench = Instance(Workbench)

    #: Parsed args
    args = Instance(Namespace)

    #: Parser this command uses. Generated automatically.
    parser = Instance(ArgumentParser)

    def run(self, args):
        """ Invoke the command with the parsed arguments. The handler
        shall raise a StopSystemExit if they don't want the application to
        to run and quit. 
        
        """
        self.args = args
        return self.declaration.handler(self)


class CliPlugin(Plugin):
    """ This plugin lets you declare CLI commands that hook anywhere in
    the startup process. 
    
    
    """
    #: Root parser
    parser = Instance(ArgumentParser)

    #: Commands
    commands = List(Command)

    def start(self):
        """ Start listening for command updates """
        super(CliPlugin, self).start()
        self._refresh_commands()
        self._bind_observers()

    def stop(self):
        """ Stop listening for command updates """
        super(CliPlugin, self).stop()
        self._unbind_observers()

    def _default_parser(self):
        """ Generate a parser using the command list """

        #: Create the root parser
        parser = CommandParser(prog=self.workbench.app_name.lower())

        #: Build parser, prepare commands
        subparsers = parser.add_subparsers()
        for c in self.commands:
            d = c.declaration
            p = subparsers.add_parser(d.name, help=d.help)
            c.parser = p
            for (flags, kwargs) in d.args:
                p.add_argument(flags, **kwargs)
            p.set_defaults(cmd=c)

        return parser

    def _refresh_commands(self, change=None):
        """ Reload all CliCommands registered by any Plugins 
        
        Any plugin can add to this list by providing a CliCommand 
        extension in the PluginManifest.
        
        If the system arguments match the command it will be invoked with
        the given arguments as soon as the plugin that registered the command
        is loaded.  Thus you can effectively hook your cli argument at any
        stage of the process.
        
        """
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.CLI_COMMAND_POINT)

        commands = []
        for extension in sorted(point.extensions, key=lambda ext: ext.rank):
            for d in extension.get_children(extensions.CliCommand):
                commands.append(Command(
                    declaration=d,
                    workbench=self.workbench,
                ))

        #: Update
        self.commands = commands

        #: Log that they've been updated
        log.debug("CLI | Commands loaded")

        #: Recreate the parser
        self.parser = self._default_parser()

        #: Parse the args, if an error occurs the program will exit
        #: but if no args are given it continues
        try:
            args = self.parser.parse_args()
        except ArgumentError as e:
            #: Ignore errors that may occur because commands havent loaded yet
            if [m for m in ['invalid choice'] if m in str(e.message)]:
                return
            self.parser.exit_with_error(e.message)

        #: Run it but defer it until the next available loop so the current
        #: plugin finishes loading
        if hasattr(args, 'cmd'):
            self.workbench.application.deferred_call(self.run, args.cmd, args)
        else:
            log.debug("CLI | No cli command was given.")

    def run(self, cmd, args):
        """ Run the given command with the given arguments.
        
        """
        #: If a sub command was given in the cli, invoke it.
        try:
            cmd = args.cmd
            log.debug("CLI | Runinng command '{}' with args: {}".format(
                cmd.declaration.name, args))
            sys.exit(cmd.run(args))
        except extensions.StopSystemExit:
            pass
        except Exception as e:
            #: Catch and exit, if we don't do this it will open the
            #: startup error dialog.
            log.error(traceback.format_exc())
            sys.exit(-1)


    def _bind_observers(self):
        """ Setup the observers for the plugin.
        """
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.CLI_COMMAND_POINT)
        point.observe('extensions', self._refresh_commands)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.
        """
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.CLI_COMMAND_POINT)
        point.unobserve('extensions', self._refresh_commands)