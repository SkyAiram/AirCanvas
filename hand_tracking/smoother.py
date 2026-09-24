class CursorSmoother:

    def __init__(self, smoothing=0.25):

        self.smoothing = smoothing

        self.x = None
        self.y = None

    def update(self, point):

        target_x, target_y = point

        if self.x is None:
            self.x = target_x
            self.y = target_y

        else:

            self.x += (
                target_x - self.x
            ) * self.smoothing

            self.y += (
                target_y - self.y
            ) * self.smoothing

        return (
            int(self.x),
            int(self.y)
        )