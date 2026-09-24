import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import cv2
import numpy as np
from canvas.drawing_canvas import DrawingCanvas
from objects.object_manager import ObjectManager
from objects.background import remove_uniform_background
from ui.retro_ui import RetroUI
from hand_tracking.gestures import detect_gesture, distance
from hand_tracking.smoother import CursorSmoother

BASE = Path(__file__).resolve().parent
PALETTES = {
    'NEON DRIVE': ['#ff48be','#53e8e5','#ffe66d','#9163ff','#ff784f','#f7e8f4',
                   '#171120','#ff3c65','#59efa9','#418dff','#aeb5cc','#ffffff'],
    'SUNSET FM': ['#ff5e78','#ff9472','#ffc857','#ffe6b3','#b96dce','#674ba8',
                  '#302248','#15152b','#ebadca','#66b8bc','#f3f0df','#ffffff'],
    'ARCADE': ['#f93855','#33ec88','#ffe537','#367dff','#b764ff','#14e2ee',
               '#151521','#6c6b86','#c1c7d7','#ff9639','#f85cbd','#ffffff']}


class AirCanvas:
    def __init__(self):
        self.width,self.height = 1280,760
        self.ui=RetroUI()
        self.canvas=DrawingCanvas(self.width,self.height)
        self.objects=ObjectManager()
        self.tool='PENCIL'
        self.palettes={k:list(v) for k,v in PALETTES.items()}
        try:
            data=json.loads((BASE/'palettes.json').read_text())
            if (set(data)==set(PALETTES) and all(len(v)==12 and all(
                isinstance(c,str) and len(c)==7 and c[0]=='#' and int(c[1:],16)>=0
                for c in v) for v in data.values())):
                self.palettes=data
        except (OSError,ValueError,TypeError):
            pass
        self.palette_index=0
        self.color_index=0
        self.mouse_down=False
        self.drag=None
        self.hand_down=False
        self.hand_started=False
        self.scale_start=None
        self.smoother=CursorSmoother(.35)
        self.set_palette()

    @property
    def bounds(self):
        return (250,63,self.width-19,self.height-40)

    def inside(self,p):
        l,t,r,b=self.bounds
        return l<=p[0]<r and t<=p[1]<b

    def set_palette(self):
        name=list(self.palettes)[self.palette_index]
        self.ui.palette_name=name
        self.ui.colors=[tuple(bytes.fromhex(c[1:])[::-1]) for c in self.palettes[name]]
        self.ui.active_color=self.color_index
        self.canvas.color=self.ui.colors[self.color_index]

    def dialog(self,callback):
        root=tk.Tk()
        root.withdraw()
        root.attributes('-topmost',True)
        try:
            return callback(root)
        finally:
            root.destroy()

    def action(self,key):
        self.release()
        try:
            if key in ('PENCIL','LINE','RECT','ELLIPSE','DOTS','ERASER','SELECT','POINTER'):
                self.tool=key
                self.canvas.mode=key
            elif key.startswith('color_'):
                self.color_index=int(key.split('_')[1])
                self.set_palette()
            elif key=='palette':
                self.palette_index=(self.palette_index+1)%len(self.palettes)
                self.set_palette()
            elif key=='edit_color':
                name=self.ui.palette_name
                color=self.dialog(lambda root:colorchooser.askcolor(
                    self.palettes[name][self.color_index],parent=root,title='Editar color activo'))[1]
                if color:
                    self.palettes[name][self.color_index]=color
                    self.set_palette()
                    (BASE/'palettes.json').write_text(json.dumps(self.palettes,indent=2))
            elif key in ('minus','plus'):
                self.canvas.set_thickness(self.canvas.thickness+(2 if key=='plus' else -2))
            elif key=='import':
                path=self.dialog(lambda root:filedialog.askopenfilename(parent=root,
                    title='Importar imagen',filetypes=[('Imagenes','*.png *.jpg *.jpeg *.webp *.bmp')]))
                if path:
                    obj=self.objects.add_image(path,400,180)
                    if obj is None:
                        raise ValueError('No se pudo abrir la imagen')
                    obj.source_image=obj.original_image.copy()
                    self.tool='POINTER'
            elif key=='export':
                path=self.dialog(lambda root:filedialog.asksaveasfilename(parent=root,
                    title='Exportar SVG',defaultextension='.svg',initialfile='air-canvas.svg',
                    filetypes=[('SVG','*.svg')]))
                if path:
                    self.canvas.export_svg(path,self.objects.objects,self.bounds)
                    self.ui.message='SVG guardado: '+Path(path).name
            elif key in ('undo','redo','clear'):
                if key!='clear' or self.dialog(lambda root:messagebox.askyesno(
                    'Limpiar trazos','Se borraran todos los trazos. Continuar?',parent=root)):
                    getattr(self.canvas,key)()
            else:
                obj=self.objects.selected_object
                if obj is None:
                    self.ui.message='Selecciona una imagen con MOVER primero'
                    return
                if key=='remove_bg':
                    obj.original_image=remove_uniform_background(obj.original_image)
                    self.ui.message='Fondo uniforme eliminado / RESTAURAR para recuperar'
                elif key=='restore_bg':
                    obj.original_image=obj.source_image.copy()
                elif key=='delete':
                    self.objects.objects.remove(obj)
                    self.objects.select(None)
                elif key in ('front','back'):
                    self.objects.objects.remove(obj)
                    self.objects.objects.insert(len(self.objects.objects) if key=='front' else 0,obj)
        except (OSError,ValueError,cv2.error,tk.TclError) as exc:
            self.ui.message='Error: '+str(exc)[:90]

    def press(self,p):
        key=self.ui.get_button_at(p)
        if key:
            self.action(key)
            return False
        if not self.inside(p):
            return False
        if self.tool in ('POINTER','SELECT'):
            self.drag=self.objects.select_at(p)
            if self.drag:
                self.drag.start_drag(p)
        else:
            self.canvas.draw(p,erase=self.tool=='ERASER')
        return True

    def move(self,p):
        if self.drag:
            self.drag.drag_to(p)
        elif self.inside(p) and self.tool not in ('POINTER','SELECT'):
            self.canvas.draw(p,erase=self.tool=='ERASER')
        else:
            self.canvas.stop_drawing()

    def release(self):
        self.canvas.stop_drawing()
        self.drag=None

    def mouse(self,event,x,y,flags,param):
        p=(x,y)
        if event==cv2.EVENT_LBUTTONDOWN:
            self.release()
            self.mouse_down=self.press(p)
        elif event==cv2.EVENT_MOUSEMOVE and self.mouse_down:
            self.move(p)
        elif event==cv2.EVENT_LBUTTONUP:
            self.release()
            self.mouse_down=False
        elif event==cv2.EVENT_MOUSEWHEEL and self.inside(p):
            obj=self.objects.selected_object
            if obj:
                delta=(flags>>16)&0xffff
                if delta>=32768:
                    delta-=65536
                obj.set_width(obj.width*(1.1 if delta>0 else 1/1.1))

    def render(self,frame=None,gesture='NONE',hand=False):
        if frame is None:
            frame=np.full((self.height,self.width,3),self.ui.PANEL,np.uint8)
            # A quiet paper workspace, with sparse monochrome registration dots.
            frame[79:self.height-40:24,266:self.width-19:24]=(204,214,219)
        frame=self.canvas.overlay(frame)
        self.objects.draw(frame)
        return self.ui.draw(frame,self.tool,gesture,hand,self.canvas.thickness)

    def run(self):
        cap=cv2.VideoCapture(0)
        tracker=None
        try:
            from hand_tracking.tracker import HandTracker
            tracker=HandTracker()
        except (ImportError,AttributeError,RuntimeError) as exc:
            self.ui.message='Modo raton / seguimiento no disponible'
            print('Seguimiento de manos no disponible:',exc)
        cv2.namedWindow('Air Canvas')
        cv2.setMouseCallback('Air Canvas',self.mouse)
        self.ui.message='Arrastra para dibujar / MOVER + rueda para escalar / Q salir'
        self.render()
        try:
            while True:
                ok,frame=cap.read() if cap.isOpened() else (False,None)
                landmarks=[]
                if ok:
                    frame=cv2.resize(cv2.flip(frame,1),(self.width,self.height))
                    if tracker:
                        frame,landmarks=tracker.detect(frame)
                gesture=detect_gesture(landmarks)
                cursor=self.smoother.update(landmarks[8]) if landmarks else None
                if not self.mouse_down:
                    if gesture=='DRAW':
                        if not self.hand_down:
                            self.release()
                            self.hand_started=self.press(cursor)
                        elif self.hand_started:
                            self.move(cursor)
                    else:
                        if self.hand_down or gesture!='ERASE':
                            self.release()
                        if gesture=='ERASE' and cursor and self.inside(cursor):
                            self.canvas.erase(cursor)
                        obj=self.objects.selected_object
                        if gesture=='SELECT' and obj and self.tool in ('POINTER','SELECT'):
                            d=max(1,distance(landmarks[8],landmarks[12]))
                            if self.scale_start is None:
                                self.scale_start=(d,obj.width)
                            obj.set_width(self.scale_start[1]*d/self.scale_start[0])
                        else:
                            self.scale_start=None
                    self.hand_down=gesture=='DRAW'
                final=self.render(frame,gesture,bool(landmarks))
                if cursor:
                    cv2.circle(final,cursor,8,self.ui.CYAN,2,cv2.LINE_AA)
                cv2.imshow('Air Canvas',final)
                key=cv2.waitKeyEx(1)
                if key in (ord('q'),27) or cv2.getWindowProperty('Air Canvas',cv2.WND_PROP_VISIBLE)<1:
                    break
                shortcuts={ord('z'):'undo',ord('y'):'redo',ord('s'):'export',ord('c'):'clear',
                           ord('v'):'POINTER',ord('b'):'PENCIL',ord('e'):'ERASER',3014656:'delete'}
                if key in shortcuts:
                    self.action(shortcuts[key])
        finally:
            cap.release()
            if tracker:
                tracker.hands.close()
            cv2.destroyAllWindows()


if __name__=='__main__':
    AirCanvas().run()
