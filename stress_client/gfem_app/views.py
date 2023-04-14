import json, re
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from stress_client.settings import SERVER, CONFIG
import requests
from json2html import *
from .forms import *
from .utils import convert_to_xlsx, from_xls_to_dict, convert_from_db, recur_unpack


def error_function(func):
    def _wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except ConnectionError as error:
            return JsonResponse({'error': "Server Error {}".format(error)}, status=404)
        except WindowsError as error:
            return JsonResponse({'error': "Server Error {}".format(error)}, status=404)
        except Exception as error:
            return JsonResponse({'error': 'some new error. {}'.format(error)}, status=404)
        return result
    return _wrapper

def prepare_request(func):
    def _wrapper(self, request):
        parameters = {}
        rct = request.POST if request.method == 'POST' else request.GET
        table_name = rct.get('table_name', None)
        for k, v in rct.dict().items():
            if v and k not in ('_method', 'save_in_file', 'file_type', 'table_name') and v != '---Select_table---':
                if rct['_method'] in ('post', 'put') or re.search(r"^[=><]{1,2}[ ]\w+", v):
                    parameters[k] = v
                else:
                    parameters[k] = ['== ' + v]
                    print(parameters[k])
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        result = func(self, request, table_name, url, parameters)
        return result
    return _wrapper




def simple_view(request, template, *args, **kwargs):
    param = kwargs if kwargs else {}
    param['catalogs'] = CONFIG['WORK_TYPE']
    return render(request, template, param)


