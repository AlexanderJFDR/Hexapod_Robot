import numpy as np
#旋转矩阵
def rotate_matrix(angle,axis='X'):
    if axis == 'X':
        mat = np.array([[1,0,0],[0,np.cos(angle),-np.sin(angle)],[0,np.sin(angle),np.cos(angle)]])
    elif axis == 'Y':
        mat = np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
    elif axis == 'Z':
        mat = np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    else:
        raise ValueError
    return mat
#平移旋转矩阵（上级坐标系->次级坐标系旋转顺序X+Y+Z）
def translation_rotate_matrix(transformAttitude):
    X, Y, Z, alpha, beta, gama = transformAttitude
    matX = rotate_matrix(alpha, 'X')
    matY = rotate_matrix(beta, 'Y')
    matZ = rotate_matrix(gama, 'Z')
    transMat = np.dot(np.dot(matX, matY), matZ)
    matrix = np.identity(4)
    matrix[:3, :3] = transMat
    matrix[:3, 3] = [X, Y, Z]
    return matrix
#坐标转换函数（上级坐标系->次级坐标系旋转顺序X+Y+Z,先旋转再平移）
def coordinate_transformation(originCoordinate,transformAttitude):
    X0,Y0,Z0 = originCoordinate
    transformMatrix = translation_rotate_matrix(transformAttitude)
    vector = np.array([X0,Y0,Z0,1])
    newCoordinate = np.dot(transformMatrix,vector)
    return newCoordinate[0], newCoordinate[1], newCoordinate[2]
#坐标转换函数（矩阵版本）
def coordinate_trans_matrix(originCoordinate,matrix):
    X0, Y0, Z0 = originCoordinate
    vector = np.array([X0, Y0, Z0, 1])
    newCoordinate = np.dot(matrix, vector)
    return newCoordinate[0], newCoordinate[1], newCoordinate[2]


