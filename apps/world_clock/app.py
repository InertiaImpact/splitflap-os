def fetch(settings, format_lines, get_rows, get_cols):
    from datetime import datetime
    import pytz

    def _initials(text):
        parts = [p for p in text.split(' ') if p]
        return ''.join(p[0] for p in parts)

    def _time_candidates(now):
        h12 = now.strftime('%I').lstrip('0') or '12'
        minute = now.strftime('%M')
        ampm = now.strftime('%p')
        ap = ampm[:1]
        h24 = now.strftime('%H')
        return [
            f'{h12}:{minute} {ampm}',
            f'{h12}:{minute}{ampm}',
            f'{h12}:{minute}{ap}',
            f'{h12}{ampm}',
            f'{h12}{ap}',
            f'{h24}:{minute}',
            f'{h24}{minute}',
        ]

    def _format_line(city, tz_abbr, now, cols):
        cols = max(1, int(cols))
        city = city.upper()
        tz_abbr = (tz_abbr or '').upper()
        labels = []
        for label in (city, city.replace(' ', ''), tz_abbr, _initials(city)):
            if label and label not in labels:
                labels.append(label)

        for t in _time_candidates(now):
            if len(t) > cols:
                continue
            budget = cols - len(t)
            if budget <= 0:
                return t
            if budget == 1:
                return t
            max_label = budget - 1
            best = None
            for label in labels:
                if len(label) <= max_label:
                    if best is None or len(label) > len(best):
                        best = label
            if best:
                return f'{best} {t}'
            if max_label > 0:
                return f'{city[:max_label]} {t}'
            return t

        tiny = now.strftime('%H%M')
        return tiny[-cols:]

    zones = [s.strip() for s in settings.get('world_clock_zones', 'US/Eastern,US/Pacific,Europe/London').split(',') if s.strip()]
    rows = max(1, int(get_rows()))
    cols = max(1, int(get_cols()))

    if not zones:
        return [format_lines('NO ZONES')]

    # Rotate visible zones over time so narrow/short displays still cycle all configured clocks.
    cycle_seconds = 6
    start_idx = int(datetime.now().timestamp() // cycle_seconds) % len(zones)

    lines = []
    visible = min(rows, len(zones))
    for row_idx in range(visible):
        z = zones[(start_idx + row_idx) % len(zones)]
        try:
            tz = pytz.timezone(z)
            now = datetime.now(tz)
            city = z.split('/')[-1].replace('_', ' ').upper()
            tz_abbr = now.strftime('%Z')
            lines.append(_format_line(city, tz_abbr, now, cols))
        except Exception:
            lines.append('TZ ERR')

    lines += [''] * (rows - len(lines))
    return [format_lines(*lines)]
