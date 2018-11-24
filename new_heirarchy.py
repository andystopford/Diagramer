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

        self.scene = Scene(self)
        self.scene.view = View(self)
        self.scene.view.setScene(self.scene)
        self.scene.view.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
        self.scene.view.setRubberBandSelectionMode(Qt.ContainsItemShape)

        #self.button_nodes = QtWidgets.QPushButton('Add Node')
        self.button_wires = QtWidgets.QPushButton('Add Wire')
        self.button_vis = QtWidgets.QPushButton('Toggle Visibility')
        self.button_test = QtWidgets.QPushButton('Test')
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.addWidget(self.scene.view)
        button_layout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(button_layout)
        #button_layout.addWidget(self.button_nodes)
        button_layout.addWidget(self.button_wires)
        button_layout.addWidget(self.button_vis)
        button_layout.addWidget(self.button_test)
        self.setLayout(mainLayout)
        self.scene.view.show()

        self.click_positions = []
        # self.button_nodes.clicked.connect(self.add_node)
        self.button_wires.clicked.connect(self.pick_wire)
        self.button_vis.clicked.connect(self.toggle_vis)

        self.vis = True

        self.node1 = Node(self, QColor("#93b0ff"), "Node 1")
        self.scene.addItem(self.node1)
        self.node2 = Node(self, QColor("#9effa1"), "Node 2")
        self.scene.addItem(self.node2)
        #self.wire_add = False
        self.wire_start = None

    def pick_wire(self):
        """Switch scene to enable special mouse events"""
        self.scene.set_opt('wire_add')

    def add_wire(self, conn):
        """Add a wire connecting picked node terminals"""
        if not self.wire_start:
            self.wire_start = conn[0]
        else:
            end = conn[0]
            bc = Wire(self.wire_start, end, self.scene, self)
            self.scene.addItem(bc)
            self.wire_start = None
            self.scene.set_opt('')

    def toggle_vis(self):
        """TODO much refinement needed here"""
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


##############################################
class Scene(QGraphicsScene):
    def __init__(self, parent=None):
        QGraphicsScene.__init__(self, parent)
        self.parent = parent    # MainWindow
        self.opt = ''

    def set_opt(self, opt):
        """Set event handler options"""
        self.opt = opt

    def mousePressEvent(self, event):
        #   call base class to retain existing event handling:
        super(Scene, self).mousePressEvent(event)
        if self.opt == 'wire_add':
            item = self.items(event.scenePos())
            if item is not None:
                self.parent.add_wire(item)

    def mouseMoveEvent(self, event):
        super(Scene, self).mouseMoveEvent(event)
        if self.opt == 'wire_add':
            pos = event.scenePos()
            # print(pos.x(), pos.y())


###############################################
class View(QGraphicsView):
    def __init__(self, parent):
        super().__init__()
        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.setMouseTracking(True)
        self.parent = parent


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
        painter.drawText(5, 15, self.name)
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
            self.rect = QRectF(self.posn.x() + 45,self.posn.y() + -5, 10, 10)
        self.setZValue(1)
        self.isSelected = False
        self.setAcceptHoverEvents(True)
        self.hovered = False

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

    def hoverEnterEvent(self, event):
        # TODO should only occur when pick enabled
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setPen(Qt.black)
        if self.type == 'in':
            if self.hovered:
                painter.setBrush(Qt.red)
                size = 15
                posx = self.posn.x() - 7.5
                posy = self.posn.y() + 20
            else:
                painter.setBrush(Qt.blue)
                size = 10
                posx = self.posn.x()-5
                posy = self.posn.y()+22.5
            painter.drawEllipse(posx, posy, size, size)
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
        start = self.start.rect.center()
        end = self.end.rect.center()
        start_y = start.y()
        end_y = end.y()
        diff_x = start.x() - end.x()

        # Halve the x difference and add 100 (offset from the node centre)
        x_comp = abs(diff_x) * 0.5 + 100
        if self.end.type == 'ins':
            end_y = end_y - start.x()
            end_x = end.x()
        else:
            end_x = x_comp
            if diff_x > 0:
                end_x = end.x() - x_comp + 100

        self.handle1.setX(x_comp)
        self.handle1.setY(start_y)
        self.handle2.setX(end_x)
        self.handle2.setY(end_y)
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
        start_point = self.start.rect.center()
        end_point = self.end.rect.center()
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
        wire_pen = QPen(QColor('#aa00ff'), 2)
        wire_pen.setCosmetic(True)
        qp.setPen(wire_pen)
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
    app = QtWidgets.QApplication(['New Heirarchy'])
    window = MainWindow()
    window.resize(640, 480)
    window.show()
    app.exec_()