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
        self.button_wires.clicked.connect(self.pick_wire)
        self.button_test.clicked.connect(self.test)

        self.vis = True

        self.node1 = Node(self.scene, QColor("#93b0ff"), "Node 1")
        self.scene.addItem(self.node1)
        self.node1.setup_terminals()
        self.node2 = Node(self.scene, QColor("#9effa1"), "Node 2")
        self.scene.addItem(self.node2)
        self.node2.setup_terminals()
        #self.wire_add = False
        self.wire_start = False
        self.curr_wire = None

    def pick_wire(self):
        """Switch scene to enable special mouse events"""
        self.scene.set_opt('wire_add')

    def add_wire(self, term):
        """Add a wire connecting picked node terminals"""
        if not self.wire_start:
            self.wire_start = term
            self.curr_wire = Wire(self.wire_start, self.scene, self)
            self.scene.addItem(self.curr_wire)
            term.parent.add_out_wire(self.curr_wire)
            self.scene.set_opt('wire_drag')

    def finish_wire(self, term):
        self.curr_wire.finish_wire(term)
        self.scene.set_opt('')
        self.wire_start = False

    def test(self):
        return


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
            items = self.items(event.scenePos())
            for item in items:
                try:
                    if item.cat == 'out':
                        self.parent.add_wire(item)
                except AttributeError:
                    pass
        elif self.opt == 'wire_drag':
            items = self.items(event.scenePos())
            for item in items:
                try:
                    if item.cat != 'out':
                        self.parent.finish_wire(item)
                except AttributeError:
                    pass

    def mouseMoveEvent(self, event):
        super(Scene, self).mouseMoveEvent(event)
        if self.opt == 'wire_drag':
            pos = event.scenePos()
            self.parent.curr_wire.set_end(pos.x(), pos.y())


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
        self.parent = parent    # Scene
        self.name = name
        self.in_wires = []
        self.inst_wires = []
        self.out_wires = []
        self.term_grps = {}
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.brush = QBrush(colour)
        self.rect = QRectF(0, 0, 100, 50)
        self.height = 50

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
        painter.drawRoundedRect(0, 0, 100, self.height, 5, 5)
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
        painter.drawRoundedRect(self.focus_rect, 5, 5)

    def setup_terminals(self):
        posn = self.pos()
        self.in_con = NodeTerminal(self, 'in', 20)
        out_con = NodeTerminal(self, 'out', 20)
        ins_con = NodeTerminal(self, 'ins', posn)
        self.term_grps['0'] = [self.in_con, out_con, '']

    def add_terminals(self):
        key = len(self.term_grps) + 1
        incr = key * 22.5
        in_con = NodeTerminal(self, 'in', incr)
        out_con = NodeTerminal(self, 'out', incr)
        self.term_grps[str(key)] = [in_con, out_con, '']
        self.height += 22.5
        self.rect.setHeight(self.rect.height() + 22.5)
        self.focus_rect.setHeight(self.rect.height() + 1)

    def set_position(self, pos):
        self.setPos(pos)

    def set_brush(self, brush):
        self.brush.setColor(brush)
        self.update()

    def add_out_wire(self, wire):
        self.out_wires.append(wire)

    def add_in_wire(self, wire):
        self.in_wires.append(wire)

    def add_inst_wire(self, wire):
        self.inst_wires.append(wire)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            x = value.x()
            y = value.y()
            """
            for wire in self.out_wires:
                wire.start_point.setX(x)
                wire.start_point.setY(y)
                wire.handle1.setX(x + 200)
                wire.handle1.setY(y + 25)
            for wire in self.in_wires:
                wire.handle2.setX(x - 100)
                wire.handle2.setY(y + 25)
            for wire in self.inst_wires:
                wire.handle2.setX(x + 50)
                wire.handle2.setY(y - 100)
            """
        return value


