import pandas as pd
from .model import Upload
from django.db.models.query import QuerySet
import numpy as np


def error_function(func):
    def _wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as error:
            print(f'Excel error {error}')
            raise ValueError(f'Excel error {error}')
    return _wrapper


@error_function
def convert_to_xlsx(json_data: dict) -> QuerySet[Upload]:
    with pd.ExcelWriter('media/NamedTemporaryFile.xlsx') as tmp:
        # pd.DataFrame(json_data).to_excel('media/'+tmp.name)
        df = pd.DataFrame(json_data)
        # Check that reference fields are in the table to convert table view.
        if 'position' in df.columns:
            df_add = df.apply(lambda row: row.position['parameter'], axis=1).apply(pd.Series)
            df = pd.concat([df, df_add], axis=1).drop('position', axis=1)
        df.dropna(axis=1, inplace=True)
        if False not in [field in df.columns for field in ['frame', 'stringer', 'side']]:
            for _key in df.columns:
                if _key not in ['frame', 'stringer', 'side']:
                    df.pivot(columns=['frame'], index=['stringer', 'side'], values=_key).\
                        to_excel(excel_writer=tmp, sheet_name=_key)
        else:
            df.to_excel(excel_writer=tmp)
    db_file = Upload.objects.create(title='NamedTemporaryFile.xlsx', upload='NamedTemporaryFile.xlsx')
    excel_file = Upload.objects.get(id=db_file.id)
    return excel_file, df.to_html(justify='left')


@error_function
def from_xls_to_dict(excel_file: object) -> dict:
    """
   excel_file: Excel file with parameters in each sheet
   return [{'frame': '10', 'stringer': '8', 'side': 'RHS', 'id': 16408200,
   'cog_x': 1450.32602, 'cog_y': -58.5324, 'cog_z: 297.8979, 'comment': 'reference information or comments'}]
   """
    xl = pd.ExcelFile(excel_file)
    sheet_names = xl.sheet_names
    df = {name: xl.parse(name, index_col=[1, 0]) for name in sheet_names if name != 'Readme'}
    parameter_list = []
    for ref1, column in df['id'].items():
        if column.notnull().any():
            for ref2, data in column.items():
                temp_dict = dict(zip(["side", "stringer", "frame"], [*ref2] + [ref1]))
                temp_dict.update({name: str(df[name][ref1][ref2]) for name in sheet_names if name != 'Readme'})
                parameter_list.append(temp_dict)
    # print(parameter_list)
    return parameter_list
