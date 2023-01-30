from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from stress_client.settings import SERVER, CONFIG
import requests
from json2html import *
from .forms import *
from .utils import convert_to_xlsx


def error_function(func):
    def _wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except ConnectionError as error:
            return JsonResponse({'messages': "Server Error {}".format(error)})
        except WindowsError as error:
            return JsonResponse({'messages': "Server Error {}".format(error)})
        except Err:
            return JsonResponse({'messages': 'some new error'})
        return result
    return _wrapper


def simple_view(request, template, *args, **kwargs):
    param = kwargs if kwargs else {}
    param['catalogs'] = CONFIG['WORK_TYPE']
    print(param)
    return render(request, template, param)


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
            # print('form is not valid')
            # print(form)
            return render(request, 'table_form.html', {'form': form})
        parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
        response = requests.get(url, params=parameters)  # , timeout=4)
        if response.status_code == 200:
            # print(response.text)
            html_table = json2html.convert(json=response.json()['parameters'])
            excel_file = convert_to_xlsx(response.json()['parameters'])
            print(excel_file.title, excel_file.upload.url)
            data = {'form': form.as_table(), 'messages': 'Тестируем', "html": html_table,
                    "load_to_file": f"file_save?file={excel_file.upload.url}"}
            return JsonResponse(data)
        elif response.status_code in (502, 422):
            return JsonResponse({'messages': "Error #{} \n{}".format(response.status_code, response.text),
                                 'form': form.as_table()})
        else:
            return JsonResponse({'messages': 'Server return status not 200', 'form': form})

    @error_function
    def post(self, request):
        parameters = {k: v for k, v in request.POST.dict().items() if v and k != 'table_name'}
        # print(parameters)
        table_name = request.POST.dict()['table_name']
        url = 'http://' + ':'.join([SERVER['host'], SERVER['port']]) + '/db'
        # print(url, '\n', parameters)
        form = BaseDynamicForm(request.POST, {"dynamic_fields": parameters})
        # print(request.POST)
        if not form.is_valid():
            # print('form is not valid')
            # print(form)
            return render(request, 'table_form.html', {'form': form})
        parameters['table_name'] = CONFIG['DATA_BASE'][table_name]['name_db']
        response = requests.get(url, params=parameters)  # , timeout=4)
        print(response.status_code, response.text)
        if response.status_code == 200:
            # print(response.text)
            html_table = json2html.convert(json=response.json()['parameters'])
            # print(form)
            data = {'form': form.as_table(), 'messages': 'Тестируем', "html": html_table}
            return JsonResponse(data)
        elif response.status_code in (502, 422):
            return JsonResponse({'messages': "Error #{} \n{}".format(response.status_code, response.text),
                                 'form': form.as_table()})
        else:
            return JsonResponse({'messages': 'Server return status not 200', 'form': form})


class FileSaveInteract(View):
    def get(self, request, template):
        file_url = request.GET['file'] if request.GET['file'] else '#'
        return render(request, template, {'file_url': file_url})

    def post(self, request, template):
        print('ja tut POST', request.POST)
        return render(request, template)


def ajax_get_fields(request, *args, **kwargs):
    table_name = request.GET['table_name']
    table_fields = CONFIG['DATA_BASE'][table_name]['fields']
    # if table_name == 'Structure':
    #     formset = BaseIComForm
    # else:
    formset = BaseDynamicForm({"dynamic_fields": table_fields})
    # print(formset)
    return render(request, 'table_form.html', {'form': formset})
