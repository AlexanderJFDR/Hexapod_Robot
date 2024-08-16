import os

import numpy as np
import math
import matplotlib.pyplot as plt
import copy

from PIL import Image
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.animation import FuncAnimation

from mathematics import *
from constant import *
from picture import *

# 定义点类
class Point:
    #初始化函数
    def __init__(self, coordinates=(0,0,0), name='None') -> None:
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.z = coordinates[2]
        self.name = name
    #获取点的坐标
    def get_coordinates(self):
        return self.x, self.y, self.z
    #设置点的坐标
    def set_coordinates(self, coordinates):
        if hasattr(coordinates, '__len__'):
            if len(coordinates) == 3:
                self.x = coordinates[0]
                self.y = coordinates[1]
                self.z = coordinates[2]
            else:
                raise ValueError
        else:
            raise ValueError

#定义身体
class Body:
    #       |-f-|
    #      P2---*---P1--------
    #      /    |    \     |
    #     /     |     \    s
    #    /      |      \   |
    #   P3-------------P0 ---
    #    \      |      /|
    #     \     |     / |
    #      \    |    /  |
    #       P4--*--P5   |
    #           |       |
    #           |---m---|
    #   y axis
    #    ^
    #    |
    #    |
    #    ----> x axis
    #初始化(定义尺寸和姿态)
    def __init__(self, size=BODY_SIZE, attitude=BODY_ATTITUDE) -> None:
        self.f, self.s, self.m = size
        self.attitude = attitude
        self.axis_x,self.axis_y,self.axis_z,self.axis_alpha,self.axis_beta,self.axis_gama = attitude
        self.attitude_matrix = translation_rotate_matrix(attitude)
        self.nodes_local_corrdinates = ((self.m, 0, 0),(self.f, self.s, 0),(-self.f, self.s, 0),(-self.m, 0, 0),
                                        (-self.f, -self.s, 0),(self.f, -self.s, 0),(0,0,0),(0,self.s,0))
        #节点坐标相对于全局坐标系
        self.vertices = [
            Point(coordinate_trans_matrix((self.m,0,0),self.attitude_matrix), 'P0'),
            Point(coordinate_trans_matrix((self.f,self.s,0),self.attitude_matrix), 'P1'),
            Point(coordinate_trans_matrix((-self.f,self.s,0),self.attitude_matrix), 'P2'),
            Point(coordinate_trans_matrix((-self.m,0,0),self.attitude_matrix), 'P3'),
            Point(coordinate_trans_matrix((-self.f,-self.s,0),self.attitude_matrix), 'P4'),
            Point(coordinate_trans_matrix((self.f,-self.s,0),self.attitude_matrix), 'P5')
        ]
        self.centroid = Point(coordinate_trans_matrix((0,0,0),self.attitude_matrix), 'Centroid')
        self.head = Point(coordinate_trans_matrix((0,self.s,0),self.attitude_matrix), 'Head')

    #更改尺寸
    def change_size(self,size):
        self.f, self.s, self.m = size
        self.vertices = [
            Point(coordinate_trans_matrix((self.m, 0, 0), self.attitude_matrix), 'P0'),
            Point(coordinate_trans_matrix((self.f, self.s, 0), self.attitude_matrix), 'P1'),
            Point(coordinate_trans_matrix((-self.f, self.s, 0), self.attitude_matrix), 'P2'),
            Point(coordinate_trans_matrix((-self.m, 0, 0), self.attitude_matrix), 'P3'),
            Point(coordinate_trans_matrix((-self.f, -self.s, 0), self.attitude_matrix), 'P4'),
            Point(coordinate_trans_matrix((self.f, -self.s, 0), self.attitude_matrix), 'P5')
        ]
        self.centroid = Point(coordinate_trans_matrix((0, 0, 0), self.attitude_matrix), 'Centroid')
        self.head = Point(coordinate_trans_matrix((0, self.s, 0), self.attitude_matrix), 'Head')
    #平移操作
    def translate(self, offset):
        if hasattr(offset, "__len__"):
            if len(offset) == 3:
                transformAttitude = (offset[0],offset[1],offset[2],0,0,0)
                matrix = translation_rotate_matrix(transformAttitude)
                self.attitude_matrix = np.dot(matrix,self.attitude_matrix)
                for i, p in self.vertices + [self.centroid, self.head]:
                    p.set_coordinates(coordinate_trans_matrix(self.nodes_local_corrdinates[i], self.attitude_matrix))
                self.axis_x += offset[0]
                self.axis_y += offset[1]
                self.axis_z += offset[2]
            else:
                raise ValueError
        else:
            raise ValueError
    #旋转操作
    def rotate(self, rot):
        if hasattr(rot, "__len__"):
            if len(rot) == 3:
                transformAttitude = (0,0,0,rot[0],rot[1],rot[2])
                matrix = translation_rotate_matrix(transformAttitude)
                self.attitude_matrix = np.dot(matrix, self.attitude_matrix)
                for i,p in self.vertices + [self.centroid, self.head]:
                    p.set_coordinates(coordinate_trans_matrix(self.nodes_local_corrdinates[i], self.attitude_matrix))
                self.axis_alpha += rot[0]
                self.axis_beta += rot[1]
                self.axis_gama += rot[2]
            else:
                raise ValueError
        else:
            raise ValueError
    #平移+旋转操作
    def transform(self, transform):
        if hasattr(transform, "__len__"):
            if len(transform) == 6:
                matrix = translation_rotate_matrix(transform)
                self.attitude_matrix = np.dot(matrix, self.attitude_matrix)
                for i, p in enumerate(self.vertices + [self.centroid, self.head]):
                    p.set_coordinates(coordinate_trans_matrix(self.nodes_local_corrdinates[i], self.attitude_matrix))
                #界面操作需要，角度直接相加并不合理
                self.axis_x += transform[0]
                self.axis_y += transform[1]
                self.axis_z += transform[2]
                self.axis_alpha += transform[3]
                self.axis_beta += transform[4]
                self.axis_gama += transform[5]
            else:
                raise ValueError
        else:
            raise ValueError
    #更新姿态
    def update_attitude(self,attitude):
        self.attitude = attitude
        self.attitude_matrix = translation_rotate_matrix(attitude)
        self.vertices = [
            Point(coordinate_trans_matrix((self.m, 0, 0), self.attitude_matrix), 'P0'),
            Point(coordinate_trans_matrix((self.f, self.s, 0), self.attitude_matrix), 'P1'),
            Point(coordinate_trans_matrix((-self.f, self.s, 0), self.attitude_matrix), 'P2'),
            Point(coordinate_trans_matrix((-self.m, 0, 0), self.attitude_matrix), 'P3'),
            Point(coordinate_trans_matrix((-self.f, -self.s, 0), self.attitude_matrix), 'P4'),
            Point(coordinate_trans_matrix((self.f, -self.s, 0), self.attitude_matrix), 'P5')
        ]
        self.centroid = Point(coordinate_trans_matrix((0, 0, 0), self.attitude_matrix), 'Centroid')
        self.head = Point(coordinate_trans_matrix((0, self.s, 0), self.attitude_matrix), 'Head')
    #绘制二维示意图
    def visualize2d(self, fig=None, ax=None):
        if fig is None:
            fig, ax = plt.subplots()
        # add head
        ax.scatter(self.head.x, self.head.y, facecolors='red', edgecolors='tomato', alpha=0.7, s=self.f * 10)
        ax.text(self.head.x, self.head.y, 'Head')
        # add center of gravity
        ax.scatter(self.centroid.x, self.centroid.y, facecolors='k', edgecolors='gray', alpha=0.7, s=self.f * 10)
        ax.text(self.centroid.x, self.centroid.y, 'Centroid')
        # add body hexagon
        v = [(v.x, v.y) for v in self.vertices]
        body = Polygon(v, facecolor='skyblue', alpha=0.6, fill=True, edgecolor='darkblue', linewidth=2)
        ax.add_patch(body)
        # add point label
        for v in self.vertices:
            ax.scatter(v.x, v.y, facecolors='darkblue', edgecolors='black', alpha=0.7, s=self.f * 10)
            ax.text(v.x, v.y, v.name)
        # adjuestment
        ax.set_xlim([self.centroid.x - 1.5 * self.m, self.centroid.x + 1.5 * self.m])
        ax.set_ylim([self.centroid.y - 1.5 * self.s, self.centroid.y + 1.5 * self.s])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.grid()
        ax.set_aspect('equal')
        return fig, ax
    #绘制三维示意图
    def visualize3d(self, fig=None, ax=None, is_axis=False, is_text=False):
        if fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(projection="3d", proj_type="ortho")
        # add head
        ax.scatter(self.head.x, self.head.y, self.head.z, facecolors='red', edgecolors='tomato', alpha=0.7,
                   s=self.f * 20)
        if is_text:
            ax.text(self.head.x, self.head.y, self.head.z, 'Head')
        # add center of gravity
        ax.scatter(self.centroid.x, self.centroid.y, self.centroid.z, facecolors='k', edgecolors='gray', alpha=0.7, s=self.f * 10)
        if is_text:
            ax.text(self.centroid.x, self.centroid.y, self.centroid.z, 'Centroid')
        # add body hexagon
        v = list([[v.x, v.y, v.z] for v in self.vertices])
        ax.add_collection3d(Poly3DCollection([v], facecolor='skyblue', alpha=0.6, edgecolor='darkblue', linewidth=5))
        # add point label
        for v in self.vertices:
            ax.scatter(v.x, v.y, v.z, facecolors='darkblue', edgecolors='black', alpha=0.7, s=self.f * 10)
            if is_text:
                ax.text(v.x, v.y, v.z, v.name)
        # add axis
        transformMatrix = translation_rotate_matrix(self.attitude)
        if is_axis:
            draw_axis(transformMatrix, scale=5, fontsize=12,fig=fig, ax=ax)
        # adjuestment
        ax.set_xlim([self.centroid.x - 3 * self.m, self.centroid.x + 3 * self.m])
        ax.set_ylim([self.centroid.y - 3 * self.s, self.centroid.y + 3 * self.s])
        ax.set_zlim([-5, 5])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_aspect('equal')
        return fig, ax
