#!/usr/bin/env python

""" Lector: ocrwidget.py

    Copyright (C) 2008 Davide Setti

    This program is released under the GNU GPLv2
""" 

import sys
import Image
#import ImageQt
import os
from PyQt4 import QtCore, QtGui
#import sys
#sys.path.append('/usr/lib/ooo-2.0/program')
#import uno

class QOcrWidget(QtGui.QGraphicsView):
    def __init__(self):
        QtGui.QGraphicsView.__init__(self)

        scene = QtGui.QGraphicsScene(self)
        #scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        #scene.setSceneRect(0, 0, 400, 400)
        self.setScene(scene)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)

        self.setMinimumSize(200, 200)
        self.first = True
        self.bMovingArea = False
        self.setCursor(QtCore.Qt.CrossCursor)
        self.isModified = False


    def drawBackground(self, painter, rect):
        if hasattr(self, 'ocrImage') and self.ocrImage:
            sceneRect = self.sceneRect()
            painter.drawImage(sceneRect, self.ocrImage)
            #self.statusBar.showMessage(self.tr("Disegno bag"))


    def mouseReleaseEvent(self, event):
        self.bMovingArea = False
        if self.itemAt(event.pos()):
            pass
        else:
            if event.button() == QtCore.Qt.LeftButton:
                if self.first == True:
                    self.pos1 = self.mapToScene(event.pos())
                    self.first = False
                else:
                    pos2 = self.mapToScene(event.pos())
                    self.first = True
                    diff = pos2 - self.pos1

                    size = QtCore.QSizeF(diff.x(), diff.y())
                    rect = QtCore.QRectF(self.pos1, size)

                    item = OcrArea(rect, self, self.areaBorder, self.areaResizeBorder)
                    self.scene().addItem(item)

                    self.isModified = True

        QtGui.QGraphicsView.mouseReleaseEvent(self,event)


    def cambiaImmagine(self):
        #delete old OcrArea
        for item in self.scene().items():
            self.scene().removeItem(item)
        
        #open image
        self.im = Image.open(self.filename)

        #set scene size and view scale
        self.setSceneSize()

        vw = float(self.width())
        vh = float(self.height())
        iw = float(self.im.size[0])
        ih = float(self.im.size[1])
        ratio = min (vw/iw, vh/ih)

        self.setMatrix(QtGui.QMatrix(.95*ratio, 0., 0., .95*ratio, 0., 0.))
        self.areaResizeBorder = 5 / ratio

        self.areaBorder = 2 / ratio

        #show image
        self.generateQtImage()
        self.resetCachedContent()
        self.isModified = False


    def rotateRight(self):
        self.im = self.im.rotate(-90)

        self.setSceneSize()
        self.generateQtImage()
        self.resetCachedContent()
        
        
    def rotateLeft(self):
        self.im = self.im.rotate(90)

        self.setSceneSize()
        self.generateQtImage()
        self.resetCachedContent()
        

    def rotateFull(self):
        self.im = self.im.rotate(180)

        self.setSceneSize()
        self.generateQtImage()
        self.resetCachedContent()


    def generateQtImage(self):
        s = self.im.convert("RGB").tostring("jpeg","RGB")

        self.ocrImage = QtGui.QImage()
        self.ocrImage.loadFromData(QtCore.QByteArray(s))

        #print "%d %d %d" % (self.ocrImage.width(), self.ocrImage.height(), self.ocrImage.depth())
        #self.ocrImage = ImageQt.ImageQt(self.im.convert("RGB"))
        #print "%d %d %d" % (self.ocrImage.width(), self.ocrImage.height(), self.ocrImage.depth())


    def setSceneSize(self):
        iw = float(self.im.size[0])
        ih = float(self.im.size[1])
        self.scene().setSceneRect(0, 0, int(iw), int(ih))


    def zoomIn(self):
        self.scale(1.25, 1.25)

        for item in self.scene().items():
            # resize area on which area is resizable
            item.resizeBorder *= 0.8
            
            # resize border
            pen = item.pen()
            pen.setWidthF(pen.widthF()*0.8)
            item.setPen(pen)
        
        self.resetCachedContent()
        self.repaint()


    def zoomOut(self):
        self.scale(0.8, 0.8)

        for item in self.scene().items():
            # resize area on which area is resizable
            item.resizeBorder *= 1.25
            
            # resize border
            pen = item.pen()
            pen.setWidthF(pen.widthF()*1.25)
            item.setPen(pen)
        
        self.resetCachedContent()
        self.repaint()


    def doOcr(self):
        import codecs
        aItems = self.scene().items()
        numItems = len(aItems)

        self.textBrowser.clear()

        #TODO: annulla non utilizzato
        progress = QtGui.QProgressDialog("Sto leggendo le immagini...", "Annulla", 0, numItems)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)

        i = 0
        for item in aItems:
            progress.setValue(i)
            rect = item.rect()
            pos = item.scenePos()
            box = (int(rect.left()+pos.x()),int(rect.top()+pos.y()),int(rect.right()+pos.x()),int(rect.bottom()+pos.y()))
            print box

            print item.scenePos().x()
            print item.scenePos().y()

            region = self.im.crop(box)
            region.save("/tmp/prova.tif")
            
            command = "tesseract /tmp/prova.tif /tmp/out.%d -l %s" % (i, self.language)
            os.popen(command)
            
            s = codecs.open("/tmp/out.%d.txt"% (i, ) ,'r','utf-8').read()
            self.textBrowser.append(s)

            i = i + 1
        
        progress.setValue(numItems)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            item = self.scene().focusItem()
            if item:
                self.scene().removeItem(item)

        QtGui.QGraphicsView.keyReleaseEvent(self, event)

       

