import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QOpenGLWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QSlider, QLabel, QGroupBox,
                             QPushButton, QTextEdit)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImage
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np


class WireframeViewer(QOpenGLWidget):
    def __init__(self, parent=None):
        super(WireframeViewer, self).__init__(parent)

        self.xRot = 0
        self.yRot = 0
        self.zRot = 0

        self.xPos = 0
        self.yPos = 0
        self.zPos = 0

        self.cameraZ = -10

        self.scale = 1.0

        self.cameraRotX = 30
        self.cameraRotY = -45

        self.matrix_display = None  # Reference to the matrix display widget

        self.vertices = np.array([
            [0, 0, 0], [0, 3, 0], [0, 8, 0], [-2, 8, 0], [-2, 5, 0], [-4, 5, 0],
            [-4, 8, 0], [-6, 8, 0], [-6, 4, 0], [-5, 3, 0], [-2, 3, 0], [-2, 0, 0]
        ], dtype=np.float32)
        new_vertices = np.copy(self.vertices)
        new_vertices[:, 2] = 1
        self.vertices = np.vstack((self.vertices, new_vertices))
        self.vertices /= 3
        self.edges = np.array([[i, (i + 1) % 12] for i in range(12)], dtype=np.int32)
        edges_1 = np.array([[i + 12, (i + 1) % 12 + 12] for i in range(12)], dtype=np.int32)
        edges_2 = np.array([[i, i + 12] for i in range(12)], dtype=np.int32)
        self.edges = np.vstack((self.edges, edges_1, edges_2))

    def set_matrix_display(self, display):
        self.matrix_display = display

    def minimumSizeHint(self):
        return QSize(400, 500)

    def initializeGL(self):
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height
        gluPerspective(45, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def draw_axes(self):
        glLoadIdentity()

        glTranslatef(0, 0, self.cameraZ)
        glRotatef(self.cameraRotX, 1.0, 0.0, 0.0)
        glRotatef(self.cameraRotY, 0.0, 1.0, 0.0)

        glLineWidth(2.0)
        glBegin(GL_LINES)

        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(3, 0, 0)

        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 3, 0)

        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 3)

        glEnd()

    def get_rotation_matrix(self):
        rx = np.radians(self.xRot)
        ry = np.radians(self.yRot)
        rz = np.radians(self.zRot)
        rot_x = np.array([
            [1, 0, 0, 0],
            [0, np.cos(rx), np.sin(rx), 0],
            [0, -np.sin(rx), np.cos(rx), 0],
            [0, 0, 0, 1]
        ])
        rot_y = np.array([
            [np.cos(ry), 0, -np.sin(ry), 0],
            [0, 1, 0, 0],
            [np.sin(ry), 0, np.cos(ry), 0],
            [0, 0, 0, 1]
        ])
        rot_z = np.array([
            [np.cos(rz), np.sin(rz), 0, 0],
            [-np.sin(rz), np.cos(rz), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        return rot_z @ rot_y @ rot_x

    def get_scale_matrix(self):
        return np.array([
            [self.scale, 0, 0, 0],
            [0, self.scale, 0, 0],
            [0, 0, self.scale, 0],
            [0, 0, 0, 1]
        ])

    def transform_vertex(self, vertex):
        matrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        vertex1 = [0, 0, 0, 1]
        vertex1[0:3] = vertex
        matrix = matrix @ self.get_scale_matrix()
        matrix = matrix @ self.get_rotation_matrix()
        matrix[3, 0:3] = np.array([self.xPos, self.yPos, self.zPos])

        if self.matrix_display is not None and not np.array_equal(matrix, np.eye(4)):
            matrix_text = "Матрица преобразования:\n\n"
            for row in matrix:
                matrix_text += "\t".join([f"{elem: .3f}" for elem in row]) + "\n"

            self.matrix_display.setText(matrix_text)

        vertex1 = vertex1 @ matrix
        return vertex1[0:3]

    def draw_figure(self):
        glLoadIdentity()

        glTranslatef(0, 0, self.cameraZ)
        glRotatef(self.cameraRotX, 1.0, 0.0, 0.0)
        glRotatef(self.cameraRotY, 0.0, 1.0, 0.0)

        glLineWidth(1.0)
        glBegin(GL_LINES)
        glColor3f(1.0, 1.0, 1.0)

        for edge in self.edges:
            for vertex_idx in edge:
                vertex = self.vertices[vertex_idx]
                transformed_vertex = self.transform_vertex(vertex)
                glVertex3fv(transformed_vertex)

        glEnd()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_axes()
        self.draw_figure()

    def set_rotation(self, axis, value):
        if axis == 'x':
            self.xRot = value
        elif axis == 'y':
            self.yRot = value
        elif axis == 'z':
            self.zRot = value
        self.update()

    def set_position(self, axis, value):
        if axis == 'x':
            self.xPos = value / 50
        elif axis == 'y':
            self.yPos = value / 50
        elif axis == 'z':
            self.zPos = value / 50
        self.update()

    def set_scale(self, value):
        self.scale = (value + 49) / 50
        self.update()

    def wheelEvent(self, event):
        self.cameraZ += event.angleDelta().y() / 120
        self.update()

    def save_projection(self, filename, rot_x, rot_y):
        current_rot_x = self.cameraRotX
        current_rot_y = self.cameraRotY

        self.cameraRotX = rot_x
        self.cameraRotY = rot_y

        self.update()
        self.makeCurrent()

        image = self.grabFramebuffer()
        image.save(filename)

        self.cameraRotX = current_rot_x
        self.cameraRotY = current_rot_y
        self.update()

    def save_projections(self):
        self.save_projection("projection_front.png", 0, 0)
        self.save_projection("projection_side.png", 0, 90)
        self.save_projection("projection_top.png", 90, 0)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel with viewer and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.viewer = WireframeViewer()
        left_layout.addWidget(self.viewer)

        save_button = QPushButton("Сохранить проекции")
        save_button.clicked.connect(self.viewer.save_projections)
        left_layout.addWidget(save_button)

        rotation_group = self.create_slider_group("Вращение",
                                                  [('X', 'red', 0, 360),
                                                   ('Y', 'green', 0, 360),
                                                   ('Z', 'blue', 0, 360)],
                                                  self.viewer.set_rotation)

        position_group = self.create_slider_group("Перемещение",
                                                  [('X', 'red', -100, 100),
                                                   ('Y', 'green', -100, 100),
                                                   ('Z', 'blue', -100, 100)],
                                                  self.viewer.set_position)

        scale_group = self.create_slider_group("Масштаб",
                                               [('Scale', 'black', 1, 200)],
                                               lambda _, v: self.viewer.set_scale(v))

        left_layout.addWidget(rotation_group)
        left_layout.addWidget(position_group)
        left_layout.addWidget(scale_group)

        main_layout.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        matrix_display = QTextEdit()
        matrix_display.setReadOnly(True)
        matrix_display.setMinimumWidth(300)
        matrix_display.setStyleSheet(
            "QTextEdit { background-color:rgb(0, 0, 0); color: blue; font-family: monospace; font-size: 30px;}")
        right_layout.addWidget(matrix_display)

        main_layout.addWidget(right_panel)

        self.viewer.set_matrix_display(matrix_display)

        self.setWindowTitle("3D Wireframe Viewer")
        self.resize(1600, 1000)

    def create_slider_group(self, title, sliders_info, slot):
        group = QGroupBox(title)
        layout = QVBoxLayout()

        def create_slot(axis):
            return lambda value: slot(axis, value)

        for axis, color, min_val, max_val in sliders_info:
            slider_layout = QHBoxLayout()

            label = QLabel(f"{axis}:")
            label.setStyleSheet(f"color: {color}")
            label.setMinimumWidth(30)
            slider_layout.addWidget(label)

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(min_val)
            slider.setMaximum(max_val)
            slider.setValue(0)
            slider.valueChanged.connect(create_slot(axis.lower()))

            value_label = QLabel(f"{min_val}")
            value_label.setMinimumWidth(40)
            slider.valueChanged.connect(lambda v, label=value_label: label.setText(f"{v}"))

            slider_layout.addWidget(slider)
            slider_layout.addWidget(value_label)
            layout.addLayout(slider_layout)

        group.setLayout(layout)
        return group


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
