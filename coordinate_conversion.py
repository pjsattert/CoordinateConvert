# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CoordinateConversion
                                 A QGIS plugin
 Convert points between 2D coordinate systems.
                              -------------------
        begin                : 2016-06-28
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Peter Satterthwaite
        email                : pjsattert@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from coordinate_conversion_dialog import CoordinateConversionDialog
import os.path
import math


class CoordinateConversion:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CoordinateConversion_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = CoordinateConversionDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&CoordinateConversion')
        
        self.dlg.loadFilePrompt.hide()
        self.dlg.inputFile.hide()
        self.dlg.loadFileButton.hide()
        self.dlg.loadLayerPrompt.hide()
        self.dlg.layerSelect.hide()
        self.dlg.newLayerName_Label.hide()
        self.dlg.newLayerName.hide()
        
        self.toolbar = self.iface.addToolBar(u'CoordinateConversion')
        self.toolbar.setObjectName(u'CoordinateConversion')
        self.dlg.inputFile.clear()
        self.dlg.loadFileButton.clicked.connect(self.select_input_file)
        self.dlg.outputFile.clear()
        self.dlg.saveFileButton.clicked.connect(self.select_output_file)
        self.dlg.convertButton.clicked.connect(self.calculateAndShow)
        self.dlg.importFromText.toggled.connect(self.importFromText_selected)
        self.dlg.importFromLayer.toggled.connect(self.importFromLayer_selected)
        self.dlg.checkNewLayer.stateChanged.connect(self.checkNewLayer_stateChanged)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CoordinateConversion', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CoordinateConversion/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Convert coordinate system'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&CoordinateConversion'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def importFromText_selected(self):
        self.dlg.loadFilePrompt.show()
        self.dlg.inputFile.show()
        self.dlg.loadFileButton.show()
        self.dlg.loadLayerPrompt.hide()
        self.dlg.layerSelect.hide()
        self.dlg.inputInstruction.hide()

    def importFromLayer_selected(self):
        self.dlg.loadFilePrompt.hide()
        self.dlg.inputFile.hide()
        self.dlg.loadFileButton.hide()
        self.dlg.loadLayerPrompt.show()
        self.dlg.layerSelect.show()
        self.dlg.inputInstruction.hide()

    def checkNewLayer_stateChanged(self):
        if (self.dlg.checkNewLayer.isChecked()):
            self.dlg.newLayerName_Label.show()
            self.dlg.newLayerName.show()
        else:
            self.dlg.newLayerName_Label.hide()
            self.dlg.newLayerName.hide()
            
    def select_input_file(self):
        loadFileName = QFileDialog.getOpenFileName(self.dlg, "Open text file", "", "*.txt")
        self.dlg.inputFile.setText(loadFileName)
        
    def select_output_file(self):
        saveFileName = QFileDialog.getSaveFileName(self.dlg, "Save text file", "", "*.txt")
        self.dlg.outputFile.setText(saveFileName)
        
    def calculateAngle(self, p1x1, p1y1, p1x2, p1y2, p2x1, p2y1, p2x2, p2y2, xDiff, yDiff):
        p1x1 += xDiff
        p2x1 += xDiff
        p1y1 += yDiff
        p2y1 += yDiff
        leg = math.sqrt(math.pow((p2x1 - p1x1),2)+ math.pow((p2y1 - p1y1),2))
        base = math.sqrt(math.pow((p2x2 - p2x1),2) + math.pow((p2y2 - p2y1),2))
        sign = 0
        slopeNew = 0
        slopeBase = 0
        if (p2x2 - p1x1 != 0):
            slopeNew = (p2y2 - p1y1)/(p2x2 - p1x1)
        if (p2x2 - p2x1 != 0):        
            slopeBase = (p2y2 - p2y1)/(p2x2 - p2x1)
        if (p2x2 - p1x1 != 0) and (p2x2 - p2x1 != 0):
            if (slopeBase > slopeNew) or (slopeBase < 0):
                sign = 1
            if (0 < slopeBase < slopeNew):
                sign = -1
        if (p2x2 - p1x1 == 0):
            if (slopeBase > 0):
                sign = -1
            if (slopeBase <0):
                sign = 1
        if (p2x2 - p2x1 == 0):
            if (slopeNew > 0):
                sign = 1
            if (slopeNew < 0):
                sign = -1
        angle = sign * 2 * math.asin((base / 2)/leg)
        return angle
    
    def getOriginalPoints(self):
        originalPoints = []
        if self.dlg.importFromText.isChecked():
            originalPoints = self.getPointsFromFile()
        if self.dlg.importFromLayer.isChecked():
            originalPoints = self.getPointsFromLayer()
        return originalPoints
    
    def getPointsFromFile(self):
        filePoints = []
        pointFileName = self.dlg.inputFile.text()
        pointFile = open(pointFileName, 'r')
        fileLines = pointFile.readlines()
        for q in range (1, len(fileLines)):
            tempString = fileLines[q]
            tempList = tempString.split(",")
            tempPoint = gisPoint(tempList[0], tempList[1], tempList[2], tempList[3], tempList[4])
            filePoints.append(tempPoint)
        pointFile.close()
        return filePoints
    
    def getPointsFromLayer(self):
        layers = self.iface.legendInterface().layers()
        selectedLayerIndex = self.dlg.layerSelect.currentIndex()
        selectedLayer = layers[selectedLayerIndex]
        fields = selectedLayer.pendingFields()
        fieldnames = [field.name() for field in fields]
        
        layerPoints = []
        for t in selectedLayer.getFeatures():
            tempPoint = gisPoint(t[0], t[1], t[2], t[3], t[4])
            layerPoints.append(tempPoint)
        return layerPoints
        
    def calculateAndShow(self):
        pt1x1 = float(self.dlg.point1ogX.text())
        pt1y1 = float(self.dlg.point1ogY.text())
        pt1x2 = float(self.dlg.point1newX.text())
        pt1y2 = float(self.dlg.point1newY.text())
        pt2x1 = float(self.dlg.point2ogX.text())
        pt2y1 = float(self.dlg.point2ogY.text())
        pt2x2 = float(self.dlg.point2newX.text())
        pt2y2 = float(self.dlg.point2newY.text())
        xTranslation = pt1x2 - pt1x1
        yTranslation = pt1y2 - pt1y1
        angle = self.calculateAngle(pt1x1, pt1y1, pt1x2, pt1y2, pt2x1, pt2y1, pt2x2, pt2y2, xTranslation, yTranslation)
        headerFileName = self.dlg.inputFile.text()
        headerFile = open(headerFileName, 'r')
        outputString = headerFile.readline()
        originalPoints = []
        originalPoints = self.getOriginalPoints();
        convertedPoints = []
        for i in range(0, len(originalPoints)):
            temp = originalPoints[i]
            temp.convertPoint(xTranslation, yTranslation, pt1x2, pt1y2, angle)
            convertedPoints.append(temp)
        for c in range(0, len(convertedPoints)):
            outputString += convertedPoints[c].getPointAsString()
        self.showOutputInDialog(outputString)
        self.saveNewPointFile(outputString)
        if (self.dlg.checkNewLayer.isChecked()):
            self.saveNewLayer()
    
    def saveNewPointFile(self, newText):
        fileName = self.dlg.outputFile.text()
        newFile = open(fileName, 'w')
        newFile.write(newText)
        newFile.close()
        
    def saveNewLayer(self):
        filePath = "file:///" + self.dlg.outputFile.text() + "?delimiter=%s&xField=%s&yField=%s"
        uri = filePath % (",", "x", "y") 
        layerName = self.dlg.newLayerName.text()
        vlayer = QgsVectorLayer(uri, layerName, "delimitedtext")
        QgsMapLayerRegistry.instance().addMapLayer(vlayer)
    
    def showOutputInDialog(self, output):
        pointDialog = QMessageBox()
        pointDialog.setWindowTitle("Converted Points")
        pointString = output
        #for c in range(0, len(output)):
        #    pointString += output[c].getPointAsString()
        pointDialog.setText("Your points have been successfully converted and saved.")
        #pointDialog.setText(pointString)
        pointDialog.setStandardButtons(QMessageBox.Ok)
        pointDialog.show()
        retval = pointDialog.exec_()
        
    def run(self):
        layers = self.iface.legendInterface().layers()
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        self.dlg.layerSelect.addItems(layer_list)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass

