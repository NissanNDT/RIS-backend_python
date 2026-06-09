import os
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from io import BytesIO
import openpyxl
from openpyxl.styles import PatternFill
from config.db import db_pool

router = APIRouter()

@router.get("/excel/{id_incident}")
def generate_excel(id_incident: int):
    # Fetch incident
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incident WHERE id = %s", [id_incident])
            incident = cur.fetchone()
            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")
            
            # Fetch incident format
            cur.execute("SELECT * FROM incident_format WHERE id_incident = %s", [id_incident])
            format_data = cur.fetchone()
            
            format_id = format_data["id"] if format_data else None
            
            # Fetch related details if format exists
            factors = []
            countermeasures = []
            participants = []
            hazard_background = None
            intervening_factors = []
            
            if format_id:
                cur.execute("SELECT * FROM factor_tree WHERE id_incident_format = %s", [format_id])
                factors = cur.fetchall()
                
                cur.execute("SELECT * FROM countermeasure_plan WHERE id_incident_format = %s", [format_id])
                countermeasures = cur.fetchall()
                
                cur.execute("SELECT * FROM analysis_participant WHERE id_incident_format = %s", [format_id])
                participants = cur.fetchall()
                
                cur.execute("SELECT * FROM hazard_background WHERE id_incident_format = %s", [format_id])
                hazard_background = cur.fetchone()
                
                cur.execute("SELECT * FROM intervening_factors WHERE id_incident_format = %s", [format_id])
                intervening_factors = cur.fetchall()

            # Get names for plant, area, supervisors
            cur.execute("SELECT name FROM area WHERE id = %s", [incident["id_area"]])
            area = cur.fetchone()
            
            cur.execute("SELECT name FROM plant WHERE id = %s", [incident["id_plant"]])
            plant = cur.fetchone()
            
            cur.execute("SELECT full_name FROM users WHERE id = %s", [incident["id_responsible_user"]])
            resp_user = cur.fetchone()
            
            cur.execute("SELECT full_name FROM users WHERE id = %s", [incident["id_general_sv"]])
            gen_sv = cur.fetchone()
            
            cur.execute("SELECT full_name FROM users WHERE id = %s", [incident["id_junior"]])
            junior = cur.fetchone()
            
            cur.execute("SELECT * FROM cost_center")
            cost_centers = cur.fetchall()
            
            cur.execute("SELECT * FROM control_hierarchy")
            hierarchies = cur.fetchall()
            
            cur.execute("SELECT * FROM verification_method")
            methods = cur.fetchall()

    # Load template
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Anexo 1 Reporte de Incidente.xlsx")
    if not os.path.exists(template_path):
        # Fallback to current working directory
        template_path = "Anexo 1 Reporte de Incidente.xlsx"
        
    try:
        wb = openpyxl.load_workbook(template_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template Excel file not found or corrupted: {str(e)}")
        
    ws = wb["REPORTE"] if "REPORTE" in wb.sheetnames else wb.active

    def set_cell(coord, val):
        from openpyxl.cell.cell import Cell
        cell = ws[coord]
        if isinstance(cell, Cell):
            cell.value = val
        else:
            for r in ws.merged_cells.ranges:
                if coord in r:
                    ws.cell(row=r.min_row, column=r.min_col, value=val)
                    return
            cell.value = val

    # Fill Header
    set_cell("B2", incident["incident_folio"] or "")
    
    # Date formatting
    inc_date = incident["date"]
    if isinstance(inc_date, (datetime, date)):
        set_cell("B3", inc_date.strftime("%Y-%m-%d"))
        set_cell("I17", inc_date.day)
        set_cell("L17", inc_date.month)
        set_cell("O17", inc_date.year)
    else:
        set_cell("B3", str(inc_date) if inc_date else "")

    set_cell("B4", area["name"] if area else "")
    if plant:
        set_cell("F4", plant["name"])
        set_cell("V15", plant["name"])

    # Fills
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    black_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")

    level_str = incident["level"] or ""
    if "G" in level_str: ws["AB4"].fill = red_fill
    if "U" in level_str: ws["AD4"].fill = red_fill
    if "R" in level_str: ws["AF4"].fill = red_fill
    if "FR1" in level_str: ws["AH4"].fill = red_fill
    if "FR0" in level_str: ws["AJ4"].fill = red_fill

    set_cell("G7", incident["incident_mechanism"] or "")
    set_cell("G9", incident["injury"] or "")

    if format_data:
        set_cell("I13", format_data["employee_name"] or "")
        set_cell("AC13", format_data["employee_age"] or "")
        set_cell("AL13", format_data["employee_payroll_number"] or "")
        set_cell("I19", format_data["employee_position"] or "")
        set_cell("X19", format_data["employee_distribution"] or "")
        set_cell("AL17", format_data["employee_seniority"] or "")
        set_cell("AX17", format_data["employee_seniority_in_position"] or "")
        
        if format_data["employee_type"] == "Sindicalizado":
            ws["AT19"].fill = red_fill
        elif format_data["employee_type"] == "No sindicalizado":
            ws["BB19"].fill = red_fill
            
        set_cell("AV13", format_data["accident_shift"] or "")
        set_cell("I23", format_data["sv_seniority"] or "")
        set_cell("AC23", format_data["sv_seniority_in_position"] or "")
        set_cell("AW23", format_data["number_of_staff_under_sv"] or "")
        set_cell("K25", format_data["attending_doctor"] or "")
        set_cell("AG25", format_data["recovery_forecast"] or "")

    if incident["id_cost_center"]:
        cc = next((c for c in cost_centers if c["id"] == incident["id_cost_center"]), None)
        set_cell("I15", cc["name"] if cc else "")

    if incident["time"]:
        set_cell("AB17", incident["time"])

    if resp_user: set_cell("I21", resp_user["full_name"])
    if gen_sv: set_cell("Z21", gen_sv["full_name"])
    if junior: set_cell("AS21", junior["full_name"])

    set_cell("C28", incident["description"] or "")
    set_cell("C55", incident["root_cause"] or "")

    # Hazard Background
    if hazard_background:
        if hazard_background["previous_fr1_incidents_presented"] is True:
            ws["N61"].fill = black_fill
        elif hazard_background["previous_fr1_incidents_presented"] is False:
            ws["D61"].fill = black_fill

        if hazard_background["existing_processes_or_areas_potential_for_incident"] is True:
            ws["N66"].fill = black_fill
            set_cell("W66", hazard_background["processes_or_areas_potential_for_incident"] or "")
        elif hazard_background["existing_processes_or_areas_potential_for_incident"] is False:
            ws["D66"].fill = black_fill

        if hazard_background["horizontal_review"] is True:
            ws["AJ61"].fill = black_fill
            set_cell("AT61", hazard_background["horizontal_review_comment"] or "")
        elif hazard_background["horizontal_review"] is False:
            ws["AO61"].fill = black_fill

        if hazard_background["risk_assessed_and_identified"] is True:
            ws["N71"].fill = black_fill
        elif hazard_background["risk_assessed_and_identified"] is False:
            ws["D71"].fill = black_fill

        if hazard_background["new_risk_assessment_needed"] is True:
            ws["AS71"].fill = black_fill
        elif hazard_background["new_risk_assessment_needed"] is False:
            ws["AI71"].fill = black_fill

        ws["N76"].fill = black_fill  # Taller de limitaciones funcionales default NO

        safety_dojo_date = hazard_background["safety_dojo_reception_date"]
        if safety_dojo_date:
            if isinstance(safety_dojo_date, (datetime, date)):
                set_cell("AB76", safety_dojo_date.strftime("%d/%m/%Y"))
            else:
                set_cell("AB76", str(safety_dojo_date))
        else:
            ws["AW76"].fill = black_fill

        genba_dojo_date = hazard_background["genba_dojo_reception_date"]
        if genba_dojo_date:
            if isinstance(genba_dojo_date, (datetime, date)):
                set_cell("AB77", genba_dojo_date.strftime("%d/%m/%Y"))
            else:
                set_cell("AB77", str(genba_dojo_date))
        else:
            ws["AW77"].fill = black_fill

        negligence = hazard_background["negligence_type"]
        if negligence == "Negligencia consciente":
            ws["V81"].fill = black_fill
        elif negligence == "Negligencia no consciente":
            ws["AD81"].fill = black_fill

        if hazard_background["labor_report"] is True:
            ws["AW81"].fill = black_fill
        elif hazard_background["labor_report"] is False:
            ws["AN81"].fill = black_fill

    # Intervening factors checks
    has_acto = any(f["name"] and "acto" in f["name"].lower() for f in intervening_factors)
    has_condicion = any(f["name"] and ("condicion" in f["name"].lower() or "condición" in f["name"].lower()) for f in intervening_factors)
    if has_acto:
        ws["D81"].fill = black_fill
    if has_condicion:
        ws["L81"].fill = black_fill

    # Intervening factors list (max 5)
    row_idx = 49
    for f in intervening_factors:
        if row_idx <= 53:
            set_cell(f"D{row_idx}", f["name"] or "")
            row_idx += 1

    # Factor tree (max 7)
    factor_row = 36
    for f in factors:
        set_cell(f"C{factor_row}", f.get("4m") or f.get("m4") or "")
        set_cell(f"H{factor_row}", f.get("actual") or "")
        set_cell(f"L{factor_row}", f.get("factor") or "")
        set_cell(f"P{factor_row}", f.get("control_point") or "")
        set_cell(f"T{factor_row}", f.get("standard") or "")
        set_cell(f"V{factor_row}", "SÍ" if f.get("met_standard") in [True, "SÍ", "SI"] else "NO")
        set_cell(f"X{factor_row}", "SÍ" if f.get("met_safety") in [True, "SÍ", "SI"] else "NO")
        set_cell(f"Z{factor_row}", f.get("comments") or "")
        factor_row += 1

    # Countermeasure Plans (starting at Row 87)
    template_capacity = 7
    start_row = 87
    extra_rows = len(countermeasures) - template_capacity if len(countermeasures) > template_capacity else 0

    if extra_rows > 0:
        # Insert blank rows
        ws.insert_rows(start_row + template_capacity, extra_rows)
        # Apply styles and merges to inserted rows
        from copy import copy
        for idx in range(extra_rows):
            r_idx = start_row + template_capacity + idx
            
            # Copy row height
            ws.row_dimensions[r_idx].height = ws.row_dimensions[start_row].height
            
            # Copy cell styles/borders
            for col_idx in range(1, ws.max_column + 1):
                src_cell = ws.cell(row=start_row, column=col_idx)
                dest_cell = ws.cell(row=r_idx, column=col_idx)
                if src_cell.has_style:
                    dest_cell.font = copy(src_cell.font)
                    dest_cell.fill = copy(src_cell.fill)
                    dest_cell.border = copy(src_cell.border)
                    dest_cell.alignment = copy(src_cell.alignment)
                    dest_cell.number_format = src_cell.number_format
                    dest_cell.protection = copy(src_cell.protection)

            # Merge cells for structure
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=3, end_column=13)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=14, end_column=19)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=20, end_column=23)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=24, end_column=28)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=29, end_column=32)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=33, end_column=37)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=38, end_column=41)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=42, end_column=47)
            ws.merge_cells(start_row=r_idx, end_row=r_idx, start_column=52, end_column=55)

    # Populate Countermeasures
    for idx, p in enumerate(countermeasures):
        r_idx = start_row + idx
        set_cell(f"C{r_idx}", p["what"] or "")
        set_cell(f"N{r_idx}", p["why"] or "")
        set_cell(f"T{r_idx}", p["how"] or "")
        set_cell(f"X{r_idx}", p["where_place"] or "")

        plan_when = p["when_date"]
        if plan_when:
            if isinstance(plan_when, (datetime, date)):
                set_cell(f"AC{r_idx}", plan_when.strftime("%d/%m/%Y"))
            else:
                set_cell(f"AC{r_idx}", str(plan_when))

        set_cell(f"AG{r_idx}", p["who"] or "")

        if p["id_control_hierarchy"]:
            hier = next((h for h in hierarchies if h["id"] == p["id_control_hierarchy"]), None)
            set_cell(f"AL{r_idx}", hier["abbreviation"] if hier and "abbreviation" in hier else (hier["name"] if hier else ""))

        if p["id_verification_method"]:
            meth = next((m for m in methods if m["id"] == p["id_verification_method"]), None)
            set_cell(f"AP{r_idx}", meth["name"] if meth else "")

        set_cell(f"AV{r_idx}", "X" if p["ok"] else "" )
        set_cell(f"AX{r_idx}", "X" if p["ng"] else "" )
        set_cell(f"AZ{r_idx}", p["comment"] or p.get("comments") or "")

    # Participants
    shift_amount = extra_rows
    workers = [p for p in participants if p["participant_type"] == 'Participante']
    interested = [p for p in participants if p["participant_type"] == 'Parte interesada pertinente']
    reps = [p for p in participants if p["participant_type"] == 'Representante de los trabajadores']

    # Worker Participants
    r_worker = 101 + shift_amount
    for p in workers:
        set_cell(f"C{r_worker}", p["name"] or "")
        set_cell(f"L{r_worker}", p["department"] or "")
        if p["id_cost_center"]:
            cc = next((c for c in cost_centers if c["id"] == p["id_cost_center"]), None)
            set_cell(f"S{r_worker}", cc["name"] if cc else "")
        r_worker += 1

    # Interested Parties
    r_interested = 101 + shift_amount
    for p in interested:
        set_cell(f"V{r_interested}", p["name"] or "")
        set_cell(f"AD{r_interested}", p["department"] or "")
        if p["id_cost_center"]:
            cc = next((c for c in cost_centers if c["id"] == p["id_cost_center"]), None)
            set_cell(f"AI{r_interested}", cc["name"] if cc else "")
        r_interested += 1

    # Representatives
    r_rep = 101 + shift_amount
    for p in reps:
        set_cell(f"AN{r_rep}", p["name"] or "")
        set_cell(f"AV{r_rep}", p["department"] or "")
        if p["id_cost_center"]:
            cc = next((c for c in cost_centers if c["id"] == p["id_cost_center"]), None)
            set_cell(f"BA{r_rep}", cc["name"] if cc else "")
        r_rep += 1

    # Save to BytesIO
    out = BytesIO()
    wb.save(out)
    out.seek(0)

    # Modify drawings in zip bytes
    zip_bytes = out.getvalue()
    modified_zip_bytes = modify_excel_zip_with_drawings_py(zip_bytes, incident["injury"] or "", factors)
    out_modified = BytesIO(modified_zip_bytes)

    filename = f"reporte_{incident['incident_folio'] or id_incident}.xlsx"
    return StreamingResponse(
        out_modified,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def modify_excel_zip_with_drawings_py(zip_bytes, injury_text, factors):
    import zipfile
    import io

    in_file = io.BytesIO(zip_bytes)
    out_file = io.BytesIO()

    try:
        with zipfile.ZipFile(in_file, 'r') as yin:
            with zipfile.ZipFile(out_file, 'w') as yout:
                for item in yin.infolist():
                    data = yin.read(item.filename)
                    if item.filename == 'xl/drawings/drawing1.xml':
                        xml_str = data.decode('utf-8')
                        modified_xml = modify_drawing_xml_py(xml_str, injury_text, factors)
                        yout.writestr(item.filename, modified_xml.encode('utf-8'))
                    else:
                        yout.writestr(item, data)
        return out_file.getvalue()
    except Exception as e:
        print("Error modifying zip with drawings in Python:", e)
        return zip_bytes

def modify_drawing_xml_py(xml_str, injury_text, factors):
    import re
    # Extract all twoCellAnchor tags
    anchors = re.findall(r'<xdr:twoCellAnchor[\s\S]*?</xdr:twoCellAnchor>', xml_str)
    
    if len(anchors) < 20:
        return xml_str
        
    new_anchors = anchors[:11]
    
    lesion_anchor = anchors[11]
    lesion_anchor = set_shape_text_py(lesion_anchor, injury_text)
    new_anchors.append(lesion_anchor)
    
    template_shapes = {}
    for idx in range(12, 20):
        template_shapes[idx] = anchors[idx]
        
    categories = [
        {"name": "Mano de Obra", "match": ["mano de obra", "mano"], "offset": 0},
        {"name": "Método", "match": ["metodo", "método"], "offset": 2},
        {"name": "Maquinaria", "match": ["maquinaria", "máquinaria"], "offset": 4},
        {"name": "Materiales", "match": ["material", "materiales"], "offset": 6}
    ]
    
    next_id = 100
    for cat in categories:
        factor = None
        for f in factors:
            f_4m = str(f.get("4m") or f.get("m4") or "").lower().strip()
            if any(m in f_4m for m in cat["match"]):
                factor = f
                break
                
        offset = cat["offset"]
        
        # Cat Shape
        cat_shape = template_shapes[12]
        cat_shape = shift_anchor_row_py(cat_shape, offset)
        cat_shape = set_shape_text_py(cat_shape, cat["name"])
        cat_shape = set_shape_id_py(cat_shape, next_id)
        next_id += 1
        new_anchors.append(cat_shape)
        
        # Details
        f_text = factor.get("factor") if factor else ""
        cp_text = factor.get("control_point") if factor else ""
        std_text = factor.get("standard") if factor else ""
        act_text = factor.get("actual") if factor else ""
        comm_text = factor.get("comments") if factor else ""
        
        # Factor
        s_factor = template_shapes[13]
        s_factor = shift_anchor_row_py(s_factor, offset)
        s_factor = set_shape_text_py(s_factor, f_text)
        s_factor = set_shape_id_py(s_factor, next_id)
        next_id += 1
        new_anchors.append(s_factor)
        
        # CP
        s_cp = template_shapes[14]
        s_cp = shift_anchor_row_py(s_cp, offset)
        s_cp = set_shape_text_py(s_cp, cp_text)
        s_cp = set_shape_id_py(s_cp, next_id)
        next_id += 1
        new_anchors.append(s_cp)
        
        # Std
        s_std = template_shapes[15]
        s_std = shift_anchor_row_py(s_std, offset)
        s_std = set_shape_text_py(s_std, std_text)
        s_std = set_shape_id_py(s_std, next_id)
        next_id += 1
        new_anchors.append(s_std)
        
        # Act
        s_act = template_shapes[16]
        s_act = shift_anchor_row_py(s_act, offset)
        s_act = set_shape_text_py(s_act, act_text)
        s_act = set_shape_id_py(s_act, next_id)
        next_id += 1
        new_anchors.append(s_act)
        
        # Comments
        s_comm = template_shapes[19]
        s_comm = shift_anchor_row_py(s_comm, offset)
        s_comm = set_shape_text_py(s_comm, comm_text)
        s_comm = set_shape_id_py(s_comm, next_id)
        next_id += 1
        new_anchors.append(s_comm)
        
        # Judgment
        if factor:
            met_std = factor.get("met_standard") in [True, "SÍ", "SI", "true", 1]
            met_saf = factor.get("met_safety") in [True, "SÍ", "SI", "true", 1]
            
            norma_shape = make_judgment_shape_py(template_shapes, met_std, offset, 40, next_id)
            next_id += 1
            new_anchors.append(norma_shape)
            
            safety_shape = make_judgment_shape_py(template_shapes, met_saf, offset, 43, next_id)
            next_id += 1
            new_anchors.append(safety_shape)
            
    header_idx = xml_str.find("<xdr:twoCellAnchor")
    xml_header = xml_str[:header_idx] if header_idx != -1 else ""
    footer_idx = xml_str.rfind("</xdr:twoCellAnchor>")
    xml_footer = xml_str[footer_idx + len("</xdr:twoCellAnchor>"):] if footer_idx != -1 else "</xdr:wsDr>"
    
    return xml_header + "\n".join(new_anchors) + xml_footer

def shift_anchor_row_py(anchor_str, offset):
    import re
    if offset == 0:
        return anchor_str
    def replace_row(match):
        val = int(match.group(1))
        return f"<xdr:row>{val + offset}</xdr:row>"
    return re.sub(r'<xdr:row>(\d+)</xdr:row>', replace_row, anchor_str)

def set_shape_id_py(anchor_str, new_id):
    import re
    return re.sub(r'<xdr:cNvPr id="(\d+)"', f'<xdr:cNvPr id="{new_id}"', anchor_str)

def set_shape_text_py(anchor_str, text):
    import re
    if "<a:t>" in anchor_str:
        return re.sub(r'<a:t>[\s\S]*?</a:t>', f'<a:t>{text}</a:t>', anchor_str)
    elif text:
        new_run = f'<a:r><a:rPr lang="es-MX" sz="1000"/><a:t>{text}</a:t></a:r>'
        return re.sub(r'<a:p>([\s\S]*?)</a:p>', f'<a:p>{new_run}</a:p>', anchor_str)
    return anchor_str

def make_judgment_shape_py(template_shapes, is_ok, offset, col_start, next_id):
    import re
    tpl_idx = 17 if is_ok else 18
    shape = template_shapes[tpl_idx]
    shape = set_shape_id_py(shape, next_id)
    shape = shift_anchor_row_py(shape, offset)
    
    state = {"count": 0, "from_col_val": 0}
    def replace_col(match):
        state["count"] += 1
        col_val = int(match.group(1))
        if state["count"] == 1:
            state["from_col_val"] = col_val
            return f"<xdr:col>{col_start}</xdr:col>"
        elif state["count"] == 2:
            span = col_val - state["from_col_val"]
            return f"<xdr:col>{col_start + span}</xdr:col>"
        return match.group(0)
        
    return re.sub(r'<xdr:col>(\d+)</xdr:col>', replace_col, shape)
