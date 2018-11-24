import sys
import math
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPolygonF, \
    QPainterPath, QPainterPathStroker
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, \
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsItem, \
    QGraphicsLineItem, QGraphicsRectItem, QGraphicsObject, \
    QGraphicsProxyWidget, QRubberBand
from PyQt5.QtOpenGL import *

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        #self.view = QGraphicsView()
        self.view = View(self)
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
        self.view.setRubberBandSelectionMode(Qt.ContainsItemShape)

        #self.button_nodes = QtWidgets.QPushButton('Add Node')
        self.button_wires = QtWidgets.QPushButton('Add Wire')
        self.button_vis = QtWidgets.QPushButton('Toggle Visibility')
        self.button_test = QtWidgets.QPushButton('Test')
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.addWidget(self.view)
        button_layout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(button_layout)
        #button_layout.addWidget(self.button_nodes)
        button_layout.addWidget(self.button_wires)
        button_layout.addWidget(self.button_vis)
        button_layout.addWidget(self.button_test)
        self.setLayout(mainLayout)
        self.view.show()

        self.click_positions = []
        # self.button_nodes.clicked.connect(self.add_node)
        self.button_wires.clicked.connect(self.pick_wire)
        self.button_vis.clicked.connect(self.toggle_vis)

        self.vis = True

        self.node1 = Node(self, QColor("#93b0ff"), "Node 1")
        self.scene.addItem(self.node1)
        self.node2 = Node(self, QColor("#9effa1"), "Node 2")
        self.scene.addItem(self.node2)
        """
        self.test_button = QtWidgets.QPushButton('test')
        self.test_proxy = QGraphicsProxyWidget()
        self.test_proxy.setWidget(self.test_button)
        self.test_proxy.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.scene.addItem(self.test_proxy)
        """
        self.wire_add = False
        self.wire_start = None
        self.line_start = None

    def BAK_add_wire(self):
        start = self.node1
        end = self.node2
        bc = Wire(start, end, self.scene, self)
        self.scene.addItem(bc)
        start.add_wire(bc)
        end.add_wire(bc)

    def pick_wire(self):
        self.wire_add = True
        print('adding')

    def add_wire(self, conn):
        print('self_add', self.wire_add)
        if self.wire_add:
            if self.wire_start == None:
                self.wire_start = conn
                print('par')
            else:
                end = conn
                bc = Wire(self.wire_start, end, self.scene, self)
                self.scene.addItem(bc)
                #self.wire_start.add_wire(bc)
                #end.add_wire(bc)
                self.wire_add = None
                self.wire_start = None

    def toggle_vis(self):
        scene_items = self.scene.items()
        if self.vis:
            scene_items[1].setVisible(False)
            scene_items[2].setVisible(False)
            self.vis = False
        else:
            scene_items[1].setVisible(True)
            scene_items[2].setVisible(True)
            self.vis = True

    def test(self, item):
        print('item', item)
        if self.line_start == None:
            self.line_start = item.parent.pos()
        else:
            end = item.parent.pos()
            print(end)
            startx = self.line_start.x()
            starty = self.line_start.y()
            endx = end.x()
            endy = end.y()
            print(startx, starty, endx, endy)


###############################################
class View(QGraphicsView):
    itemDoubleClicked = pyqtSignal(object)
    def __init__(self, parent):
        super().__init__()
        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.setMouseTracking(True)
        self.parent = parent

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if item is not None:
            #self.itemDoubleClicked.emit(item)
            self.parent.add_wire(item)

    """
    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubberband.setGeometry(
            QRect(self.origin, QSize()))
        self.rubberband.show()
        QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.rubberband.isVisible():
            self.rubberband.setGeometry(
                QRect(self.origin, event.pos()).normalized())
        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.rubberband.isVisible():
            self.rubberband.hide()
            selected = []
            rect = self.rubberband.geometry()
            print('rect', rect)
            items = self.items()
            for item in items:
                BR = item.boundingRect()
                BR = BR.getRect()
                br = QRect(int(BR[0]), int(BR[1]), int(BR[2]), int(BR[3]))
                print(br)
                if rect.contains(br):
                    print(item)
                else:
                    print (' Nothing\n')
        QWidget.mouseReleaseEvent(self, event)
    """

