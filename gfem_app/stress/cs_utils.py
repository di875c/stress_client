import numpy as np


class BaseSquare:
    # def __init__(self, *args, **kwargs):
    #     print('args: ', args, 'kwargs: ', kwargs)
    #     self.x = kwargs['width'] if len(kwargs) > 0 else args[0]['width']
    #     self.y = kwargs['height'] if len(kwargs) > 0 else args[0]['height']
    #     self.area = self.x * self.y
    #     self.div_x = kwargs['div_x'] if len(kwargs) > 0 else args[0]['div_x']
    #     self.div_y = kwargs['div_y'] if len(kwargs) > 0 else args[0]['div_y']
    #     self.alpha = kwargs['alpha'] if len(kwargs) > 0 else args[0]['alpha']
    def __init__(self, x, y, div_x, div_y, alpha):
        self.x = x
        self.y = y
        self.area = x * y
        self.div_x = div_x
        self.div_y = div_y
        self.alpha = alpha



    @property
    def cog(self):
        # TODO: alpha for whole section is not incorporated. It is only for dummy now.
        return self.x/2 + self.div_x, self.y/2 + self.div_y
        # x, y = self.x / 2 + self.div_x, self.y / 2 + self.div_y
        # return x * np.cos(self.alpha) - y * np.sin(self.alpha), x * np.sin(self.alpha) + y * np.cos(self.alpha)

    @property
    def inertia(self):
        return self.x * (self.y**3) / 12 + self.area * self.cog[1]**2, \
               self.y * (self.x**3) / 12 + self.area * self.cog[0]**2, self.area * self.cog[0] * self.cog[1]

    @staticmethod
    def inertia_axis(_area=0, _mom_inertia=[], _div_x=0, _div_y=0, _cog=False, _alpha=0):
        #recalculation moment of inertia in another axis
        k = -1 if _cog else 1
        mom_inertia_x  = _mom_inertia[0] + k * _area * (_div_y ** 2)
        mom_inertia_y = _mom_inertia[1] + k * _area * (_div_x ** 2)
        mom_inertia_xy = _mom_inertia[2] + k * _area * (_div_x * _div_y)
        alpha = np.arctan(2 * mom_inertia_xy/(mom_inertia_x-mom_inertia_y)) / 2 if _cog else _alpha
        mom_inertia_max = mom_inertia_x * (np.cos(k*alpha)**2) + mom_inertia_y * (np.sin(k*alpha)**2) \
                         - mom_inertia_xy * np.sin(k*alpha*2)
        mom_inertia_min = mom_inertia_x * (np.sin(k*alpha)**2) + mom_inertia_y * (np.cos(k*alpha)**2) \
                         + mom_inertia_xy * np.sin(k*alpha*2)
        mom_inertia_0 = (mom_inertia_y - mom_inertia_x) * np.sin(alpha*2) / 2 \
                         + mom_inertia_xy * (np.cos(alpha)**2 - np.sin(alpha)**2)
        return mom_inertia_x, mom_inertia_y, mom_inertia_xy, alpha, mom_inertia_max, mom_inertia_min, mom_inertia_0

    @property
    def output(self):
        return dict(zip(('area', 'cog', 'inertia'), (self.area, self.cog, self.inertia)))


class BaseSegment:
    def __init__(self, radius, seg_angle, div_x, div_y, alpha):
        self.radius = radius
        self.seg_angle = seg_angle / 2
        self.div_x, self.div_y, self.alpha = div_x, div_y, alpha
        self.area = self.seg_angle * radius ** 2

    @property
    def cog(self):
        return self.div_x, self.div_y + 2 / 3 * self.radius * np.sin(self.seg_angle) / self.seg_angle

    @property
    def inertia(self):
        return (self.radius ** 4 / 8 * (2 * self.seg_angle + np.sin(self.seg_angle) -
                32 * np.sin(self.seg_angle)**2 / (9 * self.seg_angle)) + self.area * self.cog[1] ** 2,
                self.radius ** 4 / 8 * (2 * self.seg_angle - np.sin(self.seg_angle)) + + self.area * self.cog[0] ** 2,
                self.area * self.cog[0] * self.cog[1])


