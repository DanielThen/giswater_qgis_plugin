'''
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
'''

# -*- coding: utf-8 -*-
from PyQt4.QtCore import pyqtSignal, QPoint, QRect, Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsRectangle, QGis, QgsMapLayerRegistry
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsMapCanvasSnapper


class MincutConnec(QgsMapTool):

    canvasClicked = pyqtSignal()


    def __init__(self, iface, controller):
        """ Class constructor """

        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.controller = controller
        # Call superclass constructor and set current action
        QgsMapTool.__init__(self, self.canvas)

        self.dragging = False

        # Vertex marker
        self.vertex_marker = QgsVertexMarker(self.canvas)
        self.vertex_marker.setColor(QColor(255, 25, 25))
        self.vertex_marker.setIconSize(11)
        self.vertex_marker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.vertex_marker.setPenWidth(5)

        # Rubber band
        self.rubber_band = QgsRubberBand(self.canvas, True)
        mFillColor = QColor(100, 0, 0);
        self.rubber_band.setColor(mFillColor)
        self.rubber_band.setWidth(3)
        mBorderColor = QColor(254, 58, 29)
        self.rubber_band.setBorderColor(mBorderColor)

        # Select rectangle
        self.select_rect = QRect()

        # TODO: Parametrize
        self.connec_group = ["Wjoin"]
        #self.snapperManager = SnappingConfigManager(self.iface)
        self.snapper = QgsMapCanvasSnapper(self.canvas)


    def activate(self):
        pass


    def reset(self):
        ''' Clear selected features '''

        layer = self.layer_connec
        if layer is not None:
            layer.removeSelection()

        # Graphic elements
        self.rubber_band.reset()


    def canvasPressEvent(self, event):   #@UnusedVariable
        self.select_rect.setRect(0, 0, 0, 0)
        self.rubber_band.reset()


    def canvasMoveEvent(self, event):
        ''' With left click the digitizing is finished '''

        if event.buttons() == Qt.LeftButton:
            if not self.dragging:
                self.dragging = True
                self.select_rect.setTopLeft(event.pos())
            self.select_rect.setBottomRight(event.pos())
            self.set_rubber_band()

        else:
            # Hide highlight
            self.vertex_marker.hide()

            # Get the click
            x = event.pos().x()
            y = event.pos().y()
            event_point = QPoint(x, y)

            # Snapping
            (retval, result) = self.snapper.snapToBackgroundLayers(event_point)  # @UnusedVariable

            # That's the snapped point
            if result <> []:
                # Check feature
                for snap_point in result:

                    element_type = snap_point.layer.name()
                    if element_type in self.connec_group:
                        # Get the point
                        point = QgsPoint(snap_point.snappedVertex)

                        # Add marker
                        self.vertex_marker.setCenter(point)
                        self.vertex_marker.show()

                        break


    def canvasReleaseEvent(self, event):
        ''' With left click the digitizing is finished '''

        if event.button() == Qt.LeftButton:

            # Get the click
            x = event.pos().x()
            y = event.pos().y()
            eventPoint = QPoint(x, y)

            # Not dragging, just simple selection
            if not self.dragging:
                
                # Snap to node
                (retval, result) = self.snapper.snapToBackgroundLayers(eventPoint)  # @UnusedVariable

                # That's the snapped point
                if result <> []:

                    # Check feature
                    for snapPoint in result:

                        element_type = snapPoint.layer.name()
                        if element_type in self.connec_group:
                            feat_type = 'connec'
                        else:
                            continue

                        point = QgsPoint(snapPoint.snappedVertex)  # @UnusedVariable
                        # layer.removeSelection()
                        # layer.select([result[0].snappedAtGeometry])

                        #snapPoint.layer.removeSelection()
                        snapPoint.layer.select([snapPoint.snappedAtGeometry])

                        # Create link
                        #self.link_connec()

                        # Hide highlight
                        #self.vertex_marker.hide()

            else:

                # Set valid values for rectangle's width and height
                if self.select_rect.width() == 1:
                    self.select_rect.setLeft(self.select_rect.left() + 1)

                if self.select_rect.height() == 1:
                    self.select_rect.setBottom(self.select_rect.bottom() + 1)

                self.set_rubber_band()               
                self.select_multiple_features(self.selected_rectangle)
                self.dragging = False

                # Create link
                #self.link_connec()

            # Refresh map canvas
            self.rubber_band.reset()
            self.iface.mapCanvas().refreshAllLayers()

            for layerRefresh in self.iface.mapCanvas().layers():
                layerRefresh.triggerRepaint()


    def set_rubber_band(self):

        # Coordinates transform
        transform = self.canvas.getCoordinateTransform()

        # Coordinates
        ll = transform.toMapCoordinates(self.select_rect.left(), self.select_rect.bottom())
        lr = transform.toMapCoordinates(self.select_rect.right(), self.select_rect.bottom())
        ul = transform.toMapCoordinates(self.select_rect.left(), self.select_rect.top())
        ur = transform.toMapCoordinates(self.select_rect.right(), self.select_rect.top())

        # Rubber band
        self.rubber_band.reset()
        self.rubber_band.addPoint(ll, False)
        self.rubber_band.addPoint(lr, False)
        self.rubber_band.addPoint(ur, False)
        self.rubber_band.addPoint(ul, False)
        self.rubber_band.addPoint(ll, True)

        self.selected_rectangle = QgsRectangle(ll, ur)


    def select_multiple_features(self, rectangle):
       
        if self.connec_group is None:
            return

        # Change cursor
        #QApplication.setOverrideCursor(Qt.WaitCursor)

        if QGis.QGIS_VERSION_INT >= 21600:

            # Selection for all connec group layers
            for layer_name in self.connec_group:
                # Get layer by his name
                layer = QgsMapLayerRegistry.instance().mapLayersByName(layer_name)
                if layer:
                    layer = layer[0]  
                    layer.selectByRect(rectangle)
                else:
                    self.controller.log_info("Layer not found", parameter=layer_name)

        else:

            for layer_name in self.connec_group:
                self.iface.setActiveLayer(layer)                
                layer.removeSelection()
                layer.select(rectangle, True)

        # Old cursor
        #QApplication.restoreOverrideCursor()