#定义腿
class Leg:
    #   |--lengths[0]-|--lengths[1]--|
    #   |=============|==============| p2 -------
    #   p0            p1             |          |
    # (origin)                       |          |
    #                                |  lengths[2]
    #                                |          |
    #                                |          |
    #                                | p3 -------
    #  z axis
    #  |
    #  |
    #  |------- x axis
    # origin
    #初始化
    def __init__(self, lengths=LEG_LENGTH, angles=LEG_ANGLE, angle_bias=ANGLE_BIAS, name='none',
                 datumaxis=(0,0,0,0,0,0), angle_limits=ANGLE_LIMITS) -> None:
        self.lengths = lengths
        self.angles = angles
        self.angle_bias = angle_bias #角度校准
        self.name = name
        self.axis_x, self.axis_y, self.axis_z, self.axis_alpha, self.axis_beta, self.axis_gama = datumaxis
        self.angle_limits = angle_limits
        self.constraint_angles()
        self.get_nodes_coordinate()
    #获取节点坐标（节点坐标相对于body坐标系）
    def get_nodes_coordinate(self):
        P0 = Point((self.axis_x, self.axis_y, self.axis_z), name='P0-BodyContact')

        coordinate = coordinate_transformation((self.lengths[0],0,0),(0,0,0,0,0,self.angles[0]))
        P1 = Point(coordinate_transformation(coordinate,(self.axis_x,self.axis_y,self.axis_z,
                                                         self.axis_alpha,self.axis_beta,self.axis_gama)),name='P1-coxa')

        coordinate = coordinate_transformation((self.lengths[1],0,0),(self.lengths[0],0,0,0,self.angles[1],0))
        coordinate = coordinate_transformation(coordinate,(0,0,0,0,0,self.angles[0]))
        P2 = Point(coordinate_transformation(coordinate,(self.axis_x,self.axis_y,self.axis_z,
                                                         self.axis_alpha,self.axis_beta,self.axis_gama)),name='P2-femur')

        coordinate = coordinate_transformation((0,0,-self.lengths[2]),(self.lengths[1],0,0,0,self.angles[2],0))
        coordinate = coordinate_transformation(coordinate,(self.lengths[0],0,0,0,self.angles[1],0))
        coordinate = coordinate_transformation(coordinate,(0,0,0,0,0,self.angles[0]))
        P3 = Point(coordinate_transformation(coordinate,(self.axis_x,self.axis_y,self.axis_z,
                                                         self.axis_alpha,self.axis_beta,self.axis_gama)),name='P3-tibia')

        self.nodes = [P0, P1, P2, P3]
    #获得角度
    def get_angle(self):
        return self.angles
    #约束角度
    def constraint_angles(self):
        self.angles[0] = min(max(self.angles[0],self.angle_limits[0][0]),self.angle_limits[0][1])
        self.angles[1] = min(max(self.angles[1], self.angle_limits[1][0]), self.angle_limits[1][1])
        self.angles[2] = min(max(self.angles[2], self.angle_limits[2][0]), self.angle_limits[2][1])
    #更新腿部长度
    def update_lengths(self,lengths):
        self.lengths = lengths
        self.get_nodes_coordinate()
    #更新基准轴姿态
    def update_datumaxis(self, datumaxis):
        self.axis_x, self.axis_y, self.axis_z, self.axis_alpha, self.axis_beta, self.axis_gama = datumaxis
        self.get_nodes_coordinate()
    #更新角度姿态
    def update_pose(self, angle):
        self.angles = list(angle)
        self.constraint_angles()
        self.get_nodes_coordinate()
    #更新角度补偿值
    def update_angle_bias(self,angle_bias):
        self.angle_bias = angle_bias
    #更新角度约束
    def update_angle_limits(self,angle_limits):
        self.angle_limits = angle_limits
        self.constraint_angles()
        self.get_nodes_coordinate()
    #拟运动求解（P3相对于body坐标系的位置增量）
    def solve_ik(self, delta_displacement):
        delta_x,delta_y,delta_z = delta_displacement
        body_x = self.nodes[3].x + delta_x
        body_y = self.nodes[3].y + delta_y
        body_z = self.nodes[3].z + delta_z
        #P3相对于P0坐标系的位置
        P_x,P_y,P_z = coordinate_transformation((body_x,body_y,body_z),(-self.axis_x,-self.axis_y,-self.axis_z,0,0,0))
        P0_x,P0_y,P0_z = coordinate_transformation((P_x,P_y,P_z),(0,0,0,-self.axis_alpha,-self.axis_beta,-self.axis_gama))
        if P0_x == 0 and P0_y>0:
            alpha = math.pi/2
        elif P0_x==0 and P0_y<0:
            alpha = -math.pi/2
        else:
            alpha = math.atan(P0_y/P0_x)
        #P3相对于P1坐标系的位置
        P1_x,P1_y,P1_z = coordinate_transformation((P0_x,P0_y,P0_z),(-self.lengths[0],0,0,0,0,-alpha))
        num = (self.lengths[1]**2+self.lengths[2]**2-P1_x**2-P1_z**2)/(2*self.lengths[1]*self.lengths[2])
        if num<-1 or num>1:
            return None
        else:
            gamma = math.asin(num)
        if gamma == math.pi/2:
            return None
        else:
            num = (P1_z*self.lengths[1]-P1_z*self.lengths[2]*math.sin(gamma)+P1_x*self.lengths[2]*
                    math.cos(gamma))/(-self.lengths[1]**2+2*self.lengths[1]*self.lengths[2]*math.sin(gamma)-self.lengths[2]**2)
            if num<-1 or num>1:
                return None
            else:
                beta = math.asin((P1_z*self.lengths[1]-P1_z*self.lengths[2]*math.sin(gamma)+P1_x*self.lengths[2]*math.cos(gamma))/
                    (-self.lengths[1]**2+2*self.lengths[1]*self.lengths[2]*math.sin(gamma)-self.lengths[2]**2))
        return alpha, beta, gamma
    #绘制三维图
    def visualize3d(self, fig=None, ax=None, is_axis=0, transform_matrix=np.identity(4)):
        if fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(projection="3d", proj_type="persp")
        # Points P0-04
        global_nodes = []
        for i, p in enumerate(self.nodes):
            global_nodes.append(coordinate_trans_matrix(p.get_coordinates(),transform_matrix))
        for p in global_nodes:
            if i == 0:
                color = 'r'
            else:
                color = 'k'
            ax.scatter(p[0], p[1], p[2], s=100, color=color)
        for l in [(0, 1), (1, 2), (2, 3)]:
            px = [global_nodes[l[0]][0], global_nodes[l[1]][0]]
            py = [global_nodes[l[0]][1], global_nodes[l[1]][1]]
            pz = [global_nodes[l[0]][2], global_nodes[l[1]][2]]
            ax.plot(px, py, pz, lw=10, color='royalblue', alpha=0.6)
        # add axis
        if is_axis:
            transformMatrix1 = translation_rotate_matrix([self.axis_x,self.axis_y,self.axis_z,self.axis_alpha,self.axis_beta,self.axis_gama])
            transformMatrix = np.dot(transform_matrix,transformMatrix1)
            draw_axis(transformMatrix, scale=5, txt='P0', fontsize=12, fig=fig, ax=ax)
            transformMatrix1 = translation_rotate_matrix([0, 0, 0, 0, 0, self.angles[0]])
            transformMatrix2 = translation_rotate_matrix([self.lengths[0], 0, 0, 0, 0, 0])
            transformMatrix = np.dot(transformMatrix,np.dot(transformMatrix1,transformMatrix2))
            draw_axis(transformMatrix, scale=5, txt='P1', fontsize=12, fig=fig, ax=ax)
            transformMatrix1 = translation_rotate_matrix([0, 0, 0, 0, self.angles[1], 0])
            transformMatrix2 = translation_rotate_matrix([self.lengths[1], 0, 0, 0, 0, 0])
            transformMatrix = np.dot(transformMatrix,np.dot(transformMatrix1,transformMatrix2))
            draw_axis(transformMatrix, scale=5, txt='P2', fontsize=12, fig=fig, ax=ax)
            transformMatrix1 = translation_rotate_matrix([0, 0, 0, 0, self.angles[2], 0])
            transformMatrix2 = translation_rotate_matrix([0, 0, -self.lengths[2], 0, 0, 0])
            transformMatrix = np.dot(transformMatrix,np.dot(transformMatrix1,transformMatrix2))
            draw_axis(transformMatrix, scale=5, txt='P3', fontsize=12, fig=fig, ax=ax)
            draw_axis(np.identity(4),scale=5,txt='global',fig=fig,ax=ax)
        # adjustment
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        ax.set_aspect('equal')
        return fig, ax
