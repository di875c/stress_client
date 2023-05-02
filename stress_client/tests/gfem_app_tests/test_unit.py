from ..utils import test_read_excel
from django.test import TestCase, Client
from stress_client.settings import CONFIG

class ViewCases(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.client = Client()
        cls.ref = './tests/test_reference/'

    def smart_check(self, url, input_data: dict, templates: list, page, test_name):
        response = self.client.get(url, input_data)
        self.assertEqual(response.status_code, 200, msg=test_name)
        for template in templates:
            self.assertTemplateUsed(response, template, msg_prefix=test_name)
        # print(response.content.decode('utf8'))
        self.maxDiff = None
        self.assertHTMLEqual(response.content.decode('utf8'), page, msg=test_name) if page else None
        return response

    def test_main_view(self):
        input_data = {}
        with open(''.join((self.ref, 'first_page.html')), 'r', encoding='utf8') as f:
            page = f.read()
        self.smart_check('', input_data, ['first_page.html', 'hf_template.html', 'gfem_rules/node_create_rule.html'],
                         page, 'First page test.')

    def test_post_view(self):
        input_data = {}
        # with open(''.join((self.ref, 'post_page.html')), 'r', encoding='utf8') as f:
        #     page = f.read()
        page = None
        # ToDo correct template for post page and than update checkpoint. Issue with CSFR token
        self.smart_check('/gfem/post_data', input_data, ['post_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Post page test.')

    def test_get_view(self):
        input_data = {}
        with open(''.join((self.ref, 'get_page.html')), 'r', encoding='utf8') as f:
            page = f.read()
        self.smart_check('/gfem/get_data', input_data, ['get_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Post page test.')

    def test_put_view(self):
        input_data = {}
        # with open(''.join((self.ref, 'get_page.html')), 'r', encoding='utf8') as f:
        #     page = f.read()
        page = None
        self.smart_check('/gfem/update_data', input_data, ['change_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Put page test.')

    def test_del_view(self):
        input_data = {}
        # with open(''.join((self.ref, 'get_page.html')), 'r', encoding='utf8') as f:
        #     page = f.read()
        page = None
        self.smart_check('/gfem/delete_data', input_data, ['delete_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Delete page test.')
