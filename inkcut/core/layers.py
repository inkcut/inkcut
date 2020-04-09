# -----------------------------------------------------------------------------
# SVG Layers filtering
# -----------------------------------------------------------------------------

"""   Inkscape

    inkscape uses the group tag (G) for describing a layer

    <g
     inkscape:groupmode="layer"
     id="layer2"
     inkscape:label="coupe"
     style="display:inline"
     transform="translate(0,-87)"
     sodipodi:insensitive="true">
    >

    attribute name "inkscape:" is translated to
            if e.get ("{http://www.inkscape.org/namespaces/inkscape}groupmode") == "layer":


    Loading a document is too step.
    -find Layer definitions and mark them load=False when not "display:inline".
     eg, Layers not visible in Inkscape are skipped
    -load the actual data and ignore layers marked not enabled

    A specific DockItem lists all the layer's definition
    and reload the doc when necessary

    TODO:
            -rotate the layer to facilitate rearangements
            by inserting/modifying the transform attached to the group
            (usefull for painting mask layers)
            -one color / layer
            -use mouse to move layers
"""

layers = []             # list of layers discovered

class Layer:
    name = ''           # displayed name
    loaded = False      # the xml for this layer is loaded or not
    enabled = True      # when loaded, use it or not
    ofssetX = 0
    offsetY = 0
    rotate  = 0