#定义六足机器人
class Hexapod:
    #初始化
    def __init__(self,body_size=BODY_SIZE,body_attitude=BODY_ATTITUDE,leg_length=HEXAPOD_LEG_LENGTH,leg_angle=HEXAPOD_LEG_ANGLE,
                 angle_bias=HEXAPOD_ANGLE_BIAS,angle_limits=HEXAPOD_ANGLE_LIMITS,leg_rot=HEXAPOD_LEG_ROT):
        self.body = Body(body_size, body_attitude)
        self.legs = []
        leg_trans = ((self.body.m, 0, 0), (self.body.f, self.body.s, 0), (-self.body.f, self.body.s, 0),
                     (-self.body.m, 0, 0), (-self.body.f, -self.body.s, 0), (self.body.f, -self.body.s, 0))
        for k, v in LEG_ID_NAMES.items():
            datumaxis = leg_trans[k] + leg_rot[k]
            self.legs.append(Leg(lengths=leg_length[k], angles=leg_angle[k], angle_bias=angle_bias[k], name=v,
                                 datumaxis=datumaxis, angle_limits=angle_limits[k]))
        self.state = 'static'
        self.support_leg = (0,1,2,3,4,5)
        self.walking_sequance = []
    #初始化腿
    def init_legs(self,leg_length=HEXAPOD_LEG_LENGTH,leg_angle=HEXAPOD_LEG_ANGLE,angle_bias=HEXAPOD_ANGLE_BIAS,
                  angle_limits=HEXAPOD_ANGLE_LIMITS,leg_rot=HEXAPOD_LEG_ROT):
        self.legs = []
        leg_trans = ((self.body.m, 0, 0), (self.body.f, self.body.s, 0), (-self.body.f, self.body.s, 0),
                     (-self.body.m, 0, 0), (-self.body.f, -self.body.s, 0), (self.body.f, -self.body.s, 0))
        for k, v in LEG_ID_NAMES.items():
            datumaxis = leg_trans[k] + leg_rot[k]
            self.legs.append(Leg(lengths=leg_length[k], angles=leg_angle[k], angle_bias=angle_bias[k], name=v,
                               datumaxis=datumaxis, angle_limits=angle_limits[k]))
    #复位
    def reset(self,body_attitude=BODY_ATTITUDE,leg_angle=HEXAPOD_LEG_ANGLE,time=1):
        self.body.update_attitude(body_attitude)
        angle_setting = {}
        i = 0
        for leg in self.legs:
            leg.update_pose(leg_angle[i])
            angle_setting[leg.name] = leg_angle[i]
            i += 1
        self.walking_sequance.append((angle_setting,time))
    #获得腿部关节角度
    def get_legs_angle(self):
        pose = {}
        for leg in self.legs:
            leg_dict = leg.get_angle()
            pose[leg.name] = leg_dict
        return pose
    #更改腿部关节角度
    def change_legs_angle(self,new_angle):
        for name, angle in new_angle.items():
            for leg in self.legs:
                if leg.name == name and angle!=None:
                    leg.update_pose(angle)
                    break
    #更改body尺寸
    def change_body_size(self,size):
        self.body.change_size(size)
        self.init_legs()
    #更改body坐标
    def change_body_attitude(self,attitude):
        self.body.update_attitude(attitude)
        self.init_legs()
    #改变运动模式
    def change_sport_type(self,type):
        if type == 'static':
            self.state = 'static'
            self.support_leg = (0, 1, 2, 3, 4, 5)
        elif type == 'move':
            self.atate = 'move'
        else:
            raise ValueError
    #身体姿态变化增量
    def support_leg_transform(self, transform):
        angle_setting = {}
        for i in self.support_leg:
            old_body_coordinates = self.legs[i].nodes[3].get_coordinates()
            new_body_coordinates = coordinate_transformation(old_body_coordinates,
                                                             (-transform[0],-transform[1],-transform[2],0,0,0))
            new_body_coordinates = coordinate_transformation(new_body_coordinates,
                                                             (0,0,0,-transform[3],-transform[4],-transform[5]))
            delta_coordinates = (new_body_coordinates[j]-old_body_coordinates[j] for j in range(3))
            angle = self.legs[i].solve_ik(delta_coordinates)
            angle_setting[self.legs[i].name] = angle
        self.change_legs_angle(angle_setting)
        self.body.transform(transform)
        return angle_setting
    #移动身体(相对位置)
    def move_body(self,transform,interposeNum=1,total_time=1,is_gif=False):
        trans = [elem / interposeNum for elem in transform]
        frames = []
        index = 0
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/move_body_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1
        for i in range(interposeNum):
            angle_setting = self.support_leg_transform(trans)
            self.walking_sequance.append((angle_setting,total_time/interposeNum))
            if is_gif:
                fig, ax = self.visualize3d()
                filename = "image/move_body_picture"+str(index)+".png"
                plt.savefig(filename)
                frames.append(Image.open(filename))
                index = index+1
        if is_gif:
            frames[0].save('image/animation.gif', format='GIF', append_images=frames[1:], save_all=True, duration=200, loop=0)
            for i in range(index):
                filename = "image/move_body_picture" + str(i) + ".png"
                os.remove(filename)
        return frames

    #旋转动作
    def rotate_move(self,rotate_angle,support_leg=(0,2,4),height=5,total_time=1,is_gif=False):
        self.support_leg = support_leg
        angle_setting = {}
        frames = []
        index = 0
        speed_time = total_time/5
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1
        angle_setting = {}
        for i in range(len(self.legs)):
            if i not in self.support_leg:
                angle = self.legs[i].solve_ik((0,0,height))
                angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting,speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        tem_frames = self.move_body(transform=(0,0,0,0,0,rotate_angle),interposeNum=1,total_time=speed_time,is_gif=is_gif)
        if is_gif:
            frames = frames+tem_frames

        angle_setting = {}
        for i in range(len(self.legs)):
            if i not in self.support_leg:
                angle = self.legs[i].solve_ik((0,0,-height))
                angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting, speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        angle_setting = {}
        for i in self.support_leg:
            angle = self.legs[i].solve_ik((0,0,height))
            angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting, speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        angle_setting = {}
        for i in self.support_leg:
            old_body_coordinates = self.legs[i].nodes[3].get_coordinates()
            new_body_coordinates = coordinate_transformation(old_body_coordinates,
                                                             (0, 0, 0, 0, 0, rotate_angle))
            delta_coordinates = (new_body_coordinates[j] - old_body_coordinates[j] for j in range(3))
            angle = self.legs[i].solve_ik(delta_coordinates)
            angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting, speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        angle_setting = {}
        for i in self.support_leg:
            angle = self.legs[i].solve_ik((0,0,-height))
            angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting,speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        if is_gif:
            frames[0].save('image/animation.gif', format='GIF', append_images=frames[1:], save_all=True, duration=200, loop=0)
            for i in range(index):
                filename = "image/rotate_move_picture" + str(i) + ".png"
                os.remove(filename)
    #三角步态
    def tripod_forward(self,forward_distance,support_leg=(0,2,4),height=5,total_time=1,is_gif=False):
        self.support_leg = support_leg
        frames = []
        index = 0
        speed_time = total_time/6
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        angle_setting = {}
        for i in range(len(self.legs)):
            if i not in self.support_leg:
                angle = self.legs[i].solve_ik((0, forward_distance/2, height))
                angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting, speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        tem_frames = self.move_body(transform=(0,forward_distance/2,0,0,0,0),interposeNum=1,total_time=speed_time,is_gif=is_gif)
        if is_gif:
            frames = frames + tem_frames

        angle_setting = {}
        for i in range(len(self.legs)):
            if i not in self.support_leg:
                angle = self.legs[i].solve_ik((0, 0, -height))
                angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting, speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        new_support_leg = ()
        for i in range(len(self.legs)):
            if i not in self.support_leg:
                new_support_leg = new_support_leg+(i,)
        self.support_leg = new_support_leg

        angle_setting = {}
        for i in range(len(self.legs)):
            if i not in self.support_leg:
                angle = self.legs[i].solve_ik((0,0,height))
                angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting, speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        tem_frames = self.move_body(transform=(0,forward_distance/2,0,0,0,0),interposeNum=1,total_time=speed_time,is_gif=is_gif)
        if is_gif:
            frames = frames + tem_frames

        angle_setting = {}
        for i in range(len(self.legs)):
            if i not in self.support_leg:
                angle = self.legs[i].solve_ik((0,forward_distance/2,-height))
                angle_setting[self.legs[i].name] = angle
        self.walking_sequance.append((angle_setting, speed_time))
        self.change_legs_angle(angle_setting)
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1

        if is_gif:
            frames[0].save('image/animation.gif', format='GIF', append_images=frames[1:], save_all=True, duration=200,
                           loop=0)
            for i in range(index):
                filename = "image/rotate_move_picture" + str(i) + ".png"
                os.remove(filename)
    #波动步态
    def wave_forward(self,forward_distance,support_leg=(0,1,2,3,4,5),height=5,total_time=1,is_gif=False):
        self.support_leg = support_leg
        frames = []
        index = 0
        speed_time = total_time/13
        if is_gif:
            fig, ax = self.visualize3d()
            filename = "image/rotate_move_picture" + str(index) + ".png"
            plt.savefig(filename)
            frames.append(Image.open(filename))
            index = index + 1
        nums = [2,1,3,0,4,5]
        for i in range(6):
            leg_num = nums[i]
            angle_setting = {}
            angle = self.legs[leg_num].solve_ik((0,forward_distance,height))
            angle_setting[self.legs[leg_num].name] = angle
            self.walking_sequance.append((angle_setting, speed_time))
            self.change_legs_angle(angle_setting)
            if is_gif:
                fig, ax = self.visualize3d()
                filename = "image/rotate_move_picture" + str(index) + ".png"
                plt.savefig(filename)
                frames.append(Image.open(filename))
                index = index + 1

            angle_setting = {}
            angle = self.legs[leg_num].solve_ik((0,0,-height))
            angle_setting[self.legs[leg_num].name] = angle
            self.walking_sequance.append((angle_setting, speed_time))
            self.change_legs_angle(angle_setting)
            if is_gif:
                fig, ax = self.visualize3d()
                filename = "image/rotate_move_picture" + str(index) + ".png"
                plt.savefig(filename)
                frames.append(Image.open(filename))
                index = index + 1

        tem_frames = self.move_body(transform=(0,forward_distance,0,0,0,0),interposeNum=1,total_time=speed_time,is_gif=is_gif)
        if is_gif:
            frames = frames + tem_frames

        if is_gif:
            frames[0].save('image/animation.gif', format='GIF', append_images=frames[1:], save_all=True, duration=200,
                           loop=0)
            for i in range(index):
                filename = "image/rotate_move_picture" + str(i) + ".png"
                os.remove(filename)

    #读取步态序列
    def load_walking_sequance(self):
        sequance = self.walking_sequance
        self.walking_sequance = []
        return sequance
    #编码器
    def encoding(self):
        sequance = self.load_walking_sequance()
        coding = []
        for item in sequance:
            angle_setting, speed_time = item
            time_str = str(int(speed_time*1000)).zfill(4)
            string = "{"
            for key,value in angle_setting.items():
                if value == None:
                    coding = []
                    self.reset()
                    self.walking_sequance = []
                    return coding
                num_list = [num for num,name in LEG_ID_NAMES.items() if name == key]
                num = num_list[0]
                alpha,beta,gama = value
                index1 = str(num*3).zfill(3)
                real_alpha = alpha+self.legs[num].angle_bias[0]
                pwm1 = str(int(real_alpha/math.pi*2*1000+1500)).zfill(4)
                string1 = "#"+index1+"P"+pwm1+"T"+time_str+"!"
                index2 = str(num*3+1).zfill(3)
                real_beta = -beta - self.legs[num].angle_bias[1]
                pwm2 = str(int(real_beta/math.pi*2*1000+1500)).zfill(4)
                string2 = "#"+index2+"P"+pwm2+"T"+time_str+"!"
                index3 = str(num*3+2).zfill(3)
                real_gama = gama + self.legs[num].angle_bias[2]
                pwm3 = str(int(real_gama/math.pi*2*1000+1500)).zfill(4)
                string3 = "#"+index3+"P"+pwm3+"T"+time_str+"!"
                string = string+string1+string2+string3
            string = string+"}"
            coding.append((string, speed_time))
        return coding
    #解码器
    def decoding(self,send_message):
        sequance = []
        index = [i for i,c in enumerate(send_message) if c == "#"]
        index.append(len(send_message))
        for i in range(len(index)-1):
            string = send_message[index[i]:index[i+1]-1].strip()
            num = int(string[1:4])
            leg_num = int(num/3)
            leg_name = LEG_ID_NAMES[leg_num]
            node_num = num%3
            pwm = int(string[5:9])
            angle = ((-1)**node_num)*((pwm-1500)/1000*math.pi/2-self.legs[leg_num].angle_bias[node_num])
            time = int(string[10:14])
            time = time/1000
            if node_num==0:
                sequance.append((leg_name,'alpha',angle,time))
            if node_num==1:
                sequance.append((leg_name,'beta',angle,time))
            if node_num==2:
                sequance.append((leg_name,'gama',angle,time))
        return sequance
    #更新角度
    def update_angle_sequance(self,sequance):
        new_angle = {}
        for item in sequance:
            leg_name, node_name, angle = item
            if leg_name not in new_angle:
                num_list = [num for num, name in LEG_ID_NAMES.items() if name == leg_name]
                index = num_list[0]
                new_angle[leg_name] = self.legs[index].angles
            if node_name == "alpha":
                new_angle[leg_name][0] = angle
            elif node_name == "beta":
                new_angle[leg_name][1] = angle
            elif node_name == "gama":
                new_angle[leg_name][2] = angle
        self.change_legs_angle(new_angle)


    #绘制三维图
    def visualize3d(self, fig=None, ax=None):
        if fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(projection="3d")
        fig, ax = self.body.visualize3d(fig, ax)
        for leg in self.legs:
            fig, ax = leg.visualize3d(fig, ax, transform_matrix=self.body.attitude_matrix)
        ax.set_zlim([0, 10])
        ax.set_aspect('equal')
        return fig, ax




