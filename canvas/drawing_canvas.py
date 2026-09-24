import cv2
import numpy as np
from xml.etree import ElementTree as ET
import base64


class DrawingCanvas:
    """Ordered vector operations; the same geometry drives preview and SVG."""
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.color = (255, 80, 220)
        self.thickness = 5
        self.eraser_size = 24
        self.mode = 'PENCIL'
        self.operations = []
        self.current = None
        self.redo_stack = []

    def draw(self, point, erase=False):
        point = tuple(map(int, point))
        mode = 'ERASER' if erase else self.mode
        if self.current is None:
            self.redo_stack.clear()
            self.current = dict(mode=mode, color=self.color,
                                size=self.eraser_size * 2 if erase else self.thickness,
                                points=[point])
            self.operations.append(self.current)
        if mode in ('LINE', 'RECT', 'ELLIPSE'):
            self.current['points'] = [self.current['points'][0], point]
        elif self.current['points'][-1] != point:
            self.current['points'].append(point)

    def erase(self, point):
        self.draw(point, erase=True)

    def stop_drawing(self):
        self.current = None

    def set_thickness(self, value):
        self.thickness = max(1, min(40, value))

    def clear(self):
        self.stop_drawing()
        self.operations.clear()
        self.redo_stack.clear()

    def undo(self):
        self.stop_drawing()
        if self.operations:
            self.redo_stack.append(self.operations.pop())

    def redo(self):
        self.stop_drawing()
        if self.redo_stack:
            self.operations.append(self.redo_stack.pop())

    def overlay(self, frame):
        layer = np.zeros_like(frame)
        alpha = np.zeros(frame.shape[:2], np.uint8)
        for op in self.operations:
            pts, mode, size = op['points'], op['mode'], op['size']
            mask = np.zeros_like(alpha)
            a, b = pts[0], pts[-1]
            if mode == 'RECT':
                cv2.rectangle(mask, a, b, 255, size, cv2.LINE_AA)
            elif mode == 'ELLIPSE':
                cv2.ellipse(mask, ((a[0]+b[0])//2, (a[1]+b[1])//2),
                            (max(1,abs(a[0]-b[0])//2),max(1,abs(a[1]-b[1])//2)),
                            0, 0, 360, 255, size, cv2.LINE_AA)
            elif mode == 'DOTS':
                for p in pts:
                    cv2.circle(mask,p,max(1,size//2),255,-1,cv2.LINE_AA)
            else:
                cv2.polylines(mask,[np.array(pts,np.int32)],False,255,size,cv2.LINE_AA)
                for p in (a,b):
                    cv2.circle(mask,p,max(1,size//2),255,-1,cv2.LINE_AA)
            if mode == 'ERASER':
                alpha = (alpha.astype(float)*(1-mask/255)).astype(np.uint8)
            else:
                layer[mask > 0] = op['color']
                alpha = np.maximum(alpha,mask)
        mix = alpha[:,:,None]/255
        return (layer*mix+frame*(1-mix)).astype(np.uint8)

    def export_svg(self, path, objects, bounds):
        left,top,right,bottom = bounds
        root = ET.Element('svg',xmlns='http://www.w3.org/2000/svg',
                          width=str(right-left),height=str(bottom-top),
                          viewBox=f'{left} {top} {right-left} {bottom-top}')
        defs = ET.SubElement(root,'defs')
        drawing = ET.SubElement(root,'g')
        def geometry(parent,op,color):
            pts,size,mode=op['points'],op['size'],op['mode']
            a,b=pts[0],pts[-1]
            attrs={'fill':'none','stroke':color,'stroke-width':str(size),
                   'stroke-linecap':'round','stroke-linejoin':'round'}
            if mode=='RECT':
                ET.SubElement(parent,'rect',x=str(min(a[0],b[0])),y=str(min(a[1],b[1])),
                              width=str(abs(a[0]-b[0])),height=str(abs(a[1]-b[1])),**attrs)
            elif mode=='ELLIPSE':
                ET.SubElement(parent,'ellipse',cx=str((a[0]+b[0])/2),cy=str((a[1]+b[1])/2),
                              rx=str(max(1,abs(a[0]-b[0])/2)),ry=str(max(1,abs(a[1]-b[1])/2)),**attrs)
            elif mode=='DOTS' or len(pts)==1:
                for p in pts:
                    ET.SubElement(parent,'circle',cx=str(p[0]),cy=str(p[1]),r=str(size/2),fill=color)
            else:
                ET.SubElement(parent,'polyline',points=' '.join(f'{x},{y}' for x,y in pts),**attrs)
        for i,op in enumerate(self.operations):
            if op['mode']=='ERASER':
                mask=ET.SubElement(defs,'mask',id=f'erase{i}',maskUnits='userSpaceOnUse',
                                   x=str(left),y=str(top),width=str(right-left),height=str(bottom-top))
                ET.SubElement(mask,'rect',x=str(left),y=str(top),width=str(right-left),height=str(bottom-top),fill='white')
                geometry(mask,op,'black')
                root.remove(drawing)
                wrapper=ET.SubElement(root,'g',mask=f'url(#erase{i})')
                wrapper.append(drawing)
                drawing=ET.SubElement(root,'g')
                root.remove(wrapper)
                drawing.append(wrapper)
            else:
                b,g,r=op['color']
                geometry(drawing,op,f'#{r:02x}{g:02x}{b:02x}')
        for obj in objects:
            if not obj.visible:
                continue
            ok,png=cv2.imencode('.png',obj.original_image)
            if not ok:
                raise ValueError('No se pudo codificar la imagen')
            ET.SubElement(root,'image',x=str(obj.x),y=str(obj.y),width=str(obj.width),height=str(obj.height),
                          href='data:image/png;base64,'+base64.b64encode(png).decode('ascii'))
        ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
