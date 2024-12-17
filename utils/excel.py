from typing import List, Dict, Any
import pandas as pd


def export_to_excel(data: List[dict], filepath: str) -> str:
    df = pd.DataFrame(data)

    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Данные')

        worksheet = writer.sheets['Данные']
        workbook = writer.book

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#E0E0E0',
            'border': 1
        })

        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        number_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '0.00'
        })

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        for row_num in range(len(df)):
            worksheet.write(row_num + 1, 0, df.iloc[row_num, 0], data_format)
            temp_value = df.iloc[row_num, 1]
            if pd.isna(temp_value):
                worksheet.write(row_num + 1, 1, '', data_format)
            else:
                worksheet.write(row_num + 1, 1, temp_value, number_format)

        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 15)

    return filepath


def import_from_excel(filename: str) -> List[Dict[str, Any]]:
    try:
        df = pd.read_excel(filename)

        required_columns = ['Источник', 'Температура']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Неверный формат файла Excel")

        data = []
        for _, row in df.iterrows():
            try:
                temp = float(row['Температура'])
                if -99.99 <= temp <= 99.99:
                    data.append({
                        'src': row['Источник'],
                        'tcw': temp
                    })
            except (ValueError, TypeError):
                continue

        return data
    except Exception as e:
        raise ValueError(f"Ошибка при импорте данных: {str(e)}")