class AnySections:
    #TODO: alpha for whole section is not incorporated. It is only for dummy now.
    def __init__(self, *args, **kwargs):
        if 'square' in kwargs:
            self.squares = [BaseSquare(*_square) for _square in kwargs['square']]

    @property
    def area(self):
        return sum(_square.area for _square in self.squares)

    @property
    def cog(self):
        return tuple(
            sum(_square.area * _square.cog[_idx] for _square in self.squares) / self.area for _idx in range(2))

    @property
    def inertia(self):
        _inertia_list = list(map(sum, zip(*[_square.inertia for _square in self.squares])))
        # print(_inertia_list)
        # sum(_square.inertia[_idx] for _square in self.squares) for _idx in range(3)) #Ix, Iy, Ixy
        _inertia_list += BaseSquare.inertia_axis(_area=self.area,
                                                 _mom_inertia=_inertia_list,
                                                 _div_x=self.cog[0],
                                                 _div_y=self.cog[1],
                                                 _cog=True)
        return dict(zip(('Ixx', 'Iyy', 'Ixy', 'Ixx_cog', 'Iyy_cog', 'Ixy_cog', 'alpha', 'Imax_princ', 'Imin_princ'), _inertia_list))

    @property
    def output(self):
        output_dct = dict(zip(('area', 'cog_X', 'cog_Y'), (self.area, *self.cog)))
        output_dct.update(self.inertia)
        return output_dct


class Square(AnySections):
    def __init__(self, *args, **kwargs):
        print('args: ', args, 'kwargs: ', kwargs)
        dct = kwargs if len(kwargs) > 0 else args[0]
        [setattr(self, attr, dct[attr]) for attr in dct]
        super().__init__(square=[(self.width, self.height, self.div_x, self.div_y, self.alpha)])


class AngleSection(AnySections):
    # def __init__(self, height, width, th_1, th_2, div_x=0, div_y=0, alpha=0, dct={}):
    def __init__(self, *args, **kwargs):
        print('args: ', args, 'kwargs: ', kwargs)
        dct = kwargs if len(kwargs) > 0 else args[0]
        [setattr(self, attr, dct[attr]) for attr in dct]
        super().__init__(square=[(self.th_1, self.height, self.div_x, self.div_y, self.alpha),
                                 (self.width - self.th_1, self.th_2, self.div_x + self.th_1, self.div_y, self.alpha)])


class CSection(AnySections):
    # def __init__(self, width_1, height, width_2, th_1, th_2, th_3, div_x=0, div_y=0, alpha=0):
    def __init__(self, *args, **kwargs):
        print('args: ', args, 'kwargs: ', kwargs)
        dct = kwargs if len(kwargs) > 0 else args[0]
        [setattr(self, attr, dct[attr]) for attr in dct]
        super().__init__(square=[(self.width_1, self.th_1, self.div_x, self.div_y + self.height-self.th_1, self.alpha), # upper flange
                                 (self.th_2, self.height - self.th_1 - self.th_3, self.div_x, self.div_y + self.th_3, self.alpha), # web
                                 (self.width_2, self.th_3, self.div_x, self.div_y, self.alpha)  # lower flange
                                 ])


class ISection(AnySections):
    # def __init__(self, width_1, height, width_2, th_1, th_2, th_3, div_x=0, div_y=0, alpha=0):
    def __init__(self, *args, **kwargs):
        print('args: ', args, 'kwargs: ', kwargs)
        dct = kwargs if len(kwargs) > 0 else args[0]
        [setattr(self, attr, dct[attr]) for attr in dct]
        super().__init__(square=[(self.width_1, self.th_1, self.div_x + (self.width_2 - self.width_1) / 2, self.div_y +
                                  self.height-self.th_1, self.alpha), # upper flange
                                 (self.th_2, self.height - self.th_1 - self.th_3, self.div_x +
                                  (self.width_2 - self.th_2) / 2, self.div_y + self.th_3, self.alpha), # web
                                 (self.width_2, self.th_3, self.div_x, self.div_y, self.alpha)  # lower flange
                                 ])
