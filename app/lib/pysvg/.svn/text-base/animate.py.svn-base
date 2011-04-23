#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from attributes import *
from core import BaseShape, BaseElement

#####################################################
# Attribute sets for animations
# Animation elements see below
#####################################################
class AnimationAttrib(XLinkAttrib):
    """
    The AnimationAttrib class defines the Animation.attrib attribute set.
    """

class AnimationAttributeAttrib:
    """
    The AnimationAttributeAttrib class defines the AnimationAttribute.attrib attribute set.
    """
    def set_attributeName(self, attributeName):
        self._attributes['attributeName'] = attributeName
    def get_attributeName(self):
        return self._attributes.get('attributeName')
    
    def set_attributeType(self, attributeType):
        self._attributes['attributeType'] = attributeType
    def get_attributeType(self):
        return self._attributes.get('attributeType')

class AnimationTimingAttrib:
    """
    The AnimationTimingAttrib class defines the AnimationTiming.attrib attribute set.
    """
    def set_begin(self, begin):
        self._attributes['begin'] = begin
    def get_begin(self):
        return self._attributes.get('begin')
    
    def set_dur(self, dur):
        self._attributes['dur'] = dur
    def get_dur(self):
        return self._attributes.get('dur')
    
    def set_end(self, end):
        self._attributes['end'] = end
    def get_end(self):
        return self._attributes.get('end')
    
    def set_min(self, min):
        self._attributes['min'] = min
    def get_min(self):
        return self._attributes.get('min')
    
    def set_max(self, max):
        self._attributes['max'] = max
    def get_max(self):
        return self._attributes.get('max')
    
    def set_restart(self, restart):
        self._attributes['restart'] = restart
    def get_restart(self):
        return self._attributes.get('restart')
    
    def set_repeatCount(self, repeatCount):
        self._attributes['repeatCount'] = repeatCount
    def get_repeatCount(self):
        return self._attributes.get('repeatCount')
    
    def set_repeatDur(self, repeatDur):
        self._attributes['repeatDur'] = repeatDur
    def get_repeatDur(self):
        return self._attributes.get('repeatDur')
    
    def set_fill(self, fill):
        self._attributes['fill'] = fill
    def get_fill(self):
        return self._attributes.get('fill')

class AnimationValueAttrib:
    """
    The AnimationValueAttrib class defines the AnimationValue.attrib attribute set.
    """
    def set_calcMode(self, calcMode):
        self._attributes['calcMode'] = calcMode
    def get_calcMode(self):
        return self._attributes.get('calcMode')
    
    def set_values(self, values):
        self._attributes['values'] = values
    def get_values(self):
        return self._attributes.get('values')

    def set_keyTimes(self, keyTimes):
        self._attributes['keyTimes'] = keyTimes
    def get_keyTimes(self):
        return self._attributes.get('keyTimes')
    
    def set_keySplines(self, keySplines):
        self._attributes['keySplines'] = keySplines
    def get_keySplines(self):
        return self._attributes.get('keySplines')
    
    def set_from(self, fromField):
        self._attributes['from'] = fromField
    def get_from(self):
        return self._attributes.get('from')
    
    def set_to(self, toField):
        self._attributes['to'] = toField
    def get_to(self):
        return self._attributes.get('to')
    
    def set_by(self, by):
        self._attributes['by'] = by
    def get_by(self):
        return self._attributes.get('by')

class AnimationAdditionAttrib:
    """
    The AnimationAdditionAttrib class defines the AnimationAddition.attrib attribute set.
    """
    def set_additive(self, additive):
        self._attributes['additive'] = additive
    def get_additive(self):
        return self._attributes.get('additive')
    
    def set_accumulate(self, accumulate):
        self._attributes['accumulate'] = accumulate
    def get_accumulate(self):
        return self._attributes.get('accumulate')
        
class AnimationEventsAttrib:
    """
    The AnimationEventsAttrib class defines the AnimationEvents.attrib attribute set.
    """
    def set_onbegin(self, onbegin):
        self._attributes['onbegin'] = onbegin
    def get_onbegin(self):
        return self._attributes.get('onbegin')
    
    def set_onend(self, onend):
        self._attributes['onend'] = onend
    def get_onend(self):
        return self._attributes.get('onend')
    
    def set_onrepeat(self, onrepeat):
        self._attributes['onrepeat'] = onrepeat
    def get_onrepeat(self):
        return self._attributes.get('onrepeat')
    
    def set_onload(self, onload):
        self._attributes['onload'] = onload
    def get_onload(self):
        return self._attributes.get('onload')
##############################################
# Animation Elements
##############################################
class animate(BaseShape, CoreAttrib, ConditionalAttrib, ExternalAttrib, AnimationEventsAttrib, AnimationAttrib, AnimationAttributeAttrib, AnimationTimingAttrib, AnimationValueAttrib, AnimationAdditionAttrib):
    """
    Class representing the animate element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'animate')
        self.setKWARGS(**kwargs)
        
class set(BaseShape, CoreAttrib, ConditionalAttrib, ExternalAttrib, AnimationEventsAttrib, AnimationAttrib, AnimationAttributeAttrib, AnimationTimingAttrib):
    """
    Class representing the set element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'set')
        self.setKWARGS(**kwargs)
        
    def set_to(self, toField):
        self._attributes['to'] = toField
    def get_to(self):
        return self._attributes.get('to')

class animateMotion(BaseShape, CoreAttrib, ConditionalAttrib, ExternalAttrib, AnimationEventsAttrib, AnimationAttrib, AnimationTimingAttrib, AnimationValueAttrib, AnimationAdditionAttrib):
    """
    Class representing the animateMotion element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'animateMotion')
        self.setKWARGS(**kwargs)
        
    def set_path(self, path):
        self._attributes['path'] = path
    def get_path(self):
        return self._attributes.get('path')
    
    def set_keyPoints(self, keyPoints):
        self._attributes['keyPoints'] = keyPoints
    def get_keyPoints(self):
        return self._attributes.get('keyPoints')
    
    def set_rotate(self, rotate):
        self._attributes['rotate'] = rotate
    def get_rotate(self):
        return self._attributes.get('rotate')
    
    def set_origin(self, origin):
        self._attributes['origin'] = origin
    def get_origin(self):
        return self._attributes.get('origin')
    
class animateTransform(BaseShape, CoreAttrib, ConditionalAttrib, ExternalAttrib, AnimationEventsAttrib, AnimationAttrib, AnimationAttributeAttrib, AnimationTimingAttrib, AnimationValueAttrib, AnimationAdditionAttrib):
    """
    Class representing the animateTransform element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'animateTransform')
        self.setKWARGS(**kwargs)
        
    def set_type(self, type):
        self._attributes['type'] = type
    def get_type(self):
        return self._attributes.get('type')
    
class animateColor(BaseShape, CoreAttrib, ConditionalAttrib, ExternalAttrib, AnimationEventsAttrib, AnimationAttrib, AnimationAttributeAttrib, AnimationTimingAttrib, AnimationValueAttrib, AnimationAdditionAttrib):
    """
    Class representing the animateColor element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'animateColor')
        self.setKWARGS(**kwargs)
        
class mpath(BaseShape, CoreAttrib, XLinkAttrib, ExternalAttrib):
    """
    Class representing the animateColor element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'mpath')
        self.setKWARGS(**kwargs)
