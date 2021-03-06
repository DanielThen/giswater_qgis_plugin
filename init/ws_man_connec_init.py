'''
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
'''

# -*- coding: utf-8 -*-
import webbrowser

from PyQt4.QtGui import QAbstractItemView
from PyQt4.QtGui import QPushButton, QTableView, QTabWidget, QAction, QLineEdit, QComboBox

from functools import partial

import utils_giswater
from parent_init import ParentDialog


def formOpen(dialog, layer, feature):
    ''' Function called when a connec is identified in the map '''

    global feature_dialog
    utils_giswater.setDialog(dialog)
    # Create class to manage Feature Form interaction  
    feature_dialog = ManConnecDialog(dialog, layer, feature)
    init_config()

    
def init_config():

    # Manage 'connec_type'
    connec_type = utils_giswater.getWidgetText("connec_type") 
    utils_giswater.setSelectedItem("connec_type", connec_type)
     
    # Manage 'connecat_id'
    connecat_id = utils_giswater.getWidgetText("connecat_id") 
    utils_giswater.setSelectedItem("connecat_id", connecat_id)   
        
     
class ManConnecDialog(ParentDialog):   
    
    def __init__(self, dialog, layer, feature):
        ''' Constructor class '''
        super(ManConnecDialog, self).__init__(dialog, layer, feature)
        self.init_config_form()
        #self.controller.manage_translation('ws_man_connec', dialog)                 

        
    def init_config_form(self):
        ''' Custom form initial configuration '''

        table_element = "v_ui_element_x_connec" 
        table_document = "v_ui_doc_x_connec" 
        table_event_connec = "v_ui_om_visit_x_connec"
        table_hydrometer = "v_rtc_hydrometer"    
        table_hydrometer_value = "v_edit_rtc_hydro_data_x_connec"    
        
        # Initialize variables            
        self.table_wjoin = self.schema_name+'."v_edit_man_wjoin"' 
        self.table_tap = self.schema_name+'."v_edit_man_tap"'
        self.table_greentap = self.schema_name+'."v_edit_man_greentap"'
        self.table_fountain = self.schema_name+'."v_edit_man_fountain"'
              
        # Define class variables
        self.field_id = "connec_id"        
        self.id = utils_giswater.getWidgetText(self.field_id, False)  
        self.filter = self.field_id+" = '"+str(self.id)+"'"                       
        self.connecat_id = self.dialog.findChild(QLineEdit, 'connecat_id')
        self.connec_type = self.dialog.findChild(QComboBox, 'connec_type')        
        
        # Get widget controls      
        self.tab_main = self.dialog.findChild(QTabWidget, "tab_main")  
        self.tbl_info = self.dialog.findChild(QTableView, "tbl_info")   
        self.tbl_document = self.dialog.findChild(QTableView, "tbl_document") 
        self.tbl_event = self.dialog.findChild(QTableView, "tbl_event_connec") 
        self.tbl_hydrometer = self.dialog.findChild(QTableView, "tbl_hydrometer") 
        self.tbl_hydrometer_value = self.dialog.findChild(QTableView, "tbl_hydrometer_value")
        self.tbl_hydrometer.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_hydrometer.clicked.connect(self.check_url)

        # Manage custom fields   
        connectype_id = self.dialog.findChild(QLineEdit, "connectype_id")
        self.feature_cat_id = connectype_id.text()        
        tab_custom_fields = 4
        self.manage_custom_fields(self.feature_cat_id, tab_custom_fields)
        
        # Manage tab visibility
        self.set_tabs_visibility(tab_custom_fields - 1)  
              
        # Load data from related tables
        self.load_data()
        
        # Fill the info table
        self.fill_table(self.tbl_info, self.schema_name+"."+table_element, self.filter)
        
        # Configuration of info table
        self.set_configuration(self.tbl_info, table_element)    
        
        # Fill the tab Document
        self.fill_tbl_document_man(self.tbl_document, self.schema_name+"."+table_document, self.filter)
        self.tbl_document.doubleClicked.connect(self.open_selected_document)
        
        # Configuration of table Document
        self.set_configuration(self.tbl_document, table_document)
        
        # Fill tab event | connec
        self.fill_tbl_event(self.tbl_event, self.schema_name+"."+table_event_connec, self.filter)
        self.tbl_event.doubleClicked.connect(self.open_selected_document_event)
        
        # Configuration of table event | connec
        self.set_configuration(self.tbl_event, table_event_connec)
        
        # Fill tab hydrometer | hydrometer
        self.fill_tbl_hydrometer(self.tbl_hydrometer, self.schema_name+"."+table_hydrometer, self.filter)
        
        # Configuration of table hydrometer | hydrometer
        self.set_configuration(self.tbl_hydrometer, table_hydrometer)
       
        # Fill tab hydrometer | hydrometer value
        self.fill_tbl_hydrometer(self.tbl_hydrometer_value, self.schema_name+"."+table_hydrometer_value, self.filter)

        # Configuration of table hydrometer | hydrometer value
        self.set_configuration(self.tbl_hydrometer_value, table_hydrometer_value)
        
        # Set signals          
        self.dialog.findChild(QPushButton, "btn_doc_delete").clicked.connect(partial(self.delete_records, self.tbl_document, table_document))            
        #self.dialog.findChild(QPushButton, "delete_row_info_2").clicked.connect(partial(self.delete_records, self.tbl_info, table_element))       
        self.dialog.findChild(QPushButton, "btn_delete_hydrometer").clicked.connect(partial(self.delete_records_hydro, self.tbl_hydrometer))               
        self.dialog.findChild(QPushButton, "btn_add_hydrometer").clicked.connect(self.insert_records)
        self.open_link = self.dialog.findChild(QPushButton, "open_link")
        self.open_link.setEnabled(False)
        self.open_link.clicked.connect(self.open_url)
        
        feature = self.feature
        canvas = self.iface.mapCanvas()
        layer = self.iface.activeLayer()

        # Toolbar actions
        action = self.dialog.findChild(QAction, "actionEnabled")
        action.setChecked(layer.isEditable())
        self.dialog.findChild(QAction, "actionZoom").triggered.connect(partial(self.action_zoom_in, feature, canvas, layer))
        self.dialog.findChild(QAction, "actionCentered").triggered.connect(partial(self.action_centered,feature, canvas, layer))
        self.dialog.findChild(QAction, "actionEnabled").triggered.connect(partial(self.action_enabled, action, layer))
        self.dialog.findChild(QAction, "actionZoomOut").triggered.connect(partial(self.action_zoom_out, feature, canvas, layer))
        self.dialog.findChild(QAction, "actionLink").triggered.connect(partial(self.check_link, True))


    def check_url(self):
        """ Check URL. Enable/Disable button that opens it """
        
        selected_list = self.tbl_hydrometer.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message)
            return
        
        row = selected_list[0].row()
        url = self.tbl_hydrometer.model().record(row).value("hydrometer_link")
        if url != '':
            self.url = url
            self.open_link.setEnabled(True)
        else:
            self.open_link.setEnabled(False)


    def open_url(self):
        """ Open URL """
        webbrowser.open(self.url)
        