#####################################
class Node(QGraphicsItem):
    def __init__(self, parent, colour, name):
        super().__init__()
        self.parent = parent    # Mainwindow
        self.name = name
        self.wires = []
        self.terminals = []
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.brush = QBrush(colour)
        self.rect = QRectF(0, 0, 100, 50)
        self.add_terminal()
        self.setZValue(0)
        # Selection border
        self.focus_rect = QRectF(self.rect.x() - 1, self.rect.y() - 1,
                                 self.rect.width() + 1, self.rect.height() + 1)

    def boundingRect(self):
        """Has to be re-implemented for the sub-classed item to work"""
        return self.rect

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(Qt.black, 2))
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setBrush(self.brush)
        painter.drawRoundedRect(0, 0, 100, 50, 5, 5)
        painter.drawText(self.rect, self.name)
        if self.isSelected():
            self.drawFocusRect(painter)

    def drawFocusRect(self, painter):
        """Highlight selected"""
        focus_brush = QBrush()
        focus_pen = QPen(Qt.DotLine)
        focus_pen.setColor(Qt.red)
        focus_pen.setWidthF(1.5)
        painter.setBrush(focus_brush)
        painter.setPen(focus_pen)
        painter.drawRect(self.focus_rect)

    def add_terminal(self):
        scene = self.parent.scene
        in_con = NodeTerminal(self, 'in')
        out_con = NodeTerminal(self, 'out')
        ins_con = NodeTerminal(self, 'ins')
        scene.addItem(in_con)
        scene.addItem(out_con)
        scene.addItem(ins_con)
        #self.terminals.append(in_con)

    def set_position(self, pos):
        self.setPos(pos)

    def set_brush(self, brush):
        self.brush.setColor(brush)
        self.update()

    def add_wire(self, wire):
        self.wires.append(wire)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for wire in self.wires:
                # Good to get handle to follow node move:
                # wire.handle1.update_position(self.pos())
                wire.update_position()
        return value


#################################################
class NodeTerminal(QGraphicsItem):
    def __init__(self, parent, type):
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.parent = parent    # a Node
        self.type = type
        self.posn = self.parent.pos()
        if self.type == 'in':
            self.rect = QRectF(self.posn.x()-5, self.posn.y() + 22.5, 10, 10)
        elif self.type == 'out':
            self.rect = QRectF(self.posn.x() + 95, self.posn.y() + 22.5, 10, 10)
        elif self.type == 'ins':
            self.rect = QRectF(self.posn.x() + 45,self.posn.y() +  -5, 10, 10)
        self.setZValue(1)
        self.isSelected = False

    def mouseDoubleClickEvent(self, event):
        self.parent.parent.view.itemDoubleClicked.emit(self)

    def boundingRect(self):
        """Just returning self.rect gives laggy performance, probably because
        it's returning the previous to last position of the parent Node"""
        self.posn = self.parent.pos()
        if self.type == 'in':
            self.rect = QRectF(self.posn.x()-5, self.posn.y() + 22.5, 10, 10)
        elif self.type == 'out':
            self.rect = QRectF(self.posn.x() + 95, self.posn.y() + 22.5, 10, 10)
        elif self.type == 'ins':
            self.rect = QRectF(self.posn.x() + 45,self.posn.y() + -5, 10, 10)
        return self.rect

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setPen(Qt.black)
        if self.type == 'in':
            if self.isSelected:
                painter.setBrush(Qt.blue)
            else:
                painter.setBrush(Qt.red)
            painter.drawEllipse(self.posn.x()-5, self.posn.y() + 22.5, 10, 10)
        elif self.type == 'out':
            painter.setBrush(QColor('#888888'))
            painter.drawEllipse(self.posn.x() + 95, self.posn.y() + 22.5, 10, 10)
        elif self.type == 'ins':
            painter.setBrush(Qt.cyan)
            painter.drawEllipse(self.posn.x() + 45,self.posn.y() + -5, 10, 10)

    def drawFocusRect(self, painter):
        """Highlight selected"""
        focus_brush = QBrush()
        focus_pen = QPen(Qt.DotLine)
        focus_pen.setColor(Qt.red)
        focus_pen.setWidthF(1.5)
        painter.setBrush(focus_brush)
        painter.setPen(focus_pen)
        painter.drawRect(self.focus_rect)

    def update_position(self):
        self.posn = self.parent.pos()
        #self.prepareGeometryChange()
        self.update()

    def mousePressEvent(self, event):
        #print(self.parent.name)
        self.isSelected = True

