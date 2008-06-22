#!/usr/bin/env python

""" Lector: ocrarea.py

    Copyright (C) 2008 Davide Setti

    This program is released under the GNU GPLv2
""" 

import sys
import Image
import os
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QApplication as qa


class OcrArea(QtGui.QGraphicsRectItem):
    
    ## static data
    resizeborder = .0
    
    def __init__(self, pos, size, type, parent = None, scene = None, areaBorder = 2, index = 0, textSize = 50):
        QtGui.QGraphicsRectItem.__init__(self, 0, 0, size.width(), size.height(), parent, scene)
        self.setPos(pos)
        
        #self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable |
            QtGui.QGraphicsItem.ItemIsFocusable |
            QtGui.QGraphicsItem.ItemIsSelectable)

        self.top = OcrAreaTop(size.width(), self, scene)
        self.left = OcrAreaLeft(size.height(), self, scene)
        self.right = OcrAreaRight(size.width(), size.height(), self, scene)
        self.bottom = OcrAreaBottom(size.width(), size.height(), self, scene)

        ## set index label
        ##TODO: set once!
        self.text = QtGui.QGraphicsTextItem("%d" % index, self)
        self.setIndex(index)
        self.setTextSize(textSize)

        ## TODO: come creare delle costanti per il tipo? (come le costanti nelle Qt) (enum?)
        self.type = type

        pen = QtGui.QPen(self.color, areaBorder, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.setPen(pen)
        self.setAcceptsHoverEvents(True)
        self.setCursor(QtCore.Qt.SizeAllCursor)


    def mouseReleaseEvent(self, event):
        self.update()
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.sEdge = ''
        QtGui.QGraphicsItem.mouseReleaseEvent(self, event)


    def setIndex(self, index):
        self.text.setPlainText("%d" % index)
        ## to prevent disturbing resize-helper events
        ## (see OcrAreaSide.mouseMoveEvent)
        self.setZValue(index*10)
        self.top.setZValue(index*10+1)
        self.left.setZValue(index*10+2)
        self.right.setZValue(index*10+3)
        self.bottom.setZValue(index*10+4)


    def setTextSize(self, size):
        font = QtGui.QFont()
        font.setPointSizeF(size)
        self.text.setFont(font)


    def contextMenuEvent(self, event):
        menu = QtGui.QMenu()
        removeAction = menu.addAction(qa.translate('QOcrWidget', "Remove"))
        menu.addSeparator()
        textAction = menu.addAction(qa.translate('QOcrWidget', "Text"))
        graphicsAction = menu.addAction(qa.translate('QOcrWidget', "Graphics"))
        selectedAction = menu.exec_(event.screenPos())

        if selectedAction == removeAction:
            self.scene().removeArea(self)
        elif selectedAction == textAction:
            self.type = 1
        elif selectedAction == graphicsAction:
            self.type = 2


    ## type property
    def _setType(self, type):
        self.__type = type
        
        if self.__type == 1:
            self.color = QtCore.Qt.darkGreen
        else: ## TODO: else -> elif ... + else raise exception
            self.color = QtCore.Qt.blue
        
        self.text.setDefaultTextColor(self.color)

        pen = self.pen()
        pen.setColor(self.color)
        self.setPen(pen)

    def _type(self):
        return self.__type

    type = property(fget=_type, fset=_setType)

    
    def sizeChange(self):
        ## TODO: reimplementare setRect e mettere questo li` dentro
        r = self.rect()
        self.top.setRect( 0, 0, r.width()+30, 30 )
        self.left.setRect( 0, 0, 30, r.height()+30 )
        self.right.setRect( 0, 0, 30, r.height()+30 )
        self.right.setPos( r.width()-15, -15 )
        self.bottom.setRect( 0, 0, r.width()+30, 30 )
        self.bottom.setPos( -15, r.height()-15 )

    
    def scale(self, value):
        print 'scale'

class OcrAreaSide(QtGui.QGraphicsRectItem):

    def __init__(self, x, y, width, height, parent, scene):
        QtGui.QGraphicsRectItem.__init__(self, 0, 0, width, height, parent, scene)
        self.setPos(x, y)
        
        self.parent = parent

        self.setAcceptsHoverEvents(True)
        self.setFlags(QtGui.QGraphicsItem.ItemIsMovable |
            QtGui.QGraphicsItem.ItemIsFocusable |
            QtGui.QGraphicsItem.ItemIsSelectable)


    def mousePressEvent(self, event):
        self.oldPoint = event.scenePos()
        QtGui.QGraphicsItem.mousePressEvent(self, event)

        self.parent.setFlag(QtGui.QGraphicsItem.ItemIsMovable, False)
        self.parent.setSelected(True)

        items = self.scene().items(event.scenePos())

        ##TODO: how do you say "decine"?
        selfdecine = round(self.zValue()/10)

        for item in items:
            itemdecine = round(item.zValue()/10)
            if itemdecine == selfdecine and item.zValue() % 10 and self.zValue() > item.zValue():
                item.mousePressEvent(event)


    def mouseMoveEvent(self, event):
        self.resizeParentItem(event.scenePos())
        self.oldPoint = event.scenePos()
        items = self.scene().selectedItems()

        for item in items:
            if self.zValue() > item.zValue():
                item.mouseMoveEvent(event)


    def resizeParentItem(self, newPoint):
        pass


    def mouseReleaseEvent(self, event):
        self.parent.setFlag(QtGui.QGraphicsItem.ItemIsMovable)

   
    def paint(self, painter, option, widget):
        pen = QtGui.QPen(QtCore.Qt.transparent, 0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawRect(self.rect())


class OcrAreaTop(OcrAreaSide):

    def __init__(self, width, parent, scene):
        OcrAreaSide.__init__(self, -15, -15, width+30, 30, parent, scene)
        

    def hoverMoveEvent(self, event):
        self.setCursor(QtCore.Qt.SizeVerCursor)


    def resizeParentItem(self, newPoint):
        diff = - newPoint.y() + self.oldPoint.y()
        
        newY = self.parent.y() - diff
        if newY > 0:
            r = self.parent.rect()
            self.parent.setPos(self.parent.x(), newY)
            self.parent.setRect(0,0,r.width(),r.height() + diff)
            self.parent.sizeChange()


class OcrAreaLeft(OcrAreaSide):

    def __init__(self, height, parent, scene):
        OcrAreaSide.__init__(self, -15, -15, 30, height+30, parent, scene)


    def hoverMoveEvent(self, event):
        items = self.scene().items(event.scenePos())
        
        selfdecine = round(self.zValue()/10)
        for item in items:
            itemdecine = round(item.zValue()/10)
            if type(item) is OcrAreaTop and itemdecine == selfdecine:
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
                return
        self.setCursor(QtCore.Qt.SizeHorCursor)
        

    def resizeParentItem(self, newPoint):
        diff = - newPoint.x() + self.oldPoint.x()
        r = self.parent.rect()

        newX = self.parent.x() - diff
        if newX > 0:
            self.parent.setPos(newX, self.parent.y())
            self.parent.setRect(0,0,r.width() + diff,r.height())
            self.parent.sizeChange()


class OcrAreaRight(OcrAreaSide):

    def __init__(self, width, height, parent, scene):
        OcrAreaSide.__init__(self, width - 15, -15, 30, height+30, parent, scene)


    def hoverMoveEvent(self, event):
        items = self.scene().items(event.scenePos())
        ## TODO: cambiare controllando lo zvalue o simili per vedere che non si tratti di un altra area
        if not len(items):
            return
        for item in items:
            if type(item) is OcrAreaTop:
                self.setCursor(QtCore.Qt.SizeBDiagCursor)
                return
        self.setCursor(QtCore.Qt.SizeHorCursor)
        

    def resizeParentItem(self, newPoint):
        diff = - newPoint.x() + self.oldPoint.x()
        r = self.parent.rect()

        self.parent.setRect(0,0,r.width() - diff,r.height())
        self.parent.sizeChange()


class OcrAreaBottom(OcrAreaSide):

    def __init__(self, width, height, parent, scene):
        OcrAreaSide.__init__(self, - 15, height - 15, width + 30, 30, parent, scene)


    def hoverMoveEvent(self, event):
        items = self.scene().items(event.scenePos())
        ## TODO: cambiare controllando lo zvalue o simili per vedere che non si tratti di un altra area
        if not len(items):
            return
        for item in items:
            if type(item) is OcrAreaLeft:
                self.setCursor(QtCore.Qt.SizeBDiagCursor)
                return
            elif type(item) is OcrAreaRight:
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
                return
        self.setCursor(QtCore.Qt.SizeVerCursor)
        

    def resizeParentItem(self, newPoint):
        diff = - newPoint.y() + self.oldPoint.y()
        r = self.parent.rect()

        self.parent.setRect(0,0,r.width(),r.height() - diff)
        self.parent.sizeChange()
