import xlrd

wb = xlrd.open_workbook(r'Reporte de incidente IMEX.xls')
print('Sheets:', wb.sheet_names())
ws = wb.sheet_by_index(0)
print(f'Rows: {ws.nrows}, Cols: {ws.ncols}')

print("\n=== ROWS 55-95 (Arbol de Factores / Antecedentes) ===")
for r in range(54, min(100, ws.nrows)):
    row_data = []
    for c in range(min(30, ws.ncols)):
        v = ws.cell_value(r, c)
        if v:
            row_data.append(f'C{c+1}={repr(v)}')
    if row_data:
        print(f'Row {r+1}: ' + ' | '.join(row_data))

print("\n=== ROWS 30-55 (Factor Tree section) ===")
for r in range(29, 56):
    row_data = []
    for c in range(min(30, ws.ncols)):
        v = ws.cell_value(r, c)
        if v:
            row_data.append(f'C{c+1}={repr(v)}')
    if row_data:
        print(f'Row {r+1}: ' + ' | '.join(row_data))

# Check merge cells
print("\n=== MERGE CELLS (rows 30-95) ===")
for m in ws.merged_cells:
    rlo, rhi, clo, chi = m
    if 29 <= rlo <= 95:
        print(f'Merge: rows {rlo+1}-{rhi} cols {clo+1}-{chi}')