#################################################
class NodeTerminal(QGraphicsItem):
    def __init__(self, parent, cat, offset):
        super(NodeTerminal, self).__init__(parent)
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.parent = parent    # a Node
        self.cat = cat
        self.posn = self.parent.pos()
        self.offset = offset

        if self.cat == 'in':
            self.rect = QRectF(-5, self.offset, 10, 10)
            self.coords = (-5, self.offset)
        elif self.cat == 'out':
            self.rect = QRectF(95.0, self.offset, 10, 10)
            self.coords = (95.0, self.offset)
        elif self.cat == 'ins':
            self.rect = QRectF(45, -5, 10, 10)
            self.coords = (45, -5)

        self.path = QPainterPath()
        self.path.addEllipse(self.rect)

        self.isSelected = False
        self.setAcceptHoverEvents(True)
        self.hovered_in = False
        self.hovered_out = False

    def get_pos(self):
        posn = self.scenePos()
        x = posn.x() + self.coords[0] + 5
        y = posn.y() + self.coords[1] + 5
        pos = QPointF(x, y)
        return pos

    def boundingRect(self):
        return self.path.boundingRect()

    def hoverEnterEvent(self, event):
        try:
            if self.parent.parent.opt == 'wire_add':
                self.hovered_out = True
                self.update()
            if self.parent.parent.opt == 'wire_drag':
                self.hovered_in = True
                self.update()
        except AttributeError:
            pass

    def hoverLeaveEvent(self, event):
        self.hovered_in = False
        self.hovered_out = False
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setPen(Qt.black)
        if self.cat == 'in':
            if self.hovered_in:
                painter.setBrush(Qt.yellow)
                size = 15
                posx = self.posn.x() - 7.5
                posy = self.posn.y() + 20
            else:
                painter.setBrush(Qt.blue)
                size = 10
                posx = self.posn.x()-5
                posy = self.posn.y()+22.5
            #painter.drawEllipse(posx, posy, size, size)
        elif self.cat == 'out':
            if self.hovered_out:
                painter.setBrush(Qt.red)
                size = 15
                posx = self.posn.x() + 92.5
                posy = self.posn.y() + 20
            else:
                painter.setBrush(QColor('#888888'))
                size = 10
                posx = self.posn.x() + 95
                posy = self.posn.y() + 22.5
            #painter.drawEllipse(posx, posy, size, size)
        elif self.cat == 'ins':
            if self.hovered_in:
                painter.setBrush(Qt.yellow)
                size = 15
                posx = self.posn.x() + 42.5
                posy = self.posn.y() - 7.5
            else:
                painter.setBrush(Qt.cyan)
                size = 10
                posx = self.posn.x() + 45
                posy = self.posn.y() - 5
            #painter.drawEllipse(posx, posy, size, size)
        painter.drawPath(self.path)

    def drawFocusRect(self, painter):
        """Highlight selected"""
        focus_brush = QBrush()
        focus_pen = QPen(Qt.DotLine)
        focus_pen.setColor(Qt.red)
        focus_pen.setWidthF(1.5)
        painter.setBrush(focus_brush)
        painter.setPen(focus_pen)
        painter.drawRect(self.focus_rect)

    def mousePressEvent(self, event):
        #print(self.parent.name)
        self.isSelected = True

