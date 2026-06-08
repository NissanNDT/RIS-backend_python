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

    # Fill Header
    ws["B2"] = incident["incident_folio"] or ""
    
    # Date formatting
    inc_date = incident["date"]
    if isinstance(inc_date, (datetime, date)):
        ws["B3"] = inc_date.strftime("%Y-%m-%d")
        ws["I17"] = inc_date.day
        ws["L17"] = inc_date.month
        ws["O17"] = inc_date.year
    else:
        ws["B3"] = str(inc_date) if inc_date else ""

    ws["B4"] = area["name"] if area else ""
    if plant:
        ws["F4"] = plant["name"]
        ws["V15"] = plant["name"]

    # Fills
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    black_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")

    level_str = incident["level"] or ""
    if "G" in level_str: ws["AB4"].fill = red_fill
    if "U" in level_str: ws["AD4"].fill = red_fill
    if "R" in level_str: ws["AF4"].fill = red_fill
    if "FR1" in level_str: ws["AH4"].fill = red_fill
    if "FR0" in level_str: ws["AJ4"].fill = red_fill

    ws["G7"] = incident["incident_mechanism"] or ""
    ws["G9"] = incident["injury"] or ""

    if format_data:
        ws["I13"] = format_data["employee_name"] or ""
        ws["AC13"] = format_data["employee_age"] or ""
        ws["AL13"] = format_data["employee_payroll_number"] or ""
        ws["I19"] = format_data["employee_position"] or ""
        ws["X19"] = format_data["employee_distribution"] or ""
        ws["AL17"] = format_data["employee_seniority"] or ""
        ws["AX17"] = format_data["employee_seniority_in_position"] or ""
        
        if format_data["employee_type"] == "Sindicalizado":
            ws["AT19"].fill = red_fill
        elif format_data["employee_type"] == "No sindicalizado":
            ws["BB19"].fill = red_fill
            
        ws["AV13"] = format_data["accident_shift"] or ""
        ws["I23"] = format_data["sv_seniority"] or ""
        ws["AC23"] = format_data["sv_seniority_in_position"] or ""
        ws["AW23"] = format_data["number_of_staff_under_sv"] or ""
        ws["K25"] = format_data["attending_doctor"] or ""
        ws["AG25"] = format_data["recovery_forecast"] or ""

    if incident["id_cost_center"]:
        cc = next((c for c in cost_centers if c["id"] == incident["id_cost_center"]), None)
        ws["I15"] = cc["name"] if cc else ""

    if incident["time"]:
        ws["AB17"] = incident["time"]

    if resp_user: ws["I21"] = resp_user["full_name"]
    if gen_sv: ws["Z21"] = gen_sv["full_name"]
    if junior: ws["AS21"] = junior["full_name"]

    ws["C28"] = incident["description"] or ""
    ws["C55"] = incident["root_cause"] or ""

    # Hazard Background
    if hazard_background:
        if hazard_background["previous_fr1_incidents_presented"] is True:
            ws["N61"].fill = black_fill
        elif hazard_background["previous_fr1_incidents_presented"] is False:
            ws["D61"].fill = black_fill

        if hazard_background["existing_processes_or_areas_potential_for_incident"] is True:
            ws["N66"].fill = black_fill
            ws["W66"] = hazard_background["processes_or_areas_potential_for_incident"] or ""
        elif hazard_background["existing_processes_or_areas_potential_for_incident"] is False:
            ws["D66"].fill = black_fill

        if hazard_background["horizontal_review"] is True:
            ws["AJ61"].fill = black_fill
            ws["AT61"] = hazard_background["horizontal_review_comment"] or ""
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
                ws["AB76"] = safety_dojo_date.strftime("%d/%m/%Y")
            else:
                ws["AB76"] = str(safety_dojo_date)
        else:
            ws["AW76"].fill = black_fill

        genba_dojo_date = hazard_background["genba_dojo_reception_date"]
        if genba_dojo_date:
            if isinstance(genba_dojo_date, (datetime, date)):
                ws["AB77"] = genba_dojo_date.strftime("%d/%m/%Y")
            else:
                ws["AB77"] = str(genba_dojo_date)
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
            ws[f"D{row_idx}"] = f["name"] or ""
            row_idx += 1

    # Factor tree (max 7)
    factor_row = 36
    for f in factors:
        ws[f"C{factor_row}"] = f.get("4m") or f.get("m4") or ""
        ws[f"H{factor_row}"] = f.get("actual") or ""
        ws[f"L{factor_row}"] = f.get("factor") or ""
        ws[f"P{factor_row}"] = f.get("control_point") or ""
        ws[f"T{factor_row}"] = f.get("standard") or ""
        ws[f"V{factor_row}"] = "SÍ" if f.get("met_standard") in [True, "SÍ", "SI"] else "NO"
        ws[f"X{factor_row}"] = "SÍ" if f.get("met_safety") in [True, "SÍ", "SI"] else "NO"
        ws[f"Z{factor_row}"] = f.get("comments") or ""
        factor_row += 1

    # Countermeasure Plans (starting at Row 87)
    template_capacity = 7
    start_row = 87
    extra_rows = len(countermeasures) - template_capacity if len(countermeasures) > template_capacity else 0

    if extra_rows > 0:
        # Insert blank rows
        ws.insert_rows(start_row + template_capacity, extra_rows)
        # Apply styles and merges to inserted rows
        for idx in range(extra_rows):
            r_idx = start_row + template_capacity + idx
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
        ws[f"C{r_idx}"] = p["what"] or ""
        ws[f"N{r_idx}"] = p["why"] or ""
        ws[f"T{r_idx}"] = p["how"] or ""
        ws[f"X{r_idx}"] = p["where_place"] or ""

        plan_when = p["when_date"]
        if plan_when:
            if isinstance(plan_when, (datetime, date)):
                ws[f"AC{r_idx}"] = plan_when.strftime("%d/%m/%Y")
            else:
                ws[f"AC{r_idx}"] = str(plan_when)

        ws[f"AG{r_idx}"] = p["who"] or ""

        if p["id_control_hierarchy"]:
            hier = next((h for h in hierarchies if h["id"] == p["id_control_hierarchy"]), None)
            ws[f"AL{r_idx}"] = hier["abbreviation"] if hier and "abbreviation" in hier else (hier["name"] if hier else "")

        if p["id_verification_method"]:
            meth = next((m for m in methods if m["id"] == p["id_verification_method"]), None)
            ws[f"AP{r_idx}"] = meth["name"] if meth else ""

        ws[f"AV{r_idx}"] = "X" if p["ok"] else ""
        ws[f"AX{r_idx}"] = "X" if p["ng"] else ""
        ws[f"AZ{r_idx}"] = p["comment"] or p.get("comments") or ""

    # Participants
    shift_amount = extra_rows
    workers = [p for p in participants if p["participant_type"] == 'Participante']
    interested = [p for p in participants if p["participant_type"] == 'Parte interesada pertinente']
    reps = [p for p in participants if p["participant_type"] == 'Representante de los trabajadores']

    # Worker Participants
    r_worker = 101 + shift_amount
    for p in workers:
        ws[f"C{r_worker}"] = p["name"] or ""
        ws[f"L{r_worker}"] = p["department"] or ""
        if p["id_cost_center"]:
            cc = next((c for c in cost_centers if c["id"] == p["id_cost_center"]), None)
            ws[f"S{r_worker}"] = cc["name"] if cc else ""
        r_worker += 1

    # Interested Parties
    r_interested = 101 + shift_amount
    for p in interested:
        ws[f"V{r_interested}"] = p["name"] or ""
        ws[f"AD{r_interested}"] = p["department"] or ""
        if p["id_cost_center"]:
            cc = next((c for c in cost_centers if c["id"] == p["id_cost_center"]), None)
            ws[f"AI{r_interested}"] = cc["name"] if cc else ""
        r_interested += 1

    # Representatives
    r_rep = 101 + shift_amount
    for p in reps:
        ws[f"AN{r_rep}"] = p["name"] or ""
        ws[f"AV{r_rep}"] = p["department"] or ""
        if p["id_cost_center"]:
            cc = next((c for c in cost_centers if c["id"] == p["id_cost_center"]), None)
            ws[f"BA{r_rep}"] = cc["name"] if cc else ""
        r_rep += 1

    # Save to BytesIO
    out = BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"reporte_{incident['incident_folio'] or id_incident}.xlsx"
    return StreamingResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