class OcrArea(QtGui.QGraphicsRectItem):
    def __init__(self, rect, parent = None, areaBorder = 2, resizeBorder = 5):
        QtGui.QGraphicsRectItem.__init__(self, rect)

        #self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        pen = QtGui.QPen(QtCore.Qt.green, areaBorder, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.setPen(pen)
        self.setAcceptsHoverEvents(True)
        self.setCursor(QtCore.Qt.SizeAllCursor)
        self.resizeBorder = resizeBorder
    

    def mousePressEvent(self, event):
        self.update()

        r = self.rect()
        if event.pos().x() > (r.right() - self.resizeBorder) :
            self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, False)
            self.sVal = "event.pos().x()"
            self.sEdge = "Right"

        elif event.pos().x() < (r.left() + self.resizeBorder) :
            self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, False)
            self.sVal = "event.pos().x()"
            self.sEdge = "Left"

        elif event.pos().y() < (r.top() + self.resizeBorder) :
            self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, False)
            self.sVal = "event.pos().y()"
            self.sEdge = "Top"

        elif event.pos().y() > (r.bottom() - self.resizeBorder) :
            self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, False)
            self.sVal = "event.pos().y()"
            self.sEdge = "Bottom"

        QtGui.QGraphicsItem.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.update()
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.sEdge = ''
        QtGui.QGraphicsItem.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        self.update()

        if hasattr(self, 'sEdge') and self.sEdge:
            r = self.rect()
            s = "r.set%s(%s)" % (self.sEdge, self.sVal)
            exec(s)
            self.setRect(r)

        QtGui.QGraphicsItem.mouseMoveEvent(self, event)


    def hoverMoveEvent(self, event):
        r = self.rect()
        if event.pos().x() > (r.right() - self.resizeBorder) :
            self.setCursor(QtCore.Qt.SizeHorCursor)

        elif event.pos().x() < (r.left() + self.resizeBorder) :
            self.setCursor(QtCore.Qt.SizeHorCursor)

        elif event.pos().y() < (r.top() + self.resizeBorder) :
            self.setCursor(QtCore.Qt.SizeVerCursor)

        elif event.pos().y() > (r.bottom() - self.resizeBorder) :
            self.setCursor(QtCore.Qt.SizeVerCursor)

        else:
            self.setCursor(QtCore.Qt.SizeAllCursor)