############################
class Wire(QGraphicsItem):
    def __init__(self, start, end, scene, parent):
        """Bezier curve with adjustable control handles connecting two Nodes"""
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.scene = scene
        self.new = True
        self.start = start  # The Start Node
        self.end = end  # The End Node
        self.parent = parent    # mainWindow
        start_point = self.start.pos()  # Position of Start Node
        end_point = self.end.pos()
        # Add Handles
        self.handle1 = Handle(start_point, self)
        self.scene.addItem(self.handle1)
        self.handle2 = Handle(end_point, self)
        self.scene.addItem(self.handle2)
        self.handles = [self.handle1, self.handle2]
        # Set up reasonable initial positions for Handles
        diff_x = start_point.x() + 100 - end_point.x()
        x_set1 = 125
        x_set2 = -25
        if diff_x < 300:
            x_set1 = abs(diff_x) * 0.5 + 100
            x_set2 = abs(diff_x) * 0.5
        self.handle1.setX(x_set1)
        self.handle1.setY(25)
        self.handle2.setX(-x_set2)
        self.handle2.setY(25)
        # Variables to store position of Nodes if moved from 0, 0:
        self.handle1_offset = ()
        self.handle2_offset = ()

    def boundingRect(self):
        """Has to be re-implemented for the sub-classed item to work"""
        start = self.start.pos() + self.start.rect.center()
        end = self.end.pos() + self.end.rect.center()
        bounds = end - start
        size = QSizeF(bounds.x(), bounds.y())
        return QRectF(start, size)

    def paint(self, painter, option, widget=None):
        """Draw a Bezier curve connecting selected Nodes"""
        qp = painter
        qp.setRenderHint(QPainter.HighQualityAntialiasing)
        start_point = self.start.pos() + self.start.rect.center()
        end_point = self.end.pos() + self.end.rect.center()
        posn1 = self.handle1.pos()
        posn2 = self.handle2.pos()
        # Get offset from Node positions
        node1_pos = self.handle1.mapFromItem(self.handle1, self.start.pos())
        node2_pos = self.handle2.mapFromItem(self.handle2, self.end.pos())
        if self.new:
            posn1 += node1_pos
            posn2 += node2_pos
            # Store offsets for subsequent events
            self.handle1_offset = self.handle1.get_posn()
            self.handle2_offset = self.handle2.get_posn()
            self.new = False
        else:
            posn1 += self.handle1_offset
            posn2 += self.handle2_offset
        path = QPainterPath(start_point)
        path.cubicTo(posn1, posn2, end_point)
        qp.setPen(QColor('#aa00ff'))    #Gradient?
        qp.drawPath(path)
        if self.parent.vis:
        #if self.isSelected():
            # Draw helper lines (https://gist.github.com/Alquimista/1274149)
            control_points = (
                (start_point.x(), start_point.y()),
                (posn1.x(), posn1.y()),
                (posn2.x(), posn2.y()),
                (end_point.x(), end_point.y()))
            old_point = control_points[0]
            red_pen = QPen(Qt.red, 1, Qt.DashLine)
            helper_pen = QPen(Qt.darkGreen, 1, Qt.DashLine)
            red_brush = QBrush(Qt.red)
            qp.setPen(red_pen)
            qp.setBrush(red_brush)
            qp.drawEllipse(old_point[0] - 3, old_point[1] - 3, 6, 6)
            #qp.drawText(old_point[0] + 5, old_point[1] - 3, '1')
            for i, point in enumerate(control_points[1:]):
                i += 2
                qp.setPen(helper_pen)
                qp.drawLine(old_point[0], old_point[1], point[0], point[1])
                qp.setPen(red_pen)
                qp.drawEllipse(point[0] - 3, point[1] - 3, 6, 6)
                #qp.setPen(greenPen)
                #qp.drawText(point[0] + 5, point[1] - 3, '%d' % i)
                old_point = point


    def update_position(self):
        self.prepareGeometryChange()
        self.update()


##############################################
class Handle(QGraphicsItem):
    """A Handle object for manipulating Bezier control points"""
    def __init__(self, posn, parent):
        super().__init__()
        self.posn = posn
        self.parent = parent    # The handle's Wire
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.rect = QRectF(posn.x()-10, posn.y()-10, 20, 20)
        self.focus_rect = QRectF(self.rect.x() - 1, self.rect.y() - 1,
                                 self.rect.width() + 1, self.rect.height() + 1)

    def boundingRect(self):
        """Has to be re-implemented for the sub-classed item to work"""
        return self.rect

    def paint(self, painter, option, widget=None):
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor("#ed25ff"))
        painter.setPen(pen)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.drawEllipse(self.posn.x() - 10, self.posn.y() - 10, 20, 20)
        if self.isSelected():
            self.drawFocusRect(painter)


    def get_posn(self):
        return self.posn

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.parent.update_position()
        return value

    def update_position(self, pos):
        print('ok')
        self.posn = pos
        self.prepareGeometryChange()
        self.update()

    def drawFocusRect(self, painter):
        """Highlight selected"""
        focus_brush = QBrush()
        focus_pen = QPen(Qt.DotLine)
        focus_pen.setColor(Qt.red)
        focus_pen.setWidthF(1.5)
        painter.setBrush(focus_brush)
        painter.setPen(focus_pen)
        painter.drawRect(self.focus_rect)


##############################################

if __name__ == '__main__':
    app = QtWidgets.QApplication(['Bezier Arrows'])
    window = MainWindow()
    window.resize(640, 480)
    window.show()
    app.exec_()