class BaseInteract(View):
    '''
    class with get, post, put and delete method for db interaction
    '''
    http_method_names = ['get', 'post', 'put', 'delete']

    def dispatch(self, request, *args, **kwargs):
        method = self.request.POST.get('_method', '').lower()
        if method == 'put':
            return self.put(request, *args, **kwargs)
        if method == 'delete':
            return self.delete(request, *args, **kwargs)
        return super(BaseInteract, self).dispatch(request, *args, **kwargs)

    # @error_function
    @prepare_request
    def get(self, request, table_name=None, url=None, parameters=None):
        file_format = request.GET.dict().get('file_type')
        print(parameters)
        form = BaseDynamicForm(request.GET, {"static_fields": parameters})
        # print(request.POST)
        if not form.is_valid():
            return render(request, 'table_form.html', {'form': form.as_table()})
        parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
        response = requests.get(url, params=parameters)  # , timeout=4)
        if response.status_code == 200:
            # print(response.json())
            out_file, html_table = convert_from_db(json_data=response.json()['parameters'],
                                                   file_format=file_format,
                                                   table_name=table_name)
            file_url = f"file_save?file={out_file.upload.url}" if out_file else None
            data = {'form': form.as_table(), 'messages': 'Тестируем', "html": html_table,
                    "load_to_file": file_url}
            return JsonResponse(data, status=200)
        elif response.status_code in (502, 422):
            return JsonResponse({'error': "Error #{} \n{}".format(response.status_code, response.text),
                                 'form': form.as_table()}, status=response.status_code)
        else:
            return JsonResponse({'error': f'Server return status {response.status_code}', 'form': form.as_table()}, status=404)

    @error_function
    @prepare_request
    def post(self, request, table_name=None, url=None, parameters=None):
        # print(request.POST.dict())
        # parameters = {k: v for k, v in request.POST.dict().items() if v and k != '_method'}
        # url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        # table_name = parameters.pop('table_name')
        # print(parameters)
        if 'excel_selection' in parameters:
            dct = from_xls_to_dict(request.FILES['upload'], CONFIG['DATA_BASE'][table_name]['ref_fields'])
            print('size of json attached: ', sys.getsizeof(json.dumps(dct)))
            parameters = {'table_name': CONFIG['DATA_BASE'][table_name]['name_db']}
            response = requests.post(url, params=parameters, data=json.dumps({"parameters": dct}),
                                     headers={'Content-Type': 'application/json'})  # , timeout=4)
        else:
            form = BaseDynamicForm(request.POST, {"static_fields": parameters, 'validate': False})
            if not form.is_valid():
                return render(request, 'table_form.html', {'form': form})
            parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
            response = requests.post(url, params=parameters)
        # url = "https://46bda8ba-446a-4aa1-b765-00c57f94efe3.mock.pstmn.io" + '/db'
        # print(response.status_code, response.text)
        if response.status_code == 200:
            data = {'messages': f'Тестируем. {response.text}'}
            return JsonResponse(data)
        elif response.status_code in (502, 422):
            return JsonResponse({'error': "Error #{} \n{}".format(response.status_code, response.text)}
                                , status=response.status_code)
        else:
            return JsonResponse({'error': 'Server return status not 200'}, status=404)

    @error_function
    @prepare_request
    def delete(self, request, table_name=None, url=None, parameters=None):
        # print(request.POST)
        # parameters = {k: v for k, v in request.POST.dict().items() if v and k != '_method'}
        # url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        # table_name = parameters.pop('table_name')
        # print(parameters)
        if 'excel_selection' in parameters:
            # print(request.FILES, '\n', CONFIG['DATA_BASE'][table_name]['ref_fields'])
            dct = from_xls_to_dict(request.FILES['upload'], CONFIG['DATA_BASE'][table_name]['ref_fields'], ['uid'])
            print('size of json attached: ', sys.getsizeof(json.dumps(dct)))
            parameters = {'table_name': CONFIG['DATA_BASE'][table_name]['name_db']}
            # print(parameters)
            response = requests.delete(url, params=parameters, data=json.dumps({"parameters": dct}),
                                       headers={'Content-Type': 'application/json'})
        else:
            form = BaseDynamicForm(request.POST, {"static_fields": parameters})
            if not form.is_valid():
                return render(request, 'table_form.html', {'form': form})
            parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
            # print(parameters)
            response = requests.delete(url, params=parameters)
        if response.status_code == 200:
            data = {'messages': f'Тестируем. {response.text}'}
            return JsonResponse(data)
        elif response.status_code in (502, 422):
            return JsonResponse({'error': "Error #{} \n{}".format(response.status_code, response.text)}
                                , status=response.status_code)
        else:
            return JsonResponse({'error': 'Server return status not 200'}, status=404)

    @error_function
    @prepare_request
    def put(self, request, table_name=None, url=None, parameters=None):
        # print('Put request: ', request.POST)
        # parameters = {k: v for k, v in request.POST.dict().items() if v and k != '_method'}
        # url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        # table_name = parameters.pop('table_name')
        # print(parameters)
        if 'excel_selection' in parameters:
            dct = from_xls_to_dict(request.FILES['upload'], False)
            print('size of json attached: ', sys.getsizeof(json.dumps(dct)))
            parameters = {'table_name': CONFIG['DATA_BASE'][table_name]['name_db']}
            # print(parameters)
            response = requests.put(url, params=parameters, data=json.dumps({"parameters": dct}),
                                    headers={'Content-Type': 'application/json'})
        else:
            form = BaseDynamicForm(request.POST, {"static_fields": parameters, 'validate': False})
            if not form.is_valid():
                return render(request, 'table_form.html', {'form': form})
            parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
            # print(parameters)
            response = requests.put(url, params=parameters)
        if response.status_code == 200:
            data = {'messages': f'Тестируем. {response.text}'}
            return JsonResponse(data)
        elif response.status_code in (502, 422):
            return JsonResponse({'error': "Error #{} \n{}".format(response.status_code, response.text)},
                                status=response.status_code)
        else:
            return JsonResponse({'error': 'Server return status not 200'}, status=404)


def file_save_view(request, template, *args, **kwargs):
    '''
    file save view for ajax request (button with download file)
    '''
    file_url = request.GET['file'] if request.GET['file'] else '#'
    return render(request, template, {'file_url': file_url})


