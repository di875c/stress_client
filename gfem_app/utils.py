import pandas as pd
from .model import Upload

def convert_to_xlsx(json_data):
    with pd.ExcelWriter('media/NamedTemporaryFile.xlsx') as tmp:
        # pd.DataFrame(json_data).to_excel('media/'+tmp.name)
        df = pd.DataFrame(json_data)
        for _key in df.columns:
            if _key not in ['reference_type1', 'reference_number1', 'reference_side1', 'reference_type2',
                            'reference_number2', 'reference_side2']:
                df.pivot(columns=['reference_type1', 'reference_number1'], index=['reference_type2',
                        'reference_number2', 'reference_side2'], values=_key).\
                    to_excel(excel_writer=tmp, sheet_name=_key)
    db_file = Upload.objects.create(title='NamedTemporaryFile.xlsx', upload='NamedTemporaryFile.xlsx')
    excel_file = Upload.objects.get(id=db_file.id)
    return excel_file