class gisPoint:
    def __init__(self, name, type, x, y, height):
        self.name = name
        self.type = type
        self.x = x
        self.y = y
        self.height = height
        
    def setName(self, newName):
        self.name = newName
        
    def setType(self, newType):
        self.type = newType
        
    def setX(self, newX):
        x = float(newX)
        
    def setY(self, newY):
        y = float(newY)
        
    def setHeight(self, newHeight):
        self.height = float(newHeight)
        
    def getName():
        return self.name
        
    def getType():
        return self.type
        
    def getX(self):
        return float(self.x)
        
    def getY(self):
        return float(self.y)
        
    def getHeight(self):
        return float(self.height)
        
    def getPointAsString(self):
        return self.name + ", " + str(self.type) + ", " + str(self.x) + ", " + str(self.y) + ", " + str(self.height)
        
    def convertPoint(self, xTrans, yTrans, rotPtX, rotPtY, angle):
        movedX = float(self.x) + xTrans
        movedY = float(self.y) + yTrans
        finalX = math.cos(angle) * (movedX - rotPtX) - math.sin(angle) * (movedY - rotPtY) + rotPtX
        finalY = math.sin(angle) * (movedX - rotPtX) + math.cos(angle) * (movedY - rotPtY) + rotPtY
        self.x = finalX
        self.y = finalY