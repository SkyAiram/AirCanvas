import cv2
import numpy as np


class ImageObject:

    def __init__(
        self,
        image,
        x=300,
        y=150,
        max_width=400,
        max_height=300
    ):

        self.original_image = image

        original_h, original_w = (
            image.shape[:2]
        )

        # ==========================================
        # ESCALA INICIAL
        # ==========================================

        initial_scale = min(
            max_width / original_w,
            max_height / original_h,
            1.0
        )

        self.width = max(1, int(
            original_w
            * initial_scale
        ))

        self.height = max(1, int(
            original_h
            * initial_scale
        ))

        # ==========================================
        # POSICIÓN
        # ==========================================

        self.x = int(x)
        self.y = int(y)

        # ==========================================
        # ESTADO
        # ==========================================

        self.selected = False
        self.visible = True

        # ==========================================
        # TAMAÑO
        # ==========================================

        self.min_size = 60
        self.max_size = 1000

        self.aspect_ratio = (
            original_w
            / original_h
        )

        # ==========================================
        # DRAG
        # ==========================================

        self.drag_offset_x = 0
        self.drag_offset_y = 0


    # ========================================================
    # BOUNDS
    # ========================================================

    def bounds(self):

        return (
            self.x,
            self.y,
            self.x + self.width,
            self.y + self.height
        )


    # ========================================================
    # CENTER
    # ========================================================

    def center(self):

        return (
            self.x
            + self.width // 2,

            self.y
            + self.height // 2
        )


    # ========================================================
    # HIT TEST
    # ========================================================

    def contains(
        self,
        point
    ):

        px, py = point

        x1, y1, x2, y2 = (
            self.bounds()
        )

        return (
            x1 <= px <= x2
            and
            y1 <= py <= y2
        )


    # ========================================================
    # START DRAG
    # ========================================================

    def start_drag(
        self,
        point
    ):

        px, py = point

        # Guardamos exactamente dónde
        # agarraste la imagen.

        self.drag_offset_x = (
            px - self.x
        )

        self.drag_offset_y = (
            py - self.y
        )


    # ========================================================
    # DRAG
    # ========================================================

    def drag_to(
        self,
        point
    ):

        px, py = point

        self.x = int(
            px
            - self.drag_offset_x
        )

        self.y = int(
            py
            - self.drag_offset_y
        )


    # ========================================================
    # CONSTRAIN TO AREA
    # ========================================================

    def constrain_to_area(
        self,
        min_x,
        min_y,
        max_x,
        max_y
    ):
        """
        Mantiene la imagen dentro del área
        útil de Air Canvas.
        """

        area_width = (
            max_x - min_x
        )

        area_height = (
            max_y - min_y
        )

        # ==========================================
        # SI LA IMAGEN ES MÁS ANCHA QUE EL CANVAS
        # ==========================================

        if self.width > area_width:

            self.x = min_x

        else:

            # Límite izquierdo

            if self.x < min_x:

                self.x = min_x

            # Límite derecho

            if (
                self.x
                + self.width
                > max_x
            ):

                self.x = (
                    max_x
                    - self.width
                )


        # ==========================================
        # SI ES MÁS ALTA QUE EL CANVAS
        # ==========================================

        if self.height > area_height:

            self.y = min_y

        else:

            # Límite superior

            if self.y < min_y:

                self.y = min_y

            # Límite inferior

            if (
                self.y
                + self.height
                > max_y
            ):

                self.y = (
                    max_y
                    - self.height
                )


    # ========================================================
    # SET WIDTH / SCALE
    # ========================================================

    def set_width(
        self,
        new_width,
        keep_center=True
    ):

        # ==========================================
        # RECORDAR CENTRO
        # ==========================================

        old_center = (
            self.center()
        )

        # ==========================================
        # LIMITAR TAMAÑO
        # ==========================================

        new_width = int(
            max(
                self.min_size,
                min(
                    self.max_size,
                    new_width
                )
            )
        )

        new_height = max(1, int(
            new_width
            / self.aspect_ratio
        ))

        self.width = (
            new_width
        )

        self.height = (
            new_height
        )

        # ==========================================
        # CONSERVAR CENTRO
        # ==========================================

        if keep_center:

            cx, cy = old_center

            self.x = int(
                cx
                - self.width / 2
            )

            self.y = int(
                cy
                - self.height / 2
            )


    # ========================================================
    # DRAW
    # ========================================================

    def draw(
        self,
        frame
    ):

        if not self.visible:

            return

        frame_h, frame_w = (
            frame.shape[:2]
        )

        if (
            self.width <= 0
            or
            self.height <= 0
        ):

            return


        # ====================================================
        # INTERPOLACIÓN
        # ====================================================

        if (
            self.width
            <
            self.original_image.shape[1]
        ):

            interpolation = (
                cv2.INTER_AREA
            )

        else:

            interpolation = (
                cv2.INTER_LINEAR
            )


        # ====================================================
        # RESIZE
        # ====================================================

        resized = cv2.resize(
            self.original_image,
            (
                self.width,
                self.height
            ),
            interpolation=interpolation
        )


        # ====================================================
        # POSICIÓN
        # ====================================================

        x1 = int(self.x)
        y1 = int(self.y)

        x2 = int(
            x1 + self.width
        )

        y2 = int(
            y1 + self.height
        )


        # ====================================================
        # RECORTAR CONTRA LA PANTALLA
        # ====================================================

        screen_x1 = max(
            0,
            x1
        )

        screen_y1 = max(
            0,
            y1
        )

        screen_x2 = min(
            frame_w,
            x2
        )

        screen_y2 = min(
            frame_h,
            y2
        )


        # Objeto completamente fuera
        # de la pantalla.

        if (
            screen_x1 >= screen_x2
            or
            screen_y1 >= screen_y2
        ):

            return


        # ====================================================
        # REGIÓN CORRESPONDIENTE DE LA IMAGEN
        # ====================================================

        image_x1 = (
            screen_x1 - x1
        )

        image_y1 = (
            screen_y1 - y1
        )

        image_x2 = (
            image_x1
            + screen_x2
            - screen_x1
        )

        image_y2 = (
            image_y1
            + screen_y2
            - screen_y1
        )


        visible = resized[
            image_y1:image_y2,
            image_x1:image_x2
        ]


        if visible.size == 0:

            return


        # ====================================================
        # PNG / RGBA
        # ====================================================

        if (
            len(visible.shape) == 3
            and
            visible.shape[2] == 4
        ):

            rgb = (
                visible[:, :, :3]
                .astype(np.float32)
            )

            alpha = (
                visible[:, :, 3]
                .astype(np.float32)
                / 255.0
            )

            alpha = np.expand_dims(
                alpha,
                axis=2
            )


            background = frame[
                screen_y1:screen_y2,
                screen_x1:screen_x2
            ].astype(
                np.float32
            )


            blended = (

                rgb * alpha

                +

                background
                * (1.0 - alpha)
            )


            frame[
                screen_y1:screen_y2,
                screen_x1:screen_x2
            ] = blended.astype(
                np.uint8
            )


        # ====================================================
        # JPG / RGB
        # ====================================================

        else:

            # Por seguridad, imágenes grayscale

            if len(
                visible.shape
            ) == 2:

                visible = (
                    cv2.cvtColor(
                        visible,
                        cv2.COLOR_GRAY2BGR
                    )
                )


            frame[
                screen_y1:screen_y2,
                screen_x1:screen_x2
            ] = visible


        # ====================================================
        # SELECTION BOX
        # ====================================================

        if self.selected:

            self.draw_selection(
                frame
            )


    # ========================================================
    # SELECTION
    # ========================================================

    def draw_selection(
        self,
        frame
    ):

        x1, y1, x2, y2 = (
            self.bounds()
        )


        # Marco

        cv2.rectangle(
            frame,

            (
                int(x1),
                int(y1)
            ),

            (
                int(x2),
                int(y2)
            ),

            (
                20,
                20,
                20
            ),

            2,

            cv2.LINE_AA
        )


        # Handles

        self.draw_handles(
            frame
        )


    # ========================================================
    # HANDLES
    # ========================================================

    def draw_handles(
        self,
        frame
    ):

        x1, y1, x2, y2 = (
            self.bounds()
        )


        points = [

            (
                x1,
                y1
            ),

            (
                x2,
                y1
            ),

            (
                x1,
                y2
            ),

            (
                x2,
                y2
            )
        ]


        size = 7


        for x, y in points:

            x = int(x)
            y = int(y)


            # Fondo crema

            cv2.rectangle(
                frame,

                (
                    x - size,
                    y - size
                ),

                (
                    x + size,
                    y + size
                ),

                (
                    235,
                    245,
                    245
                ),

                -1
            )


            # Border negro

            cv2.rectangle(
                frame,

                (
                    x - size,
                    y - size
                ),

                (
                    x + size,
                    y + size
                ),

                (
                    20,
                    20,
                    20
                ),

                2
            )
