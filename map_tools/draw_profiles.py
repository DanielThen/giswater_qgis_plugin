"""

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

"""

# -*- coding: utf-8 -*-
from qgis.core import QgsPoint, QgsFeatureRequest, QgsMapLayer, QgsExpression
from qgis.gui import QgsVertexMarker
from PyQt4.QtCore import QPoint, Qt
from PyQt4.QtGui import QColor, QListWidget


from PyQt4.QtCore import *
from PyQt4.QtGui import *


from qgis.core import *
from qgis.gui import *

from decimal import *

import matplotlib.pyplot as plt
import math
from dao.controller import DaoController
import utils_giswater
#from controller import DaoController
from ..ui.draw_profile import DrawProfile
from ..ui.load_profiles import LoadProfiles
import matplotlib.patches as patches

import utils_giswater
from parent_init import ParentDialog

from parent import ParentMapTool


# Import networkanalysis module
from qgis.networkanalysis import *

from functools import partial

from dao.pg_dao import PgDao

import string
import psycopg2         #@UnusedImport
import psycopg2.extras


class DrawProfiles(ParentMapTool):
    ''' Button 1. Draw_profiles '''

    def __init__(self, iface, settings, action, index_action):
        ''' Class constructor '''

        # Call ParentMapTool constructor
        super(DrawProfiles, self).__init__(iface, settings, action, index_action)

        # Vertex marker
        self.vertexMarker = QgsVertexMarker(self.canvas)
        self.vertexMarker.setColor(QColor(255, 25, 25))
        self.vertexMarker.setIconSize(12)
        self.vertexMarker.setIconType(QgsVertexMarker.ICON_CIRCLE)  # or ICON_CROSS, ICON_X
        self.vertexMarker.setPenWidth(5)
        self.list_of_selected_nodes = []
        self.nodes = []
        node_id_dijkstra=[]
        ''' QgsMapTools inherited event functions '''
        #self.open()
        


    def canvasMoveEvent(self, event):
        # Hide highlight
        self.vertexMarker.hide()

        # Get the click
        x = event.pos().x()
        y = event.pos().y()

   

        #Plugin reloader bug, MapTool should be deactivated
        try:
            eventPoint = QPoint(x, y)
        except(TypeError, KeyError) as e:
            self.iface.actionPan().trigger()
            return

        # Snapping
        (retval, result) = self.snapper.snapToBackgroundLayers(eventPoint)  # @UnusedVariable

        # That's the snapped point
        if result <> []:

            # Check Arc or Node
            for snapPoint in result:
                exist=self.snapperManager.check_node_group(snapPoint.layer)
                if exist:
                    point = QgsPoint(result[0].snappedVertex)
                    # Add marker
                    self.vertexMarker.setCenter(point)
                    self.vertexMarker.show()
                    break


    def canvasReleaseEvent(self, event):
        
        # With left click the digitizing is finished
        if event.button() == Qt.LeftButton:

            # Get the click
            x = event.pos().x()
            y = event.pos().y()

            eventPoint = QPoint(x, y)

            snappFeat = None

            # Snap to node
            (retval, result) = self.snapper.snapToBackgroundLayers(eventPoint)  # @UnusedVariable
       
            if result <> []:
                self.snappFeat = next(result[0].layer.getFeatures(QgsFeatureRequest().setFilterFid(result[0].snappedAtGeometry)))
 
                # Leave last selection - SHOW ALL SELECTIONS
                result[0].layer.select([result[0].snappedAtGeometry])
                #a=result[0].layer.select([result[0].snappedAtGeometry])
                #feat = QgsFeature()
                geometry = self.snappFeat.geometry()
                x=geometry.asPoint().x()
                y=geometry.asPoint().y()
                
                # Get selected feature (at this moment it will have one and only one)
                feature = self.snappFeat
                node_id = feature.attribute('node_id')

                # Check if one node is not selected two or more times
                if node_id not in self.list_of_selected_nodes:
                    self.list_of_selected_nodes.append(node_id)
                    self.nodes.append(QgsPoint(x, y))
                      
                else :
                # Show warning message
                    message = "Node "+node_id+" is alredy selected"
                    self.controller.show_info(message, context_name='ui_message')

            
            if len(self.nodes)==1:
                start_point_id = self.list_of_selected_nodes[0]
                start_point = self.dlg.findChild(QLineEdit, "start_point")  
                utils_giswater.setText("start_point", start_point_id)
            if len(self.nodes)==2:
                end_point_id = self.list_of_selected_nodes[1]
                end_point = self.dlg.findChild(QLineEdit, "end_point")  
                utils_giswater.setText("end_point", end_point_id)
                
                self.shortest_path(self.list_of_selected_nodes[0],self.list_of_selected_nodes[1])

                
            '''
            # WIP
            # To do: On selectionon of 2nd node open form
            if len(self.list_of_selected_nodes)>2:
                # Create the dialog
                #self.dlg = DrawProfile()
                #utils_giswater.setDialog(self.dlg)

                # Create signals
                self.dlg.findChild(QPushButton, "draw").clicked.connect(self.paintEvent)

                self.tbl_list_node = self.dlg.findChild(QListWidget, "tbl_list_node")
                self.tbl_list_arc = self.dlg.findChild(QListWidget, "tbl_list_arc")

                # Fill listWidget with node_id and arc_id ( shortest path )
                self.fill_listWidget()

                # Call function if arc is selected in a list of drawn arcs
                self.tbl_list_arc.itemClicked.connect(self.select_arc)

                # Open the dialog
                #self.dlg.exec_()
            '''
            
    
    def set_points(self,widget):
    
        if widget == start_point:
            start_point = self.dlg.findChild(QLineEdit, "start_point")  
            utils_giswater.setText("start_point", node_id)
        if widget == end_point:
            start_point = self.dlg.findChild(QLineEdit, "end_point")  
            utils_giswater.setText("end_point", node_id)
            # activate shortest path
        


    def activate(self):

        # Check button
        self.action().setChecked(True)

        self.dlg = DrawProfile()
        utils_giswater.setDialog(self.dlg)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        self.dlg.findChild(QPushButton, "add_start_point").clicked.connect(self.btn_activate_snapping)
        #self.dlg.findChild(QPushButton, "btn_draw").clicked.connect(self.paintEvent)
        
        self.btn_save_profile = self.dlg.findChild(QPushButton, "btn_save_profile")  
        self.btn_save_profile.clicked.connect(self.save_profile)

        
        self.btn_load_profile = self.dlg.findChild(QPushButton, "btn_load_profile")  
        self.btn_load_profile.clicked.connect(self.load_profile)

        
        self.profile_id = self.dlg.findChild(QLineEdit, "profile_id")  
        self.widget_start_point = self.dlg.findChild(QLineEdit, "start_point") 
        self.widget_end_point = self.dlg.findChild(QLineEdit, "end_point") 
        
        self.dlg.show()
        
        
    def save_profile(self):
    
        id = self.profile_id.text()
        start_point = self.widget_start_point.text()
        end_point = self.widget_end_point.text()
       
        # wip - check if id exist in dB
        
        
        n = len(self.arc_id)
        for i in range(n):
            sql = "INSERT INTO "+self.schema_name+".anl_arc_profile_value (profile_id, arc_id, start_point, end_point) "
            sql+= " VALUES ('"+id+"','"+self.arc_id[i]+"','"+start_point+"','"+end_point+"')"
            #self.controller.execute_sql(sql) 
            status = self.controller.execute_sql(sql) 

            if not status:
                message = "Error inserting profile table, you need to review data"
                self.controller.show_warning(message, context_name='ui_message') 
                return
      
        # Show message to user
        message = "Values has been updated"
        self.controller.show_info(message)
        
        
    def load_profile(self):

        self.dlg_load = LoadProfiles()
        utils_giswater.setDialog(self.dlg_load)
        
        self.btn_open = self.dlg_load.findChild(QPushButton, "btn_open")  
        self.btn_open.clicked.connect(self.open_profile)
        
        self.tbl_profiles = self.dlg_load.findChild(QListWidget, "tbl_profiles") 
        sql = "SELECT DISTINCT(profile_id) FROM "+self.schema_name+".anl_arc_profile_value"
        row = self.controller.get_rows(sql)
        m=len(row)
       
        for i in range(m):
            item_arc = QListWidgetItem(row[i][0])
            self.tbl_profiles.addItem(item_arc)
            
         
        self.dlg_load.open()
        self.dlg.close()
        
        
    def open_profile(self):
    
        # Selected item from list 
        selected_profile = self.tbl_profiles.currentItem().text()
        
        # Get data from DB for selected item| profile_id, start_point, end_point
        sql = "SELECT start_point,end_point FROM"+self.schema_name+".anl_arc_profile_value WHERE profile_id ='"+selected_profile+"'"
        row = self.controller.get_rows(sql)
        start_point=row[0][0]
        end_point=row[0][1]
        
        # Fill widgets of form draw_profile | profile_id, start_point, end_point
        Start_point = self.dlg.findChild(QLineEdit, "start_point")  
        Start_point.setText(str(start_point))
        
        End_point = self.dlg.findChild(QLineEdit, "end_point")  
        End_point.setText(str(end_point))
        
        Profile_id = self.dlg.findChild(QLineEdit, "profile_id")  
        Profile_id.setText(str(selected_profile))
        
        # Get data from DB for selected item| tbl_list_arc
        tbl_list_arc = self.dlg.findChild(QListWidget, "tbl_list_arc") 
        sql = "SELECT arc_id FROM "+self.schema_name+".anl_arc_profile_value WHERE profile_id ='"+selected_profile+"'"
        row = self.controller.get_rows(sql)
      
        # Fill widget list_of_arcs
        row = self.controller.get_rows(sql)
        m=len(row)
       
        for i in range(m):
            item_arc = QListWidgetItem(str(row[i][0]))
            tbl_list_arc.addItem(item_arc)
        
        self.dlg_load.close()
        self.dlg.open()
        
        
    def btn_activate_snapping(self):
        # Store user snapping configuration
        self.snapperManager.storeSnappingOptions()

        # Clear snapping
        self.snapperManager.clearSnapping()

        # Set snapping to node

        self.snapperManager.snapToNode()

        # Change cursor
        self.canvas.setCursor(self.cursor)

        # Show help message when action is activated
        if self.show_help:
            message = "Select the node inside a pipe by clicking on it and it will be removed"
            self.controller.show_warning(message, context_name='ui_message')
        
        
    def deactivate(self):

        # Check button
        self.action().setChecked(False)

        # Restore previous snapping
        self.snapperManager.recoverSnappingOptions()

        # Recover cursor
        self.canvas.setCursor(self.stdCursor)

        # Removehighlight
        self.h = None


    def paintEvent(self,arc_id,node_id):
        '''
        Parent function - Draw profiles
        '''
        # Control current layer (due to QGIS bug in snapping system)
        if self.canvas.currentLayer() == None:
            self.iface.setActiveLayer(self.layer_node[0])
            
        # arc_id ,node_id list of nodes and arc form dijkstra algoritam
        self.set_parameters(arc_id,node_id)
        self.fill_memory(arc_id,node_id)
        self.set_table_parameters()

        # Start drawing
        # Draw first | start node
        # Function self.draw_first_node(start_point, top_elev, ymax, z1, z2, cat_geom1, geom1)
        self.draw_first_node(self.memory[0][0], self.memory[0][1], self.memory[0][2], self.memory[0][3],
                             self.memory[0][4], self.memory[0][5], self.memory[0][6],0)

        # Draw nodes between first and last node
        # Function self.draw_nodes(start_point, top_elev, ymax, z1, z2, cat_geom1, geom1, index)
        for i in range(1, self.n - 1):
            self.draw_nodes(self.memory[i][0], self.memory[i][1], self.memory[i][2], self.memory[i][3],
                            self.memory[i][4], self.memory[i][5], self.memory[i][6], i)
            self.draw_arc()
            self.draw_ground()

        # Draw last node
        self.draw_last_node(self.memory[self.n - 1][0], self.memory[self.n - 1][1], self.memory[self.n - 1][2], self.memory[self.n - 1][3],
                            self.memory[self.n - 1][4], self.memory[self.n - 1][5], self.memory[self.n - 1][6], self.n - 1)
        self.draw_arc()
        self.draw_ground()

        self. draw_table_horizontals()
        self.set_properties()

        self.draw_coordinates()
        self.draw_grid()

        # Clean array
        #self.list_of_selected_nodes.clear()
        #self.list_of_selected_arcs.clear()
        
        # Maximeze window ( after drawing )
        mng = plt.get_current_fig_manager()
        mng.window.showMaximized()
        plt.show()

        # Action on resizeing window
        cid = self.fig1.canvas.mpl_connect('resize_event',self.on_resize)
     


    def set_properties(self):
        ''' Set properties of main window '''
        
        # Set window name
        self.win = plt.gcf()
        self.win.canvas.set_window_title('Draw Profile')

        self.axes = plt.gca()
        # Hide axes
        self.axes.set_axis_off()
        # Set background color of window
        self.fig1 = plt.figure(1)
        self.rect = self.fig1.patch
        self.rect.set_facecolor('white')

        # Set axes
        # Set x-axes
        #x_min = round(self.memory[0][0] - self.fix_x - self.fix_x * Decimal(0.15))
        #x_max = round(self.memory[self.n - 1][0] + self.fix_x * Decimal(0.15))
        x_min = round(self.memory[0][0] - self.fix_x - self.fix_x * Decimal(0.15))
        x_max = round(self.memory[self.n - 1][0] + self.fix_x + self.fix_x * Decimal(0.15))
        self.axes.set_xlim([x_min, x_max])
        # Set y-axes
        y_min = round(self.min_top_elev - self.z - self.height_row*Decimal(1.5))
        y_max = round(self.max_top_elev +self.height_row*Decimal(1.5))
        self.axes.set_ylim([y_min, y_max])


    def set_parameters(self,arc_id,node_id):
        '''
        Get and calculate parameters and values for drawing
        '''
        self.list_of_selected_arcs = arc_id
        self.list_of_selected_nodes = node_id
        
        self.gis_length = [0]
        self.start_point = [0]
        self.arc_id = []

        # Get arcs between nodes ( on shortest path )
        self.n= len(self.list_of_selected_nodes)
      
        # Get length (gis_length) of arcs and save them in separate list ( self.gis_length )
        for arc_id in self.list_of_selected_arcs:
            # Get gis_length from v_edit_arc
            sql = "SELECT gis_length"
            sql += " FROM "+self.schema_name+".v_edit_arc"
            sql += " WHERE arc_id='" + str(arc_id) + "'"
            row = self.controller.get_rows(sql)

            # First member need to be 0
            i = 1
            self.gis_length.append(row[0][0])

        # Calculate start_point ( coordinates ) of drawing for each node
        n = len(self.gis_length)
        for i in range(1, n):
            x = self.start_point[i - 1] + self.gis_length[i]
            self.start_point.append(x)
            i = i + 1


    def fill_memory(self,arc_id,node_id):
        ''' Get parameters from data base
        Fill self.memory with parameterspostgres
        '''
        self.memory = []

        i = 0
        # Get parameters and fill the memory
        self.list_of_selected_nodes = node_id

        for node_id in self.list_of_selected_nodes:

            # start_point = self.start_point[i-1] + gis_length[i]
            # self.parameters : list of parameters for one node
            # self.parameters [start_point, top_elev, y_max,z1, z2, cat_geom1, geom1, slope, elev1, elev2,y1 ,y2, node_id, elev]
            self.parameters = [self.start_point[i], None, None, None, None, None, None, None, None, None, None, None, None,
                              None]
            # Get data top_elev ,y_max, elev, nodecat_id from v_edit_node
            sql = "SELECT top_elev,ymax,elev,nodecat_id"
            # sql += " FROM " + self.schema_name + ".     "
            sql += " FROM "+self.schema_name+".v_edit_node"
            sql += " WHERE node_id='" + str(node_id) + "'"
            row = self.controller.get_rows(sql)
            self.parameters[1] = row[0][0]
            self.parameters[2] = row[0][1]
            self.parameters[13] = row[0][2]
            nodecat_id = row[0][3]

            # Get data z1, z2 ,cat_geom1 ,elev1 ,elev2 , y1 ,y2 ,slope from v_edit_arc
            sql = "SELECT z1,z2,cat_geom1,elev1,elev2, y1,y2,slope"
            # sql += " FROM " + self.schema_name + ".     "
            sql += " FROM "+self.schema_name+".v_edit_arc"
            sql += " WHERE node_1='" + str(node_id) + "'"
            row = self.controller.get_rows(sql)
            self.parameters[3] = row[0][0]
            self.parameters[4] = row[0][1]
            self.parameters[5] = row[0][2]
            self.parameters[8] = row[0][3]
            self.parameters[9] = row[0][4]
            self.parameters[10] = row[0][5]
            self.parameters[11] = row[0][6]
            self.parameters[7] = row[0][7]

            # Geom1 from cat_node
            sql = "SELECT geom1"
            # sql += " FROM " + self.schema_name + ".     "
            sql += " FROM "+self.schema_name+".cat_node"
            sql += " WHERE id='" + str(nodecat_id) + "'"
            row = self.controller.get_rows(sql)
            self.parameters[6] = row[0][0]

            # Set node_id in memory
            self.parameters[12] = node_id

            self.memory.append(self.parameters)
            i = i + 1

        # Check if we have all data for drawing
        if 'None' in self.memory:
            message = "Missing some data"
            self.controller.show_info(message, context_name='ui_message')
            return


    def draw_first_node(self, start_point, top_elev, ymax, z1, z2, cat_geom1, geom1,indx):
        ''' Draw first node '''

        # Get number of pixels by unit (coordinate [1,1])
        # Transform coordinate between unut and pixels
        # inches = axes.transData.transform((1, 1))

        axes = plt.gca()

        # Draw first node
        ytop = ymax - z1 - cat_geom1
        x = [0, -(geom1), -(geom1), (geom1), (geom1)]
        y = [top_elev, top_elev, top_elev - ymax, top_elev - ymax, top_elev - ymax + z1]

        x1 = [geom1, geom1, 0]
        y1 = [top_elev - ymax + z1 + cat_geom1, top_elev, top_elev]
        plt.plot(x, y, 'black')
        plt.plot(x1, y1, 'black')
        plt.show()

        self.first_top_x = 0
        self.first_top_y = top_elev

        # Draw fixed part of table
        self.draw_fix_table(start_point)


    def draw_fix_table(self,start_point):
        ''' Draw fixed part of table'''

        # DRAW TABLE - FIXED PART
        # Draw fixed part of table
        self.draw_marks(0)


        # Vertical line [-1,0]
        x = [start_point - self.fix_x * Decimal(0.2), start_point - self.fix_x * Decimal(0.2)]
        y = [self.min_top_elev - 1 * self.height_row, self.min_top_elev - 6 * self.height_row]
        plt.plot(x, y, 'black')

        # Vertical line [-2,0]
        x = [start_point - self.fix_x * Decimal(0.75), start_point - self.fix_x * Decimal(0.75)]
        y = [self.min_top_elev - 2 * self.height_row, self.min_top_elev - 5 * self.height_row]
        plt.plot(x, y, 'black')

        # Vertical line [-3,0]
        x = [start_point - self.fix_x, start_point - self.fix_x]
        y = [self.min_top_elev - 1 * self.height_row, self.min_top_elev - 6 * self.height_row]
        plt.plot(x, y, 'black')

        # Fill the fixed part of table with data - draw text
        # Called just with first node
        self.data_fix_table(start_point)


    def draw_marks(self,start_point):
        ''' Draw marks for each node'''
        # Vertical line [0,0]
        x = [start_point, start_point]
        y = [self.min_top_elev - 1 * self.height_row,
             self.min_top_elev - 2 * self.height_row - Decimal(0.1) * self.height_row]
        plt.plot(x, y, 'black')

        # Vertical lines [0,0] - marks
        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(2.9) * self.height_row, self.min_top_elev - Decimal(3.1) * self.height_row]
        plt.plot(x, y, 'black')

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(3.9) * self.height_row, self.min_top_elev - Decimal(4.1) * self.height_row]
        plt.plot(x, y, 'black')

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(4.9) * self.height_row, self.min_top_elev - Decimal(5.1) * self.height_row]
        plt.plot(x, y, 'black')

        x = [start_point, start_point]
        y = [self.min_top_elev - Decimal(5.9) * self.height_row, self.min_top_elev - Decimal(6.1) * self.height_row]
        plt.plot(x, y, 'black')


    def data_fix_table(self,start_point):
        ''' FILL THE FIXED PART OF TABLE WITH DATA - DRAW TEXT '''

        center = self.gis_length[1] / 2

        c = (self.fix_x - self.fix_x * Decimal(0.2)) / 2
        plt.text(-(c + self.fix_x * Decimal(0.2)),
                 self.min_top_elev - 1 * self.height_row - Decimal(0.45) * self.height_row, 'DIAMETER', fontsize=7.5,
                 horizontalalignment='center')


        plt.text(-(c + self.fix_x * Decimal(0.2)),
                 self.min_top_elev - 1 * self.height_row - Decimal(0.80) * self.height_row, 'SLP. / LEN.', fontsize=7.5,
                 horizontalalignment='center')

        c = (self.fix_x * Decimal(0.25)) / 2
        plt.text(-(c + self.fix_x * Decimal(0.74)),
                 self.min_top_elev - Decimal(2) * self.height_row - self.height_row * 3 / 2, 'ORDINATES', fontsize=7.5,
                 rotation='vertical', horizontalalignment='center', verticalalignment='center')

        plt.text(-self.fix_x * Decimal(0.70), self.min_top_elev - Decimal(2.05) * self.height_row - self.height_row / 2,
                 'TOP ELEV', fontsize=7.5, verticalalignment='center')
        plt.text(-self.fix_x * Decimal(0.70), self.min_top_elev - Decimal(3.05) * self.height_row - self.height_row / 2,
                 'Y MAX', fontsize=7.5, verticalalignment='center')
        plt.text(-self.fix_x * Decimal(0.70), self.min_top_elev - Decimal(4.05) * self.height_row - self.height_row / 2,
                 'ELEV', fontsize=7.5, verticalalignment='center')

        c = (self.fix_x - self.fix_x * Decimal(0.2)) / 2
        plt.text(-(c + self.fix_x * Decimal(0.2)),
                 self.min_top_elev - Decimal(self.height_row * 5 + self.height_row / 2), 'NODE ID', fontsize=7.5,
                 horizontalalignment='center', verticalalignment='center')

        # Fill table with values
        self.fill_data(0, 0)


    def draw_nodes(self, start_point, top_elev, ymax, z1, z2, cat_geom1, geom1, indx):
        ''' Draw nodes between first and last node '''

        ytop1 = ymax - z1 - cat_geom1
        ytop2 = ymax - z2 - cat_geom1

        x = [start_point, start_point - (geom1), start_point - (geom1)]
        y = [top_elev, top_elev, top_elev - ytop2]

        x1 = [start_point - (geom1), start_point - (geom1), start_point + (geom1), start_point + (geom1)]
        y1 = [top_elev - ytop2 - cat_geom1, top_elev - ymax, top_elev - ymax, top_elev - ymax + z1]

        x2 = [start_point + (geom1),start_point + (geom1), start_point]
        y2 = [top_elev - ytop1, top_elev, top_elev]

        plt.plot(x, y, 'black')
        plt.plot(x1, y1, 'black')
        plt.plot(x2, y2, 'black')
        plt.show()

        # index -1 for node before
        # memory[[indx-1][]]
        self.x = self.memory[indx - 1][6] + self.memory[indx - 1][0]
        # top_elev - ymax + z1 + cut_geom1
        self.y = self.memory[indx - 1][1] - self.memory[indx - 1][2] + self.memory[indx - 1][3] + self.memory[indx - 1][5]

        self.x1 = self.memory[indx - 1][6] + self.memory[indx - 1][0]
        self.y1 = self.y1 = self.memory[indx - 1][1] - self.memory[indx - 1][2] + self.memory[indx - 1][3]

        self.x2 = (start_point - (geom1))
        self.y2 = top_elev - ytop2
        self.x3 = (start_point - (geom1))
        self.y3 = top_elev - ytop2 - cat_geom1

        self.node_top_x = start_point
        self.node_top_y = top_elev

        self.first_top_x = self.memory[indx - 1][0]
        self.first_top_y = self.memory[indx - 1][1]

        # DRAW TABLE-MARKS
        self.draw_marks(start_point)

        # Fill table
        self.fill_data(start_point,indx)


    def fill_data(self,start_point,indx):

        #self.n = len(self.list_of_selected_nodes)

        # Fill top_elevation and node_id for all nodes
        # Fill top_elevation
        plt.annotate(' ' + '\n' + str(round(self.memory[indx][1], 2)) + '\n' + ' ',
                     xy=(Decimal(start_point), self.min_top_elev - Decimal(self.height_row * 2 + self.height_row / 2)),
                     fontsize=7.5, rotation='vertical', horizontalalignment='center', verticalalignment='center')

        # Draw node_id
        plt.text(0 + start_point, self.min_top_elev - Decimal(self.height_row * 5 + self.height_row / 2),
                 self.memory[indx][12], fontsize=7.5,
                 horizontalalignment='center', verticalalignment='center')

        # Fill y_max and alevation
        # 1st node : y_max,y2 and top_elev, elev2
        if indx == 0:
            # Fill y_max
            plt.annotate(' ' + '\n' + str(round(self.memory[0][2], 2)) + '\n' + str(round(self.memory[0][10], 2)),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * 3 + self.height_row / 2)), fontsize=7.5,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill elevation
            plt.annotate(' ' + '\n' + str(round(self.memory[0][13], 2)) + '\n' + str(round(self.memory[0][8], 2)),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * 4 + self.height_row / 2)), fontsize=7.5,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

        # Last node : y_max,y1 and top_elev, elev1
        elif (indx == self.n-1):
            # Fill y_max
            plt.annotate(str(round(self.memory[indx-1][11], 2)) + '\n' + str(round(self.memory[indx][2], 2)) + '\n' + ' ',
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * 3 + self.height_row / 2)), fontsize=7.5,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill elevation
            plt.annotate(str(round(self.memory[indx-1][9], 2)) + '\n' + str(round(self.memory[indx][13], 2)) + '\n' + ' ',
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * 4 + self.height_row / 2)), fontsize=7.5,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')
        # Nodes between 1st and last node : y_max,y1,y2 and top_elev, elev1, elev2
        else:
            # Fill y_max
            plt.annotate(str(round(self.memory[indx-1][11], 2)) + '\n' + str(round(self.memory[indx][2], 2)) + '\n' + str(round(self.memory[indx][10], 2)),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * 3 + self.height_row / 2)), fontsize=7.5,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')

            # Fill elevation
            plt.annotate(str(round(self.memory[indx-1][9], 2)) + '\n' + str(round(self.memory[indx][13], 2)) + '\n' + str(round(self.memory[indx][8], 2)),
                         xy=(Decimal(0 + start_point),
                             self.min_top_elev - Decimal(self.height_row * 4 + self.height_row / 2)), fontsize=7.5,
                         rotation='vertical', horizontalalignment='center', verticalalignment='center')


        # Fill diameter and slope / length for all nodes except last node
        if (indx != self.n - 1):
            # Draw diameter
            center = self.gis_length[indx + 1] / 2
            plt.text(center + start_point, self.min_top_elev - 1*self.height_row - Decimal(0.45)*self.height_row, round(self.memory[indx][5], 2),
                     fontsize=7.5,horizontalalignment='center')  # PUT IN THE MIDDLE PARAMETRIZATION
            # Draw slope / length
            slope = str(round((self.memory[indx][7]*100),2))
            length = str(round(self.gis_length[indx+1],2))

            plt.text(center + start_point, self.min_top_elev - 1*self.height_row - Decimal(0.8)*self.height_row, slope + '%/' + length,
                     fontsize=7.5, horizontalalignment='center')  # PUT IN THE MIDDLE PARAMETRIZATION



    def draw_last_node(self, start_point, top_elev, ymax, z1, z2, cat_geom1, geom1, indx):

        x = [start_point, start_point - (geom1), start_point - (geom1)]
        # y = [top_elev, top_elev,top_elev-ytop2+cat_geom1]
        y = [top_elev, top_elev, top_elev - ymax + z2 + cat_geom1]

        x1 = [start_point - geom1, start_point - geom1, start_point + geom1, start_point + geom1, start_point]
        y1 = [top_elev - ymax + z2, top_elev - ymax, top_elev - ymax, top_elev, top_elev]

        plt.plot(x, y, 'black')
        plt.plot(x1, y1, 'black')
        plt.show()

        self.x = self.memory[indx - 1][6] + self.memory[indx - 1][0]
        # top_elev - ymax + z1 + cut_geom1
        self.y = self.memory[indx - 1][1] - self.memory[indx - 1][2] + self.memory[indx - 1][3] + self.memory[indx - 1][5]

        self.x1 = self.memory[indx - 1][6] + self.memory[indx - 1][0]
        self.y1 = self.y1 = self.memory[indx - 1][1] - self.memory[indx - 1][2] + self.memory[indx - 1][3]

        self.x2 = (start_point - (geom1))
        self.y2 = top_elev - ymax + z2 + cat_geom1
        self.x3 = (start_point - (geom1))
        self.y3 = top_elev - ymax + z2

        self.first_top_x = self.memory[indx - 1][0]
        self.first_top_y = self.memory[indx - 1][1]

        self.node_top_x = start_point
        self.node_top_y = top_elev

        # DRAW TABLE
        # DRAW TABLE-MARKS
        self.draw_marks(start_point)
        # Fill table
        self.fill_data(start_point, indx)


    def set_table_parameters(self):

        # Search y coordinate min_top_elev ( top_elev- ymax)
        self.min_top_elev = self.memory[0][1] - self.memory[0][2]
        #n = len(self.list_of_selected_nodes)
        for i in range(1, self.n):
            if (self.memory[i][1] - self.memory[i][2]) < self.min_top_elev:
                self.min_top_elev = self.memory[i][1] - self.memory[i][2]
        # Search y coordinate max_top_elev
        self.max_top_elev = self.memory[0][1]
        for i in range(1, self.n):
            if (self.memory[i][1]) > self.max_top_elev:
                self.max_top_elev = self.memory[i][1]

        # Calculating dimensions of x-fixed part of table 
        self.fix_x = Decimal(0.1 / (1 - 0.1)) * self.memory[self.n - 1][0]

        # Calculating dimensions of y-fixed part of table 
        # Height y = height of table + height of graph
        self.z = self.max_top_elev - self.min_top_elev
        self.height_row = (self.z * Decimal(0.97)) / Decimal(5)

        # Height of graph + table 
        self.height_y = self.z * 2


    def draw_table_horizontals(self):
        ''''''
        self.set_table_parameters()

        #self.n_node = len(self.list_of_selected_nodes)
        # DRAWING TABLE
        # Nacrtat horizontale
        x = [self.memory[self.n - 1][0], self.memory[0][0] - self.fix_x]
        # x = [self.memory[n - 1][0], self.memory[0][0] - 120]
        y = [self.min_top_elev - self.height_row, self.min_top_elev - self.height_row]
        # y = [self.min_top_elev - 1, self.min_top_elev - 1]
        plt.plot(x, y, 'black')

        x = [self.memory[self.n - 1][0], self.memory[0][0] - self.fix_x]
        # x = [self.memory[n - 1][0], self.memory[0][0] - 120]
        y = [self.min_top_elev - 2 * self.height_row, self.min_top_elev - 2 * self.height_row]
        plt.plot(x, y, 'black')

        # horizontale krace
        x = [self.memory[self.n - 1][0], self.memory[0][0] - self.fix_x * Decimal(0.75)]
        # x = [self.memory[n - 1][0], self.memory[0][0] - 90]
        y = [self.min_top_elev - 3 * self.height_row, self.min_top_elev - 3 * self.height_row]
        plt.plot(x, y, 'black')
        x = [self.memory[self.n - 1][0], self.memory[0][0] - self.fix_x * Decimal(0.75)]
        # x = [self.memory[n - 1][0], self.memory[0][0] - 90]
        y = [self.min_top_elev - 4 * self.height_row, self.min_top_elev - 4 * self.height_row]
        plt.plot(x, y, 'black')
        # zadnje dvije linije
        x = [self.memory[self.n - 1][0], self.memory[0][0] - self.fix_x]
        # x = [self.memory[n - 1][0], self.memory[0][0] - 120]
        y = [self.min_top_elev - 5 * self.height_row, self.min_top_elev - 5 * self.height_row]
        plt.plot(x, y, 'black')
        x = [self.memory[self.n - 1][0], self.memory[0][0] - self.fix_x]
        # x = [self.memory[n - 1][0], self.memory[0][0] - 120]
        y = [self.min_top_elev - 6 * self.height_row, self.min_top_elev - 6 * self.height_row]
        plt.plot(x, y, 'black')


    def on_resize(self,event):
        ''' TO DO '''
        pass
        # Clear the entire current figure
        #plt.clf()
        #self.paintEvent()
        #plt.rcParams['xtick.labelsize'] = 2
        #plt.rcParams.update({'font-size':22})
        #plt.draw()
        #res.remove()


    def check_colision(self,gis_length,pix):
        '''TO DO'''
        # Checking colision just for text

        axes = plt.gca()
        [x,y] = axes.transData.transform([(0,1),(1,0)])

        # available_length in pixels
        available_length = 2500

        # gis_lenght in pixels, x[0]-pixels by unit
        gis_length_pix = Decimal(gis_length)*Decimal(x[0])

        # if colision return 1
        if gis_length_pix > available_length:
            return 1
        #if no colision return 0
        else:
            return 0


    def draw_coordinates(self):

        start_point = self.memory[self.n - 1][0]
        geom1 = self.memory[self.n - 1][6]
        # Draw coocrinates
        x = [0, 0]
        y = [self.min_top_elev - 1 * self.height_row, self.max_top_elev + 1 * self.height_row]
        plt.plot(x, y, 'black')
        x = [start_point,start_point]
        y = [self.min_top_elev - 1 * self.height_row, self.max_top_elev + 1 * self.height_row]
        plt.plot(x, y, 'black')
        x = [0,start_point]
        y = [self.max_top_elev + 1 * self.height_row,self.max_top_elev + 1 * self.height_row]
        plt.plot(x, y, 'black')

        # Values left y_ordinate_max
        plt.text(0 - geom1*Decimal(1.5) , self.max_top_elev + self.height_row,str(round(self.max_top_elev + self.height_row,2)),fontsize=7.5,horizontalalignment='right', verticalalignment='center')

        # Loop till self.max_top_elev + height_row
        y = int(math.ceil(self.min_top_elev - 1 * self.height_row))
        x= int(math.floor(self.max_top_elev))
        for i in range(y, x):
            if i%2 == 0:
                x1 = [0, start_point]
                y1 = [i, i]
            else:
                i = i+1
                x1 = [0, start_point]
                y1 = [i, i]
            plt.plot(x1, y1, 'lightgray')
            # Values left y_ordinate_all
            plt.text(0 - geom1 * Decimal(1.5), i,str(i), fontsize=7.5, horizontalalignment='right', verticalalignment='center')


    def draw_grid(self):
        # Values right y_ordinate_max
        start_point = self.memory[self.n-1][0]
        geom1 = self.memory[self.n-1][6]
        plt.annotate('P.C. '+str(round(self.min_top_elev - 1 * self.height_row,2)) + '\n' + ' ',
                     xy=(0 - geom1*Decimal(1.5) , self.min_top_elev - 1 * self.height_row),
                     fontsize=7.5, horizontalalignment='right', verticalalignment='center')

        # Values right x_ordinate_min
        plt.annotate('0'+ '\n' + ' ',
                     xy=(0, self.max_top_elev + 1 * self.height_row),
                     fontsize=7.5, horizontalalignment='center')

        # Values right x_ordinate_max
        plt.annotate(str(round(start_point,2))+ '\n' + ' ',
                     xy=(start_point, self.max_top_elev + 1*self.height_row),
                     fontsize=7.5, horizontalalignment='center')

        # Loop from 0 to start_point(of last node) 
        y = 0
        x = int(math.floor(start_point))
        # First after 0 (first is drawn ,start from i(0)+1) 
        for i in range(50, x,50):
            x1 = [i, i]
            y1 = [self.min_top_elev - 1 * self.height_row, self.max_top_elev + 1 * self.height_row]
            plt.plot(x1, y1, 'lightgray' )
            # values left y_ordinate_all
            plt.text(0 - geom1 * Decimal(1.5), i, str(i), fontsize=7.5, horizontalalignment='right', verticalalignment='center')
            plt.text(start_point + geom1 * Decimal(1.5), i, str(i), fontsize=7.5, horizontalalignment='left', verticalalignment='center')
            # values right x_ordinate_all
            plt.annotate(str(i) + '\n' + ' ',
                         xy=(i, self.max_top_elev + 1 * self.height_row),
                         fontsize=7.5, horizontalalignment='center')


    def draw_arc(self):
        x = [self.x, self.x2]
        y = [self.y, self.y2]
        x1 = [self.x1, self.x3]
        y1 = [self.y1, self.y3]
        plt.plot(x, y, 'black')
        plt.plot(x1, y1, 'black')


    def draw_ground(self):
        # Green triangle
        plt.plot(self.first_top_x,self.first_top_y,'g^',linewidth=3.5)
        plt.plot(self.node_top_x, self.node_top_y, 'g^',linewidth=3.5)
        x = [self.first_top_x, self.node_top_x]
        y = [self.first_top_y, self.node_top_y]
        plt.plot(x, y, 'green', linestyle='dashed')


    def fill_listWidget(self):
        ''' Fill listWidget with node_id and arc_id ( shortest path ) '''

        # Fill ListWidgetItem - List of nodes
        n = len(self.list_of_selected_nodes)

        # Define empty list of arc_id's
        self.list_of_selected_arcs = []
        # Get arc of the selected nodes
        for i in range(0, n - 1):
            sql = "SELECT arc_id"
            sql += " FROM "+self.schema_name+".v_edit_arc"
            sql += " WHERE node_1='" + str(self.list_of_selected_nodes[i]) + "' AND node_2='" + str(
                self.list_of_selected_nodes[i + 1]) + "'"
            row = self.controller.get_rows(sql)
            self.list_of_selected_arcs.append(row[0][0])
            i = i + 1

    
    def shortest_path(self,start_point, end_point):
        ''' Calculating shortest path using dijkstra algoritam ''' 

        args = []

        start_point_id = start_point
        end_point_id = end_point        
    
        args.append(start_point_id)
        args.append(end_point_id)
     
        
        self.node_id = []
        self.arc_id = []
        sql = "SELECT * FROM public.pgr_dijkstra('SELECT id, source, target, cost FROM "+self.schema_name+".v_test_arc'," + start_point + "," +end_point + ",false)"
      
        rows = self.controller.get_rows(sql)
        number_nodes=len(rows)
        for i in range(0, number_nodes ):
            self.node_id.append(str(rows[i]['node']))
            self.arc_id.append(str(rows[i]['edge']))
        
        # SELECT ARCS OF SHORTEST PATH
        if rows:
            # Build an expression to select them
            m=len(self.arc_id)
            aux = "\"arc_id\" IN ("
            for i in range(m-1):
            # Get a featureIterator from this expression:
                aux += "'" + str(self.arc_id[i]) + "', "
            aux = aux[:-2] + ")"
        
            expr = QgsExpression(aux)
            '''
            if expr.hasParserError():
                message = "Expression Error: " + str(expr.parserErrorString())
                self.controller.show_warning(message, context_name='ui_message')
                return
            '''
            # Loop which is pasing trought all layer of arc_group searching for feature
            #layer_arc = self.iface.activeLayer() 
            for layer_arc in self.layer_arc_man:
                it = layer_arc.getFeatures(QgsFeatureRequest(expr))
        
                # Build a list of feature id's from the previous result
                id_list = [i.id() for i in it]

                # Select features with these id's
                layer_arc.setSelectedFeatures(id_list)
            
        # SELECT NODES OF SHORTEST PATH
        n=len(self.node_id)
        aux = "\"node_id\" IN ("
        for i in range(n):
        # Get a featureIterator from this expression:
            aux += "'" + str(self.node_id[i]) + "', "
        aux = aux[:-2] + ")"
        
        expr = QgsExpression(aux)
        '''
        if expr.hasParserError():
            message = "Expression Error: " + str(expr.parserErrorString())
            self.controller.show_warning(message, context_name='ui_message')
            return
        '''

        # Loop which is pasing trought all layer of node_group searching for feature
        for layer_node in self.layer_node_man:

            it = layer_node.getFeatures(QgsFeatureRequest(expr))
        
            # Build a list of feature id's from the previous result
            id_list = [i.id() for i in it]

            # Select features with these id's
            layer_node.setSelectedFeatures(id_list)
        
        #layer = iface.activeLayer()
        self.tbl_list_arc = self.dlg.findChild(QListWidget, "tbl_list_arc")
        m=len(self.arc_id)
        list = []

        for i in range(m-1):
            item_arc = QListWidgetItem(self.arc_id[i])
            self.tbl_list_arc.addItem(item_arc)
            #layer.changeAttributeValue(feature.id(), columnnumber, value)
            list.append(self.arc_id[i])
            
        # Remove last element from list because is -1 
        self.arc_id.pop()
    
      
        self.dlg.findChild(QPushButton, "btn_draw").clicked.connect(partial(self.paintEvent,self.arc_id,self.node_id))
        

            