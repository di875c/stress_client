import pandas as pd
from django.test import TestCase, Client
from stress_service.utils import cs_converter, cs_utils, uid_generate
from stress_service.views import cs_calculation_view
import pandas as pd


L_SECTION = [{'type': 'L-Section', 'area': 79.0, 'cog_Y': 13.514, 'cog_Z': 17.017, 'Iyy': 33088.41, 'Izz': 29907.99,
          'Iyz': 10931.45, 'J': 25.28, 'Iyy_cog': 10211.329, 'Izz_cog': 15479.305, 'Iyz_cog': -7236.8226,
          'alpha': -35.0, 'Imain_1': 5144.05, 'Imain_2': 20546.58, 'I0': 7.27e-09}]


class UtilsTestCases(TestCase):
    def test_cs_fem_polygon(self):
        input_list = [{'type': 'FEM-Polygon', 'y_0': '0', 'y_1': '0', 'y_2': '10', 'y_3': '0',
                       'z_0': '0', 'z_1': '10', 'z_2': '0', 'z_3': '0', 'points': '4'}]
        result, picture = cs_converter(input_list)
        res_properties = [{'type': 'FEM-Polygon', 'area': 50.0, 'Iyy': 277.78, 'Izz': 277.78, 'Iyz': -138.89, 'J': 260.92, 'phi': -135.0}]
        for k, v in res_properties[0].items():
            self.assertAlmostEqual(v, result[0][k], places=2)

    def test_cs_l_angle(self):
        input_list = [{'type': 'L-Section', 'height': '40', 'th_1': '1.0', 'width_1': '40', 'th_2': '1.0', 'alpha':
                       '10.0', 'div_y': '5.1', 'div_z': '5'}]
        result, picture = cs_converter(input_list)
        for k, v in L_SECTION[0].items():
            self.assertAlmostEqual(v, result[0][k], places=2)

    def test_cs_wrong_table_name(self):
        input_list = [{'type': 'LSection', 'height': '40', 'th_1': '1.0', 'width_1': '40', 'th_2': '1.0', 'alpha':
            '10.0', 'div_y': '5.1', 'div_z': '5'}]
        with self.assertRaises(AttributeError) as error:
            cs_converter(input_list)
        self.assertEqual(error.exception.__str__(), 'Wrong section name')


class ViewsTestCases(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.path = './tests/test_input/'
        cls.client = Client()
        cls.url = '/stress-service/ajax/CS-calculation/'

    def test_cs_calc(self):
        input_data = {'table_name': 'L-Section', 'height': '40', 'th_1': '1.0', 'width_1': '40', 'th_2': '1.0',
                      'alpha': '10.0', 'div_y': '5.1', 'div_z': '5'}
        response = self.client.post(self.url, input_data)
        response_dct = response.json()
        df = pd.DataFrame(L_SECTION).to_html(justify='left', classes="table table-striped", max_rows=10,
                                             float_format=lambda x: f"{x:.2f}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_dct['messages'], 'Расчет выполнен')
        self.assertEqual(response_dct['html'], df)

    def test_cs_calc_fem_polygon_file(self):

        with open(''.join((self.path, 'l_section.csv')), 'r') as input_file:
            input_data = {'table_name': 'FEM-Polygon', 'excel_selection': 'on', 'attachment': input_file}
            response = self.client.post(self.url, input_data)
        print(response)
