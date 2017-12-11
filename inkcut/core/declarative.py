"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 11, 2017

@author: jrm
"""
from .utils import log, clip
from enaml.core.declarative import d_, Declarative as EnamlDeclarative


class Declarative(EnamlDeclarative):
    """ A json pickable declarative using the id """

    def __getstate__(self):
        """ Only pickle declarative members
        
        """
        state = super(Declarative, self).__getstate__()
        for name, member in self.members().items():
            metadata = member.metadata
            if (name in state and (not metadata or
                                       not metadata.get('d_final', False))):
                del state[name]
        return state

    def __setstate__(self, state):
        """  Set the state ignoring any fields that fail to set which
        may occur due to version changes.
        
        """
        for key, value in state.items():
            try:
                setattr(self, key, value)
            except Exception as e:
                #: Shorten any long values
                log.warning("Failed to restore state '{}.{} = {}'".format(
                    self, key, clip(value)
                ))