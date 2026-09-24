import cv2


class RetroUI:
    BG = (232, 242, 248)
    PANEL = (232, 242, 248)
    INK = (49, 53, 47)
    DESKTOP = (108, 199, 118)
    MUTED = (120, 127, 117)
    PINK = INK
    CYAN = INK

    def __init__(self):
        self.sidebar_width = 248
        self.topbar_height = 62
        self.status_height = 38
        self.buttons = {}
        self.colors = []
        self.active_color = 0
        self.palette_name = 'NEON DRIVE'
        self.message = 'Listo para crear'

    def text(self, frame, text, x, y, scale=.4, color=None):
        cv2.putText(frame,text,(x,y),cv2.FONT_HERSHEY_SIMPLEX,scale,
                    color or self.INK,1,cv2.LINE_AA)

    def button(self,frame,key,label,x,y,w=105,h=30,active=False):
        cv2.rectangle(frame,(x+2,y+3),(x+w+2,y+h+3),self.INK,-1)
        cv2.rectangle(frame,(x,y),(x+w,y+h),self.INK if active else self.PANEL,-1)
        cv2.rectangle(frame,(x,y),(x+w,y+h),self.INK,1)
        if active:
            cv2.rectangle(frame,(x+3,y+3),(x+w-3,y+h-3),self.PANEL,1)
        self.text(frame,label,x+9,y+20,.36,self.PANEL if active else self.INK)
        self.buttons[key]=(x,y,x+w,y+h)

    def get_button_at(self,point):
        if point:
            x,y=point
            for key,(a,b,c,d) in self.buttons.items():
                if a<=x<=c and b<=y<=d:
                    return key
        return None

    def draw(self,frame,tool,gesture,hand,size):
        h,w=frame.shape[:2]
        self.buttons.clear()
        # Desktop surround and an offset, solid classic Mac window shadow.
        cv2.rectangle(frame,(0,0),(w,11),self.DESKTOP,-1)
        cv2.rectangle(frame,(0,0),(7,h),self.DESKTOP,-1)
        cv2.rectangle(frame,(w-17,0),(w,h),self.DESKTOP,-1)
        cv2.rectangle(frame,(0,h-12),(w,h),self.DESKTOP,-1)
        cv2.rectangle(frame,(18,h-19),(w-9,h-8),self.INK,-1)
        cv2.rectangle(frame,(w-18,24),(w-9,h-12),self.INK,-1)
        cv2.rectangle(frame,(8,12),(w-18,61),self.BG,-1)
        cv2.rectangle(frame,(8,62),(247,h-39),self.BG,-1)
        cv2.line(frame,(248,62),(248,h-38),self.INK,2)
        cv2.line(frame,(8,61),(w-18,61),self.INK,2)
        for y in range(23,52,5):
            cv2.line(frame,(94,y),(w-190,y),self.MUTED,1)
        cv2.rectangle(frame,(w//2-110,17),(w//2+110,56),self.BG,-1)
        self.text(frame,'AirCanvas',w//2-72,44,.72)
        self.button(frame,'export','EXPORTAR SVG',w-174,22,142)
        for i in range(3):
            cv2.circle(frame,(29+i*23,37),7,self.INK,2,cv2.LINE_AA)
        cv2.circle(frame,(29,37),4,self.INK,-1)
        self.text(frame,'+ Herramientas',16,86,.4)
        tools=[('POINTER','MOVER'),('PENCIL','LAPIZ'),('LINE','LINEA'),('RECT','RECTANGULO'),
               ('ELLIPSE','ELIPSE'),('DOTS','PUNTOS'),('SELECT','SELECCION'),('ERASER','BORRADOR')]
        for i,(key,label) in enumerate(tools):
            self.button(frame,key,label,16+(i%2)*116,99+(i//2)*38,active=tool==key)
        self.text(frame,'Grosor del trazo',16,269,.38)
        self.button(frame,'minus','-',16,281,42)
        self.text(frame,f'{size:02d} PX',91,302,.48)
        self.button(frame,'plus','+',195,281,42)
        self.text(frame,self.palette_name+'  /  12',16,336,.36)
        for i,color in enumerate(self.colors):
            x,y=18+(i%6)*37,349+(i//6)*32
            cv2.rectangle(frame,(x,y),(x+25,y+23),color,-1)
            cv2.rectangle(frame,(x,y),(x+25,y+23),self.INK,1)
            if i==self.active_color:
                cv2.rectangle(frame,(x-3,y-3),(x+28,y+26),self.INK,1)
            self.buttons[f'color_{i}']=(x,y,x+25,y+23)
        self.button(frame,'palette','PALETA >',16,417)
        self.button(frame,'edit_color','EDITAR COLOR',132,417)
        self.text(frame,'+ Imagen y capas',16,471,.4)
        for i,(key,label) in enumerate([('import','+ IMPORTAR'),('remove_bg','QUITAR FONDO'),
                                        ('restore_bg','RESTAURAR'),('delete','ELIMINAR'),
                                        ('front','AL FRENTE'),('back','AL FONDO')]):
            self.button(frame,key,label,16+(i%2)*116,484+(i//2)*38)
        self.button(frame,'undo','DESHACER',16,610)
        self.button(frame,'redo','REHACER',132,610)
        self.button(frame,'clear','LIMPIAR TRAZOS',16,649,221)
        for y in (255,322,457,597):
            cv2.line(frame,(16,y),(237,y),self.MUTED,1)
        cv2.rectangle(frame,(8,h-38),(w-18,h-20),self.BG,-1)
        cv2.line(frame,(8,h-39),(w-18,h-39),self.INK,1)
        self.text(frame,self.message[:100],18,h-24,.32)
        self.text(frame,'MANO: '+('ON' if hand else 'OFF')+' / '+gesture,w-245,h-24,.3)
        cv2.rectangle(frame,(8,12),(w-18,h-20),self.INK,2)
        return frame
