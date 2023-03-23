import json
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
    def get(self, request):
        parameters = {k: v for k, v in request.GET.dict().items() if v and k not in ('table_name', '_method',
                                                                                     'save_in_file', 'file_type')}
        # print(parameters)
        table_name = request.GET.dict()['table_name']
        file_format = request.GET.dict()['file_type'] if 'file_type' in request.GET.dict() else None
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        form = BaseDynamicForm(request.GET, {"dynamic_fields": parameters})
        # print(request.POST)
        if not form.is_valid():
            return render(request, 'table_form.html', {'form': form.as_table()})
        parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
        response = requests.get(url, params=parameters)  # , timeout=4)
        if response.status_code == 200:
            # print(response.json())
            # excel_file, html_table = convert_to_xlsx(response.json()['parameters'])
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
    def post(self, request):
        # print(request.POST.dict())
        parameters = {k: v for k, v in request.POST.dict().items() if v and k != '_method'}
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        table_name = parameters.pop('table_name')
        # print(parameters)
        if 'excel_selection' in parameters:
            dct = from_xls_to_dict(request.FILES['upload'], CONFIG['DATA_BASE'][table_name]['ref_fields'])
            print('size of json attached: ', sys.getsizeof(json.dumps(dct)))
            parameters = {'table_name': CONFIG['DATA_BASE'][table_name]['name_db']}
            response = requests.post(url, params=parameters, data=json.dumps({"parameters": dct}),
                                     headers={'Content-Type': 'application/json'})  # , timeout=4)
        else:
            form = BaseDynamicForm(request.POST, {"dynamic_fields": parameters, 'validate': False})
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
    def delete(self, request):
        # print(request.POST)
        parameters = {k: v for k, v in request.POST.dict().items() if v and k != '_method'}
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        table_name = parameters.pop('table_name')
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
            form = BaseDynamicForm(request.POST, {"dynamic_fields": parameters})
            if not form.is_valid():
                return render(request, 'table_form.html', {'form': form})
            parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
            # print(parameters)
            response = requests.delete(url, params=parameters)
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
    def put(self, request):
        # print('Put request: ', request.POST)
        parameters = {k: v for k, v in request.POST.dict().items() if v and k != '_method'}
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        table_name = parameters.pop('table_name')
        # print(parameters)
        if 'excel_selection' in parameters:
            dct = from_xls_to_dict(request.FILES['upload'], False)
            print('size of json attached: ', sys.getsizeof(json.dumps(dct)))
            parameters = {'table_name': CONFIG['DATA_BASE'][table_name]['name_db']}
            # print(parameters)
            response = requests.put(url, params=parameters, data=json.dumps({"parameters": dct}),
                                    headers={'Content-Type': 'application/json'})
        else:
            form = BaseDynamicForm(request.POST, {"dynamic_fields": parameters, 'validate': False})
            if not form.is_valid():
                return render(request, 'table_form.html', {'form': form})
            parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
            # print(parameters)
            response = requests.put(url, params=parameters)
        # url = "https://46bda8ba-446a-4aa1-b765-00c57f94efe3.mock.pstmn.io" + '/db'
        # print(response.status_code, response.text)
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


def ajax_get_fields(request, *args, **kwargs):
    '''
    ajax rendering view for additional fields which depends on selected table or another input options
    '''
    param = request.GET.dict()
    table_name = param.pop('table_name')
    if 'excel_selection' not in param:
        if table_name in CONFIG['DATA_BASE']:
            table_fields = CONFIG['DATA_BASE'][table_name]['fields']
            param['form'] = BaseDynamicForm({"dynamic_fields": table_fields}).as_table()
        elif table_name in CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['SECTION-TYPE']:
            table_fields = CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['SECTION-TYPE'][table_name]['Parameters'] +\
                           CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['STANDARD-PART']['Parameters']
            if table_name == "FEM-Polygon":
                number = int(param.pop('points'))
                table_fields = [(f'x_{idx}', f'y_{idx}') for idx in range(number)]
                table_fields = recur_unpack(table_fields)
            param['form'] = BaseDynamicForm({"dynamic_fields": table_fields, "type_fields": 'float'}).as_table()
    elif param['excel_selection'] == 'on':
        param['excel_selection'] = True
        param['form'] = UploadForm
    if 'save_in_file' in param and param['save_in_file'] == 'on' and 'file_type' in CONFIG['DATA_BASE'][table_name]:
        param['save_file_form'] = CONFIG['DATA_BASE'][table_name]['file_type'].keys()
    return render(request, 'table_form.html', param)
