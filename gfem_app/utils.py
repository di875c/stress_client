import pandas as pd
from .model import Upload
from django.db.models.query import QuerySet
# import numpy as np
from .stress.cs_utils import *
from stress_client.settings import CONFIG


def error_function(func):
    def _wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as error:
            print(f'Excel error {error}')
            raise ValueError(f'Excel error {error}')
    return _wrapper


def convert_from_db(json_data: dict, file_format: str, table_name: str, easy_format=False) -> (QuerySet[Upload], pd.DataFrame.to_html):
    df = pd.DataFrame(json_data)
    if 'position' in df.columns:
        df_add = df.apply(lambda row: row.position['parameter'], axis=1).apply(pd.Series)
        df = pd.concat([df, df_add], axis=1).drop('position', axis=1)
    df.dropna(axis=1, how='all', inplace=True)
    if file_format == 'excel':
        filename = convert_to_xlsx(df, easy_format)
    elif file_format == 'bdf':
        filename = convert_to_bdf(df, table_name)
    else:
        return None, df.to_html(justify='left')
    db_file = Upload.objects.create(upload=filename)
    file_out = Upload.objects.get(id=db_file.id)
    return file_out, df.to_html(justify='left')



def convert_to_bdf(df: pd.DataFrame, table_name) -> str:
    filename = 'NamedTemporaryFile.bdf'

    #TODO: create logic for filling columns which are not presented in database

    # bdf_fields = CONFIG['DATA_BASE'][table_name]['file_type']['bdf']
    # [df.insert(column) for column in bdf_fields if column in bdf_fields


    print('create bdf file')
    df_to_print = df[CONFIG['DATA_BASE'][table_name]['file_type']['bdf']]
    df_to_print.insert(0, 'GRID', 'GRID')
    df_to_print.to_csv(fr'media/{filename}', header=None, index=None, sep=",", mode='w')

    return filename


@error_function
def convert_to_xlsx(json_data: dict, easy_format=False) -> (QuerySet[Upload], pd.DataFrame.to_html):
    with pd.ExcelWriter('media/NamedTemporaryFile.xlsx') as tmp:
        # pd.DataFrame(json_data).to_excel('media/'+tmp.name)
        # print(json_data)
        df = pd.DataFrame(json_data)
        # Check that reference fields are in the table to convert table view.
        if 'position' in df.columns:
            df_add = df.apply(lambda row: row.position['parameter'], axis=1).apply(pd.Series)
            df = pd.concat([df, df_add], axis=1).drop('position', axis=1)
        df.dropna(axis=1, how='all', inplace=True)
        if False not in [field in df.columns for field in ['frame', 'stringer', 'side']] and not easy_format:
            for _key in df.columns:
                if _key not in ['frame', 'stringer', 'side']:
                    df.pivot(columns=['frame'], index=['stringer', 'side'], values=_key).\
                        to_excel(excel_writer=tmp, sheet_name=_key)
        else:
            df.to_excel(excel_writer=tmp)
    db_file = Upload.objects.create(upload='NamedTemporaryFile.xlsx')
    excel_file = Upload.objects.get(id=db_file.id)
    return excel_file, df.to_html(justify='left')


# @error_function
def from_xls_to_dict(excel_file: object, ref_fields: bool, prm_dct=['all']) -> dict:
    """
   excel_file: Excel file with parameters in each sheet
   ref_fields: include ref_fields (frame/stringer position) in result dict
   prm_dict: parameters which have to be included in result dict
   return [{'frame': '10', 'stringer': '8', 'side': 'RHS', 'id': 16408200,
   'cog_x': 1450.32602, 'cog_y': -58.5324, 'cog_z: 297.8979, 'comment': 'reference information or comments'}]
   """
    xl = pd.ExcelFile(excel_file)
    sheet_names = xl.sheet_names
    sheet_names.remove('Readme') if 'Readme' in sheet_names else None
    df = {name: xl.parse(name, index_col=[1, 0]) for name in sheet_names}
    parameter_list = []
    prm_lst = sheet_names if 'all' in prm_dct else prm_dct
    for ref1, column in df[prm_lst[0]].items():
        if column.notnull().any():
            for ref2, data in column.items():
                temp_dict = dict(zip(["side", "stringer", "frame"], [*ref2] + [ref1])) if ref_fields else dict()
                temp_dict.update({name: str(df[name][ref1][ref2]) for name in prm_lst if pd.notna(df[name][ref1][ref2])})
                parameter_list.append(temp_dict)
    # print(parameter_list)
    return parameter_list


def cs_analysis(dct: dict) -> dict:
    # class_name = CONFIG['CALCULATION_TYPE']['CROSS-SECTION'][dct['table_name']]['Class_name']
    class_name = dct.pop('table_name')
    section = globals()[CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['SECTION-TYPE'][class_name]['Class_name']](dct)
    return [{'area': section.area, 'cog': section.cog, 'inertia': section.inertia}]


def cs_converter(db_cs_lst: list) -> list:
    """
    db_cs_lst: cross-section parameters list ([{'side': 'LHS', 'stringer': 1, 'frame': 10, 'uid': '11010110', 'type':
    'Stringer', 'section_type': 'L-Section', 'height': '40', 'th_1': '4.2', 'width': '30', 'th_2': '2.5', 'alpha':
    '0', 'coord_x': '150', 'coord_y': '45', 'coord_z': '55.1', 'comment': 'Stringer test'},])
    """
    sections = []
    for item in db_cs_lst:
        section_config = CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['SECTION-TYPE'][item['section_type']]
        dct = {k: float(item.pop(k)) for k in list(item.keys()) if k in section_config['Parameters'] or
               k in CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['STANDARD-PART']['Parameters']}

        #TODO: update div_x, y, z in line with business logic
        for arg in ('div_x', 'div_y'):
            dct[arg] = 0
        item.update(globals()[section_config['Class_name']](dct).output)
        sections.append(item)
    return sections


