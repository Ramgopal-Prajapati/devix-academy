import calendar
import datetime


def build_month_calendar_grid(year, month, records_by_day, today=None):
    """
    Builds a structured month calendar grid for visual attendance display.
    records_by_day is a dict mapping day number (int) -> record object or dict with 'status', 'check_in', 'check_out', 'remark'.
    
    Returns:
        dict containing:
            'weeks': list of lists (each week has 7 day dicts)
            'present_count': int
            'half_day_count': int
            'absent_count': int
            'leave_count': int
            'sunday_count': int
    """
    if today is None:
        today = datetime.date.today()

    cal = calendar.Calendar(firstweekday=0)  # Monday = 0, Sunday = 6
    month_days = cal.monthdayscalendar(year, month)

    present_count = 0
    half_day_count = 0
    absent_count = 0
    leave_count = 0
    sunday_count = 0

    weeks = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({
                    'day': '',
                    'is_padding': True,
                    'status': 'Empty',
                    'color_class': 'cal-empty',
                    'badge_bg': 'transparent',
                })
                continue

            day_date = datetime.date(year, month, day)
            is_sunday = (day_date.weekday() == 6)
            is_today = (day_date == today)
            is_future = (day_date > today)

            rec = records_by_day.get(day)
            check_in = None
            check_out = None
            remark = ""

            if rec is not None:
                if hasattr(rec, 'status'):
                    status = rec.status
                    check_in = getattr(rec, 'check_in', None)
                    check_out = getattr(rec, 'check_out', None)
                    remark = getattr(rec, 'remark', '')
                elif isinstance(rec, dict):
                    status = rec.get('status', 'Absent')
                    check_in = rec.get('check_in')
                    check_out = rec.get('check_out')
                    remark = rec.get('remark', '')
                else:
                    status = str(rec)
            else:
                if is_sunday:
                    status = 'Sunday'
                elif is_future:
                    status = 'Future'
                else:
                    # Past weekday with no attendance marked
                    status = 'Absent'

            # Assign styling tokens
            if status == 'Sunday':
                color_class = 'cal-sunday'
                badge_bg = '#64748b'  # Slate Gray
                label = 'Sunday'
                sunday_count += 1
            elif status == 'Present':
                color_class = 'cal-present'
                badge_bg = '#16a34a'  # Green
                label = 'Present'
                present_count += 1
            elif status == 'Half_Day':
                color_class = 'cal-halfday'
                badge_bg = '#d97706'  # Amber/Orange
                label = 'Half Day'
                half_day_count += 1
            elif status == 'Leave':
                color_class = 'cal-leave'
                badge_bg = '#2563eb'  # Blue
                label = 'Leave'
                leave_count += 1
            elif status == 'Absent':
                color_class = 'cal-absent'
                badge_bg = '#dc2626'  # Red
                label = 'Absent'
                absent_count += 1
            else:
                color_class = 'cal-future'
                badge_bg = '#94a3b8'  # Faint
                label = 'Upcoming'

            week_data.append({
                'day': day,
                'date': day_date,
                'is_padding': False,
                'is_sunday': is_sunday,
                'is_today': is_today,
                'is_future': is_future,
                'status': status,
                'label': label,
                'color_class': color_class,
                'badge_bg': badge_bg,
                'check_in': check_in,
                'check_out': check_out,
                'remark': remark,
            })
        weeks.append(week_data)

    return {
        'weeks': weeks,
        'present_count': present_count,
        'half_day_count': half_day_count,
        'absent_count': absent_count,
        'leave_count': leave_count,
        'sunday_count': sunday_count,
        'total_days_in_month': calendar.monthrange(year, month)[1],
    }
