import datetime
import re
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


# @error_function
def convert_from_db(json_data: dict, file_format: str, table_name: str, easy_format=False) -> (QuerySet[Upload], pd.DataFrame.to_html):
    # print(json_data)
    df = pd.DataFrame(data=json_data)
    if 'position' in df.columns:
        df_add = df.apply(lambda row: row.position['parameter'], axis=1).apply(pd.Series)
        df = pd.concat([df, df_add], axis=1).drop('position', axis=1)
    if file_format == 'excel':
        filename = convert_to_xlsx(df, table_name, easy_format)
    elif file_format == 'bdf':
        filename = convert_to_bdf(df, table_name)
    else:
        return None, df.to_html(justify='left')
    db_file = Upload.objects.create(upload=filename)
    file_out = Upload.objects.get(id=db_file.id)
    return file_out, df.to_html(justify='left')


# @error_function
def convert_to_bdf(df: pd.DataFrame, table_name: str) -> str:
    """
     function taken DataFrame and convert it in bdf format according to config yaml
     """
    filename = f'{table_name}.bdf'
    _bdf_lst = list(CONFIG['DATA_BASE'][table_name]['file_type']['bdf'].keys())
    # select column which are in DB
    _db_col_lst = [_name for _name in _bdf_lst if _name in df.columns]
    df_to_bdf = df[_db_col_lst]
    #TODO: split df by element_type and remove empty columns

    # add columns which are not presented in DB
    [df_to_bdf.insert(idx, _name, CONFIG['DATA_BASE'][table_name]['file_type']['bdf'][_name])
     for idx, _name in enumerate(_bdf_lst) if _name not in _db_col_lst]
    # save to bdf file
    print(df_to_bdf)
    type_column = [_name for _name in df_to_bdf.columns if _name.endswith('_type')]
    with open(fr'media/{filename}', 'w') as csv_file:
        csv_file.write(f'#file created at {datetime.datetime.now()} \n')
    if len(type_column) > 0:
        for _type, df_to_bdf_group in df_to_bdf.groupby(type_column[0]):
            df_to_bdf_group.dropna(axis=1, how='all', inplace=True)
            for drop_col in df_to_bdf_group.columns:
                df_to_bdf_group[drop_col] = df_to_bdf_group[drop_col].astype(str).apply(lambda x: re.sub(r'\.0$', '', x))
            df_to_bdf_group.to_csv(fr'media/{filename}', header=None, index=None, sep=",", mode='a')
    else:
        df_to_bdf.to_csv(fr'media/{filename}', header=None, index=None, sep=",", mode='a')
    return filename


@error_function
def convert_to_xlsx(df: pd.DataFrame, table_name: str, easy_format: bool) -> str:
    filename = f'{table_name}.xlsx'
    with pd.ExcelWriter(f'media/{filename}') as tmp:
        df.dropna(axis=1, how='all', inplace=True)
        if False not in [field in df.columns for field in ['frame', 'stringer', 'side']] and not easy_format:
            for _key in df.columns:
                if _key not in ['frame', 'stringer', 'side']:
                    df.pivot(columns=['frame'], index=['stringer', 'side'], values=_key).\
                        to_excel(excel_writer=tmp, sheet_name=_key)
        else:
            df.to_excel(excel_writer=tmp)
    return filename


@error_function
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


def cs_converter(db_cs_lst: list) -> list:
    """
    db_cs_lst: cross-section parameters list ([{'side': 'LHS', 'stringer': 1, 'frame': 10, 'uid': '11010110', 'type':
    'Stringer', 'section_type': 'L-Section', 'height': '40', 'th_1': '4.2', 'width': '30', 'th_2': '2.5', 'alpha':
    '0', 'coord_x': '150', 'coord_y': '45', 'coord_z': '55.1', 'comment': 'Stringer test'},])
    """
    sections = []
    for item in db_cs_lst:
        section_config = CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['SECTION-TYPE'][item['section_type']]
        if db_cs_lst[0]['section_type'] == 'FEM-Polygon':
            _points_number = int(db_cs_lst[0].pop('points'))
            dct = [(db_cs_lst[0].pop(f'x_{idx}'), db_cs_lst[0].pop(f'y_{idx}')) for idx in range(_points_number)]
        else:
            dct = {k: float(item.pop(k)) for k in list(item.keys()) if k in section_config['Parameters'] or
                   k in CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['STANDARD-PART']['Parameters']}

            #TODO: update div_x, y, z in line with business logic
            for arg in ('div_x', 'div_y'):
                dct[arg] = 0
        print(dct)
        section = globals()[section_config['Class_name']](dct)
        item.update(section.output)
        sections.append(item)
    picture = None if len(db_cs_lst) > 1 else section.plot
    return sections, picture


def recur_unpack(lst: list, return_lst=None) -> list:
    # prepare list with unpacked internal lists [[1,2,3],4,[[5,6],7]] --> [1,2,3,4,5,6,7]
    return_lst = list() if not return_lst else return_lst
    for _val in lst:
        if type(_val) == list or type(_val) == tuple:
            return_lst = recur_unpack(_val, return_lst)
        else:
            return_lst.append(_val)
    return return_lst