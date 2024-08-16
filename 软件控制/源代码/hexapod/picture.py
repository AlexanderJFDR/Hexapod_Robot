import matplotlib.pyplot as plt
from mathematics import *
#绘制坐标系
def draw_axis(transformMatrix, scale=1, txt=None, fontsize=12,fig=None, ax=None):
    if fig is None:
        fig = plt.figure()
        ax = fig.add_subplot(projection="3d", proj_type="ortho")

    vectorO = np.dot(transformMatrix, [0,0,0,1])
    vectorX = np.dot(transformMatrix, [scale,0,0,1])
    vectorY = np.dot(transformMatrix, [0,scale,0,1])
    vectorZ = np.dot(transformMatrix, [0,0,scale,1])
    ax.quiver3D(vectorO[0],vectorO[1],vectorO[2],vectorX[0]-vectorO[0],vectorX[1]-vectorO[1],
                vectorX[2]-vectorO[2],color='r',length=1)
    ax.text(vectorX[0],vectorX[1],vectorX[2],'x',fontsize=fontsize)
    ax.quiver3D(vectorO[0],vectorO[1],vectorO[2],vectorY[0]-vectorO[0],vectorY[1]-vectorO[1],
                vectorY[2]-vectorO[2],color='g',length=1)
    ax.text(vectorY[0],vectorY[1],vectorY[2],'y',fontsize=fontsize)
    ax.quiver3D(vectorO[0],vectorO[1],vectorO[2],vectorZ[0]-vectorO[0],vectorZ[1]-vectorO[1],
                vectorZ[2]-vectorO[2],color='b',length=1)
    ax.text(vectorZ[0],vectorZ[1],vectorZ[2],'z',fontsize=fontsize)
    ax.text(vectorO[0],vectorO[1],vectorO[2],txt,fontsize=fontsize)