if __name__ == "__main__":
    # body = Body()
    # body.update_attitude([10,5,0,math.pi/4,math.pi/6,0])
    # print(BODY_ATTITUDE)
    # fig, ax = body.visualize3d(is_axis=True)
    # plt.show()

    # leg = Leg(datumaxis=(5,10,0,0,0,math.pi/6))
    # fig, ax = leg.visualize3d(is_axis=1)
    # alpha,beta,gama = leg.solve_ik((-10,10,5))
    # leg.update_pose((alpha,beta,gama))
    # print([leg.nodes[3].x,leg.nodes[3].y,leg.nodes[3].z])
    # fig, ax = leg.visualize3d(is_axis=1)
    # plt.show()

    hexapod = Hexapod(body_attitude=(0,5,10,math.pi/6,0,math.pi/4))
    # fig, ax = hexapod.visualize3d()
    hexapod.reset()
    # fig, ax = hexapod.visualize3d()
    # hexapod.change_legs_angle({"MiddleRight":[0,0,math.pi/6],"FrontRight":[math.pi/4,0,0]})
    # fig, ax = hexapod.visualize3d()
    # hexapod.change_body_size((5,8,8))
    # fig, ax = hexapod.visualize3d()
    hexapod.move_body(transform=(0,0,0,math.pi/12,0,0),interposeNum=1,is_gif=True)
    #hexapod.move_body(transform=(0,3,0,0,0,0), interposeNum=1, is_gif=True)
    #hexapod.rotate_move(rotate_angle=math.pi/8,is_gif=True)
    hexapod.tripod_forward(forward_distance=20,is_gif=True)
    #hexapod.wave_forward(forward_distance=5, is_gif=True)
    #encoding = hexapod.encoding()
    #angle = hexapod.get_legs_angle()
    plt.show()