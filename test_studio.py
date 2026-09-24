import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from main import AirCanvas
from canvas.drawing_canvas import DrawingCanvas
from objects.background import remove_uniform_background
from objects.image_object import ImageObject


class StudioTests(unittest.TestCase):
    def test_black_and_erase_history(self):
        c=DrawingCanvas(100,100)
        c.color=(0,0,0)
        c.draw((10,50)); c.draw((90,50)); c.stop_drawing()
        base=np.full((100,100,3),255,np.uint8)
        self.assertEqual(int(c.overlay(base)[50,50,0]),0)
        c.erase((50,50)); c.stop_drawing()
        self.assertEqual(int(c.overlay(base)[50,50,0]),255)
        c.undo()
        self.assertEqual(int(c.overlay(base)[50,50,0]),0)
        c.redo()
        self.assertEqual(int(c.overlay(base)[50,50,0]),255)

    def test_background_preserves_enclosed_white_and_alpha(self):
        image=np.full((50,50,4),255,np.uint8)
        image[10:40,10:40,:3]=0
        image[20:30,20:30,:3]=255
        image[15,15,3]=80
        out=remove_uniform_background(image)
        self.assertEqual(out[0,0,3],0)
        self.assertEqual(out[25,25,3],255)
        self.assertEqual(out[15,15,3],80)

    def test_svg_geometry_masks_and_embedded_images(self):
        c=DrawingCanvas(100,100)
        for mode in ('PENCIL','LINE','RECT','ELLIPSE','DOTS'):
            c.mode=mode
            c.draw((10,10)); c.draw((70,70)); c.stop_drawing()
        c.erase((30,30)); c.stop_drawing()
        c.draw((90,90)); c.stop_drawing()
        obj=ImageObject(np.full((20,20,4),255,np.uint8))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'drawing.svg'
            c.export_svg(path,[obj],(0,0,100,100))
            root=ET.parse(path).getroot()
            ns={'s':'http://www.w3.org/2000/svg'}
            self.assertEqual(len(root.findall('.//s:mask',ns)),1)
            self.assertTrue(root.find('s:image',ns).get('href').startswith('data:image/png;base64,'))
            for tag in ('rect','ellipse','polyline','circle'):
                self.assertIsNotNone(root.find('.//s:'+tag,ns))

    def test_mouse_drag_shape_and_ui_bounds(self):
        app=AirCanvas()
        frame=app.render()
        for x1,y1,x2,y2 in app.ui.buttons.values():
            self.assertTrue(0<=x1<x2<=1280 and 0<=y1<y2<722)
        app.action('RECT')
        app.mouse(cv2.EVENT_LBUTTONDOWN,300,100,0,None)
        app.mouse(cv2.EVENT_MOUSEMOVE,500,250,0,None)
        app.mouse(cv2.EVENT_LBUTTONUP,500,250,0,None)
        self.assertEqual(app.canvas.operations[0]['points'],[(300,100),(500,250)])
        obj=ImageObject(np.zeros((50,50,3),np.uint8),300,100)
        app.objects.objects.append(obj)
        app.action('POINTER')
        app.press((310,110)); app.move((260,90)); app.release()
        self.assertEqual((obj.x,obj.y),(250,80))
        app.objects.select(obj)
        old_width=obj.width
        app.mouse(cv2.EVENT_MOUSEWHEEL,300,100,120<<16,None)
        self.assertGreater(obj.width,old_width)
        cv2.imwrite('exports/ui-preview.png',frame)


if __name__=='__main__':
    unittest.main()
