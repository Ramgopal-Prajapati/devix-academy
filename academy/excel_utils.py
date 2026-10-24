import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from io import BytesIO
import calendar
from datetime import date
from attendance.models import Attendance


def _apply_header_style(cell, text, bg_color="1E293B", text_color="FFFFFF", font_size=10, bold=True):
    cell.value = text
    cell.font = Font(name="Segoe UI", size=font_size, bold=bold, color=text_color)
    cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _thin_border():
    thin = Side(border_style="thin", color="CBD5E1")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def export_students_detail_excel_response(students_qs, filename="DeviX_Students_Detail.xlsx"):
    """
    Exports comprehensive directory of students to a beautifully styled Excel workbook (.xlsx).
    Includes contact, course, trainer, attendance analytics, and certificate eligibility.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students Directory"
    ws.views.sheetView[0].showGridLines = True

    # 1. Title Banner
    ws.merge_cells("A1:V1")
    title_cell = ws["A1"]
    title_cell.value = "DeviX Academy — Students Master Directory"
    title_cell.font = Font(name="Segoe UI", size=15, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1E1B4B", end_color="1E1B4B", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # 2. Metadata Subtitle
    ws.merge_cells("A2:V2")
    sub_cell = ws["A2"]
    today_str = date.today().strftime("%d %B %Y")
    total_count = students_qs.count()
    sub_cell.value = f"Generated on: {today_str} | Total Enrolled Students: {total_count} | Authorized Institute Management Suite"
    sub_cell.font = Font(name="Segoe UI", size=9, italic=True, color="475569")
    sub_cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # 3. Column Headers
    headers = [
        "S.No",
        "Student ID",
        "Student Name",
        "Email Address",
        "Phone Number",
        "Department",
        "Enrolled Course",
        "Assigned Trainer",
        "Course Duration",
        "Class / Batch",
        "Start Date",
        "End Date",
        "Total Sessions",
        "Present Days",
        "Leave Days",
        "Absent Days",
        "Attendance %",
        "Certificate Eligibility",
        "Status",
        "LinkedIn",
        "GitHub",
        "Registration Date"
    ]

    header_row_idx = 4
    ws.row_dimensions[header_row_idx].height = 26

    for col_idx, text in enumerate(headers, 1):
        cell = ws.cell(row=header_row_idx, column=col_idx)
        _apply_header_style(cell, text, bg_color="2563EB", text_color="FFFFFF", font_size=10, bold=True)
        cell.border = _thin_border()

    # 4. Data Rows
    row_idx = 5
    border = _thin_border()
    zebra_even = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    zebra_odd = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    for idx, student in enumerate(students_qs.select_related('user', 'department', 'course', 'trainer', 'trainer__user'), 1):
        stats = student.get_attendance_stats()
        fill = zebra_odd if idx % 2 == 1 else zebra_even
        ws.row_dimensions[row_idx].height = 22

        row_data = [
            idx,
            student.student_id,
            student.name,
            student.email,
            student.phone,
            student.department.name if student.department else "N/A",
            student.course.name if student.course else "Unassigned",
            student.trainer.full_name if student.trainer else "Unassigned",
            student.course_duration or (student.course.duration if student.course else "N/A"),
            student.student_class or "General",
            student.start_date.strftime("%d-%m-%Y") if student.start_date else "N/A",
            student.end_date.strftime("%d-%m-%Y") if student.end_date else "Ongoing",
            stats['total'],
            stats['present'],
            stats.get('leave', 0),
            stats['absent'],
            f"{stats['percentage']}%",
            "Eligible (>=75%)" if stats['is_eligible'] else "Ineligible (<75%)",
            "Active" if student.is_active else "Inactive",
            student.linkedin or "—",
            student.github or "—",
            student.created_at.strftime("%d-%m-%Y") if student.created_at else "N/A"
        ]

        for col_idx, val in enumerate(row_data, 1):
            c = ws.cell(row=row_idx, column=col_idx, value=val)
            c.font = Font(name="Segoe UI", size=9)
            c.border = border
            c.fill = fill

            # Center alignment for IDs, dates, numbers, and stats
            if col_idx in [1, 2, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

            # Conditional Highlights
            if col_idx == 17:  # Attendance %
                pct = stats['percentage']
                if pct >= 75.0:
                    c.font = Font(name="Segoe UI", size=9, bold=True, color="166534")
                else:
                    c.font = Font(name="Segoe UI", size=9, bold=True, color="991B1B")
            elif col_idx == 18:  # Eligibility
                if stats['is_eligible']:
                    c.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
                    c.font = Font(name="Segoe UI", size=9, bold=True, color="166534")
                else:
                    c.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    c.font = Font(name="Segoe UI", size=9, bold=True, color="991B1B")

        row_idx += 1

    # 5. Auto-fit column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            # Skip title merged row
            if cell.row in [1, 2]:
                continue
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 11)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def export_monthly_student_attendance_excel_response(students_qs, year, month, filename=None):
    """
    Exports a detailed day-by-day month-wise Student Attendance Matrix to Excel (.xlsx).
    Shows daily status (P, L, A, SUN), monthly totals, and eligibility calculations.
    """
    if not filename:
        filename = f"DeviX_Student_Attendance_{year}_{month:02d}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    month_name = calendar.month_name[month]
    ws.title = f"{month_name[:3]} {year} Attendance"
    ws.views.sheetView[0].showGridLines = True

    # Calculate days in selected month
    num_days = calendar.monthrange(year, month)[1]
    days_list = [date(year, month, d) for d in range(1, num_days + 1)]
    today = date.today()

    total_cols = 4 + num_days + 5  # Base info + days + totals

    # 1. Main Banner
    last_col_letter = get_column_letter(total_cols)
    ws.merge_cells(f"A1:{last_col_letter}1")
    title_cell = ws["A1"]
    title_cell.value = f"DeviX Academy — Student Monthly Attendance Matrix: {month_name} {year}"
    title_cell.font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1E1B4B", end_color="1E1B4B", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # 2. Subtitle / Legend
    ws.merge_cells(f"A2:{last_col_letter}2")
    sub_cell = ws["A2"]
    sub_cell.value = "Legend: [P] Present (Green) | [L] Approved Leave (Orange) | [A] Absent (Red) | [SUN] Sunday / Weekend | Eligibility Threshold: 75%"
    sub_cell.font = Font(name="Segoe UI", size=9, bold=True, color="334155")
    sub_cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # 3. Header Rows (Row 4)
    ws.row_dimensions[4].height = 28
    base_headers = ["S.No", "Student ID", "Student Name", "Course"]
    for i, h in enumerate(base_headers, 1):
        cell = ws.cell(row=4, column=i)
        _apply_header_style(cell, h, bg_color="334155", font_size=9)
        cell.border = _thin_border()

    # Day columns (1 .. num_days)
    day_col_start = 5
    for i, d in enumerate(days_list):
        col_idx = day_col_start + i
        cell = ws.cell(row=4, column=col_idx)
        day_str = f"{d.day}\n{d.strftime('%a')[:2]}"
        is_sun = d.weekday() == 6
        bg = "475569" if not is_sun else "94A3B8"
        _apply_header_style(cell, day_str, bg_color=bg, font_size=8)
        cell.border = _thin_border()
        ws.column_dimensions[get_column_letter(col_idx)].width = 5.0

    # Summary Totals Headers
    totals_headers = ["Present (P)", "Leave (L)", "Absent (A)", "Total Days", "Att %", "Eligibility"]
    totals_start = day_col_start + num_days
    for i, h in enumerate(totals_headers):
        col_idx = totals_start + i
        cell = ws.cell(row=4, column=col_idx)
        _apply_header_style(cell, h, bg_color="1E3A8A", font_size=9)
        cell.border = _thin_border()

    # 4. Fill Student Rows
    border = _thin_border()
    p_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # soft green
    p_font = Font(name="Segoe UI", size=8, bold=True, color="166534")

    l_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # soft yellow/amber
    l_font = Font(name="Segoe UI", size=8, bold=True, color="B45309")

    a_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid") # soft red
    a_font = Font(name="Segoe UI", size=8, bold=True, color="B91C1C")

    sun_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    sun_font = Font(name="Segoe UI", size=8, color="94A3B8")

    row_idx = 5
    for idx, student in enumerate(students_qs.select_related('course', 'trainer'), 1):
        ws.row_dimensions[row_idx].height = 20
        # Base info
        ws.cell(row=row_idx, column=1, value=idx).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=row_idx, column=2, value=student.student_id).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=row_idx, column=3, value=student.name).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=row_idx, column=4, value=student.course.name if student.course else "Unassigned").alignment = Alignment(horizontal="left", vertical="center")

        for c_idx in range(1, 5):
            ws.cell(row=row_idx, column=c_idx).border = border
            ws.cell(row=row_idx, column=c_idx).font = Font(name="Segoe UI", size=9)

        # Fetch attendance for this month
        month_records = Attendance.objects.filter(
            student=student,
            date__year=year,
            date__month=month
        )
        att_map = {att.date.day: att.status for att in month_records}

        p_count = 0
        l_count = 0
        a_count = 0

        for i, d in enumerate(days_list):
            col_idx = day_col_start + i
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = border
            cell.alignment = Alignment(horizontal="center", vertical="center")

            if d.weekday() == 6:  # Sunday
                cell.value = "SUN"
                cell.fill = sun_fill
                cell.font = sun_font
            else:
                st = att_map.get(d.day)
                if st == 'Present':
                    cell.value = "P"
                    cell.fill = p_fill
                    cell.font = p_font
                    p_count += 1
                elif st == 'Leave':
                    cell.value = "L"
                    cell.fill = l_fill
                    cell.font = l_font
                    l_count += 1
                elif st == 'Absent':
                    cell.value = "A"
                    cell.fill = a_fill
                    cell.font = a_font
                    a_count += 1
                else:
                    # Not marked or past/future
                    if d <= today and d.weekday() < 5:
                        cell.value = "—"
                    else:
                        cell.value = ""
                    cell.font = Font(name="Segoe UI", size=8, color="CBD5E1")

        # Summary columns
        total_sessions = p_count + l_count + a_count
        pct = round((p_count / total_sessions * 100), 1) if total_sessions > 0 else 0.0
        is_eligible = pct >= 75.0

        summary_values = [
            (p_count, "166534"),
            (l_count, "B45309"),
            (a_count, "B91C1C"),
            (total_sessions, "1E293B"),
            (f"{pct}%", "166534" if is_eligible else "B91C1C"),
            ("Eligible" if is_eligible else "Ineligible", "166534" if is_eligible else "B91C1C")
        ]

        for i, (val, color_hex) in enumerate(summary_values):
            col_idx = totals_start + i
            c = ws.cell(row=row_idx, column=col_idx, value=val)
            c.border = border
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.font = Font(name="Segoe UI", size=9, bold=True, color=color_hex)
            if i == 5:
                c.fill = PatternFill(start_color="DCFCE7" if is_eligible else "FEE2E2", fill_type="solid")

        row_idx += 1

    # Adjust widths of base columns
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 24
    ws.column_dimensions["D"].width = 28
    for i in range(len(totals_headers)):
        col_letter = get_column_letter(totals_start + i)
        ws.column_dimensions[col_letter].width = 13

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
