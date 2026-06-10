import xlrd
import openpyxl

print("=== COMPARING ANTECEDENTES DE PELIGRO ===")
wb_xls = xlrd.open_workbook('Reporte de incidente IMEX.xls', formatting_info=True)
ws_xls = wb_xls.sheet_by_index(0)

wb_xlsx = openpyxl.load_workbook('Anexo 1 Reporte de Incidente.xlsx', data_only=True)
ws_xlsx = wb_xlsx.active

# Section starts:
# XLS row 53 corresponds to XLSX row 58
# Let's map XLS row r to XLSX row r + 5
for r_xls in range(52, 77):
    r_xlsx = r_xls + 6 # since 53 mapped to 58 (1-indexed: 53 is 0-indexed 52, 58 is 1-indexed 58)
    # Let's look at cell values in all columns
    print(f"\n--- XLS Row {r_xls+1} vs XLSX Row {r_xlsx} ---")
    for col in range(1, 60):
        val_xls = ws_xls.cell_value(r_xls, col-1) if col-1 < ws_xls.ncols else None
        val_xlsx = ws_xlsx.cell(row=r_xlsx, column=col).value
        if val_xls or val_xlsx:
            print(f"Col {col}: XLS={repr(val_xls)} | XLSX={repr(val_xlsx)}")
