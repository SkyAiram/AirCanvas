import cv2

from objects.image_object import ImageObject


class ObjectManager:

    def __init__(self):

        self.objects = []

        self.selected_object = None

    # ==================================
    # IMPORTAR
    # ==================================

    def add_image(
        self,
        path,
        x=350,
        y=150
    ):

        image = cv2.imread(
            path,
            cv2.IMREAD_UNCHANGED
        )

        if image is None:

            print(
                "No se pudo abrir:",
                path
            )

            return None

        obj = ImageObject(
            image,
            x=x,
            y=y
        )

        self.objects.append(
            obj
        )

        self.select(
            obj
        )

        return obj

    # ==================================
    # SELECCIONAR
    # ==================================

    def select(self, obj):

        for item in self.objects:
            item.selected = False

        self.selected_object = obj

        if obj is not None:
            obj.selected = True

    # ==================================
    # SELECCIONAR EN PUNTO
    # ==================================

    def select_at(self, point):

        # Recorremos al revés porque
        # el último objeto está encima.

        for obj in reversed(
            self.objects
        ):

            if obj.contains(point):

                self.select(obj)

                return obj

        self.select(None)

        return None

    # ==================================
    # DIBUJAR
    # ==================================

    def draw(self, frame):

        for obj in self.objects:

            obj.draw(frame)