############################
class Wire(QGraphicsItem):
    def __init__(self, start, scene, parent):
        """Bezier curve with adjustable control handles connecting two Nodes"""
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.scene = scene
        self.new = True
        self.parent = parent  # mainWindow
        self.start = start  # The Start NodeTerminal
        self.end = QPointF(0.0, 0.0)  # Temp
        self.end_term = None

        self.start_point = start.pos()

        start_x = self.start_point.x()
        start_y = self.start_point.y()

        # Set up reasonable initial positions for Handles
        self.handle1 = Handle(self.start_point, Qt.red, self.start)
        self.handle2 = Handle(self.start_point, Qt.green, self.start)
        self.handle3 = Handle(self.start_point, Qt.blue, self)  # temp for drag

        # TODO get this to work
        hnd_pos = self.handle1.mapToParent(0, 0)
        pos = self.start.scenePos()
        y = pos.y()
        self.handle1.setX(start_x + 200)
        self.handle1.setY(hnd_pos.y() - y)
        print(hnd_pos.y(), y)

        self.end_point = self.handle3.rect.center()
        end_x = self.end_point.x()
        end_y = self.end_point.y()
        self.handle2.setX(end_x - 100)
        self.handle2.setY(end_y + 25)

    def set_end(self, endx, endy):
        """Handle3 is moved to follow the mouse pointer"""
        self.handle2.setX(endx - 100)
        self.handle2.setY(endy)
        self.handle3.setX(endx)
        self.handle3.setY(endy)
        self.end_point.setX(endx)
        self.end_point.setY(endy)

    def boundingRect(self):
        """Has to be re-implemented for the sub-classed item to work"""
        start = self.start_point
        end = self.end
        bounds = end - start
        size = QSizeF(bounds.x(), bounds.y())
        return QRectF(start, size)

    def finish_wire(self, term):
        """Term is Node terminal object"""
        self.end_term = term
        self.handle2.setParentItem(self.end_term)
        if term.cat == 'ins':
            self.handle2.setX(50)
            self.handle2.setY(- 100)
            term.parent.inst_wires.append(self)
        else:
            hnd_pos = self.handle2.mapToParent(0, 0)
            pos = self.end_term.scenePos()
            y = pos.y()
            self.handle2.setX(-100)
            self.handle2.setY(hnd_pos.y() - y)
            term.parent.in_wires.append(self)
            term.parent.add_terminals()
        self.update()
        self.parent.scene.removeItem(self.handle3)

    def paint(self, painter, option, widget=None):
        """Draw a Bezier curve connecting selected Nodes"""
        qp = painter
        qp.setRenderHint(QPainter.HighQualityAntialiasing)
        from_point = self.start.get_pos()
        posn1 = self.handle1.scenePos()
        posn2 = self.handle2.scenePos()
        path = QPainterPath(from_point)
        if self.end_term:
            self.end_point = self.end_term.get_pos()
        # Draw path
        path.cubicTo(posn1, posn2, self.end_point)
        wire_pen = QPen(QColor('#aa00ff'), 2)
        wire_pen.setCosmetic(True)
        qp.setPen(wire_pen)
        qp.drawPath(path)

        if self.parent.vis:
        #if self.isSelected():
            # Draw helper lines (https://gist.github.com/Alquimista/1274149)
            control_points = (
                (from_point.x(), from_point.y()),
                (posn1.x(), posn1.y()),
                (posn2.x(), posn2.y()),
                (self.end_point.x(), self.end_point.y()))
            old_point = control_points[0]
            helper_pen = QPen(Qt.darkGreen, 1, Qt.DashLine)
            for i, point in enumerate(control_points[1:]):
                i += 2
                qp.setPen(helper_pen)
                qp.drawLine(old_point[0], old_point[1], point[0], point[1])
                old_point = point

    def update_position(self):
        self.prepareGeometryChange()
        self.update()


##############################################
class Handle(QGraphicsItem):
    """A Handle object for manipulating Bezier control points"""
    def __init__(self, posn, colour, parent):
        super(Handle, self).__init__(parent)
        self.posn = posn
        self.colour = colour
        self.parent = parent    # The start node (handles 0, 1) or the wire (2)
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.rect = QRectF(posn.x()-10, posn.y()-10, 20, 20)
        self.focus_rect = QRectF(self.rect.x() - 1, self.rect.y() - 1,
                                 self.rect.width() + 1, self.rect.height() + 1)
        self.path = QPainterPath()
        self.path.addEllipse(self.rect)

    def boundingRect(self):
        """Has to be re-implemented for the sub-classed item to work"""
        return self.rect

    def paint(self, painter, option, widget=None):
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(self.colour)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.drawPath(self.path)
        if self.isSelected():
            self.drawFocusRect(painter)

    def get_posn(self):
        return self.posn

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
    app = QtWidgets.QApplication(['Node Children'])
    window = MainWindow()
    window.resize(640, 480)
    window.show()
    app.exec_()