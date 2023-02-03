import json

from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from stress_client.settings import SERVER, CONFIG
import requests, sys
from json2html import *
from .forms import *
from .utils import convert_to_xlsx, from_xls_to_dict


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
    if request.method == 'GET':
        param = kwargs if kwargs else {}
        param['catalogs'] = CONFIG['WORK_TYPE']
        # print(param)
        return render(request, template, param)
    elif request.method == 'POST':
        print('post method work')
        print(request.POST.dict())
        # parameters = {k: v for k, v in request.POST.dict().items() if v and k != 'table_name'}
        # print(parameters)
        # # table_name = request.POST.dict()['table_name']
        # url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        # print(url, '\n', parameters)
        # # print('files: ', request.FILES['excel_file_path'])
        # form = BaseDynamicForm(request.POST, {"dynamic_fields": parameters}) if 'excel_selection' not in parameters \
        #     else UploadForm(request.POST, request.FILES)
        #
        # # print(form)
        data = {'messages': 'Wrong path'}
        return JsonResponse(data, status=200)


class BaseInteract(View):
    @error_function
    def get(self, request):
        parameters = {k: v for k, v in request.GET.dict().items() if v and k != 'table_name'}
        # print(parameters)
        table_name = request.GET.dict()['table_name']
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        # print(url, '\n', parameters)
        form = BaseDynamicForm(request.GET, {"dynamic_fields": parameters})
        # print(request.POST)
        if not form.is_valid():
            return render(request, 'table_form.html', {'form': form})
        parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
        response = requests.get(url, params=parameters)  # , timeout=4)
        if response.status_code == 200:
            print(response.json())
            # html_table = json2html.convert(json=response.json()['parameters'])
            excel_file, html_table = convert_to_xlsx(response.json()['parameters'])
            print(excel_file.title, excel_file.upload.url)
            data = {'form': form.as_table(), 'messages': 'Тестируем', "html": html_table,
                    "load_to_file": f"file_save?file={excel_file.upload.url}"}
            return JsonResponse(data, status=200)
        elif response.status_code in (502, 422):
            return JsonResponse({'error': "Error #{} \n{}".format(response.status_code, response.text),
                                 'form': form.as_table()}, status=response.status_code)
        else:
            return JsonResponse({'error': f'Server return status {response.status_code}', 'form': form}, status=404)

    @error_function
    def post(self, request):
        # print(request.POST.dict())
        parameters = {k: v for k, v in request.POST.dict().items() if v}
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        table_name = parameters.pop('table_name')
        # print(parameters)
        if 'excel_selection' in parameters:
            print(request.FILES)
            form = UploadForm(parameters['title'], request.FILES)
            dct = from_xls_to_dict(request.FILES['upload'])
            print('size of json attached: ', sys.getsizeof(json.dumps(dct)))
        else:
            form = BaseDynamicForm(request.POST, {"dynamic_fields": parameters})
            if not form.is_valid():
                return render(request, 'table_form.html', {'form': form})
        # url = "https://46bda8ba-446a-4aa1-b765-00c57f94efe3.mock.pstmn.io" + '/db'
        parameters = {'table_name': CONFIG['DATA_BASE'][table_name]['name_db']}
        print(parameters)
        response = requests.post(url, params=parameters, data=json.dumps({"parameters": dct}))  # , timeout=4)
        print(response.status_code, response.text)
        if response.status_code == 200:
            data = {'messages': f'Тестируем. {response.text}'}
            return JsonResponse(data)
        elif response.status_code in (502, 422):
            return JsonResponse({'error': "Error #{} \n{}".format(response.status_code, response.text)}
                                , status=response.status_code)
        else:
            return JsonResponse({'error': 'Server return status not 200'}, status=404)


class FileSaveInteract(View):
    def get(self, request, template):
        file_url = request.GET['file'] if request.GET['file'] else '#'
        return render(request, template, {'file_url': file_url})

    def post(self, request, template):
        print('ja tut POST', request.POST)
        return render(request, template)


def ajax_get_fields(request, *args, **kwargs):
    param = request.GET.dict()
    table_name = param.pop('table_name')
    if 'excel_selection' not in param:
        table_fields = CONFIG['DATA_BASE'][table_name]['fields']
        param['form'] = BaseDynamicForm({"dynamic_fields": table_fields}).as_table()
    else:
        param['excel_selection'] = True
        param['form'] = UploadForm.as_table()
    print(param)
    return render(request, 'table_form.html', param)


def ajax_post_fields(request, *args, **kwargs):
    parameters = {k: v for k, v in request.GET.dict().items() if v}
    if 'excel_section' in parameters:
        return
    return