# def ajax_get_fields(request, *args, **kwargs):
#     '''
#     ajax rendering view for additional fields which depends on selected table or another input options
#     '''
#     param = request.GET.dict()
#     table_name = param.pop('table_name')
#     if 'excel_selection' not in param:
#         if table_name in CONFIG['DATA_BASE']:
#             table_fields = CONFIG['DATA_BASE'][table_name]['fields']
#             param['form'] = BaseDynamicForm({"dynamic_fields": table_fields}).as_table()
#         elif table_name in CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['SECTION-TYPE']:
#             table_fields = CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['SECTION-TYPE'][table_name]['Parameters'] +\
#                            CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['STANDARD-PART']['Parameters']
#             if table_name == "FEM-Polygon":
#                 number = int(param.pop('points'))
#                 table_fields = [(f'y_{idx}', f'z_{idx}') for idx in range(number)]
#                 table_fields = recur_unpack(table_fields)
#             param['form'] = BaseDynamicForm({"dynamic_fields": table_fields, "type_fields": 'float'}).as_table()
#     elif param['excel_selection'] == 'on':
#         param['excel_selection'] = True
#         param['form'] = UploadForm
#         param['template'] = CONFIG['DATA_BASE'][table_name].get('template', None) if table_name in CONFIG['DATA_BASE'] else None
#     if 'save_in_file' in param and param['save_in_file'] == 'on' and 'file_type' in CONFIG['DATA_BASE'][table_name]:
#         param['save_file_form'] = CONFIG['DATA_BASE'][table_name]['file_type'].keys()
#     return render(request, 'table_form.html', param)




class AjaxFields(View):
    def get(self, request):
        param = request.GET.dict()
        param = self.chain(request, param)
        return render(request, 'table_form.html', param)

    def chain(self, request, param):
        table_name = param.get('table_name')
        if not table_name:
            return param
        else:
            # two rows without excel selection and with excel selection
            *args, param = self.save_in_file(*self.cs_input(*self.static_fields(*self.dynamic_fields(
                *self.add_dynamic_fields(request, table_name, param))))) if 'excel_selection' not in param else \
                self.save_in_file(*self.excel_input(request, table_name, param))
        return param

    def dynamic_fields(self, request, table_name, param):
        if table_name in CONFIG['DATA_BASE'] and 'dynamic_fields' in CONFIG['DATA_BASE'][table_name]:
            # table_fields = CONFIG['DATA_BASE'][table_name]['dynamic_fields']
            param['dynamic_fields'] = CONFIG['DATA_BASE'][table_name]['dynamic_fields']
        return request, table_name, param

    def add_dynamic_fields(self, request, table_name, param):
        if table_name == 'add_dynamic_field':
            static_param = [val for key, val in param.items() if key.startswith('st_par_')]
            param['form'] = BaseDynamicForm({"static_fields": static_param}).as_table()
        return request, table_name, param

    def static_fields(self, request, table_name, param):
        if table_name in CONFIG['DATA_BASE'] and 'fields' in CONFIG['DATA_BASE'][table_name]:
            table_fields = CONFIG['DATA_BASE'][table_name]['fields']
            param['form'] = BaseDynamicForm({"static_fields": table_fields}).as_table()
            # print(param['form'])
        return request, table_name, param

    def cs_input(self, request, table_name, param):
        if table_name in CONFIG['DATA_BASE']['Sections']['dynamic_fields']['type']:
            table_fields = CONFIG['DATA_BASE']['Sections']['dynamic_fields']['type'][table_name] + \
                           CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['STANDARD-PART']['Parameters']
            if table_name == "FEM-Polygon":
                number = int(param.pop('points'))
                table_fields = [(f'y_{idx}', f'z_{idx}') for idx in range(number)]
                table_fields = recur_unpack(table_fields)
            param['form'] = BaseDynamicForm({"static_fields": table_fields, "type_fields": 'float'}).as_table()
        return request, table_name, param

    def excel_input(self, request, table_name, param):
        if param.get('excel_selection') == 'on':
            param['excel_selection'] = True
            param['form'] = UploadForm
            param['template'] = CONFIG['DATA_BASE'][table_name].get('template') if table_name in CONFIG['DATA_BASE'] \
                else None
        return request, table_name, param

    def save_in_file(self, request, table_name, param):
        if param.get('save_in_file') == 'on' and 'file_type' in CONFIG['DATA_BASE'][table_name]:
            param['save_file_form'] = CONFIG['DATA_BASE'][table_name]['file_type'].keys()
        return request, table_name, param
