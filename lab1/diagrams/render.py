#!/usr/bin/env python3
"""Рисует комплект диаграмм работы 1. Источник правды для картинок — этот файл."""

from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
FONT = "DejaVu Sans"

HEAD = f'''
digraph G {{
  graph [
    fontname="{FONT}",
    bgcolor="white",
    pad="0.45",
    nodesep="0.42",
    ranksep="0.72",
    splines=true,
    outputorder=edgesfirst
  ];
  node [
    fontname="{FONT}",
    fontsize=13,
    shape=box,
    style="rounded,filled",
    color="#1C2B33",
    penwidth=1.4,
    margin="0.16,0.10"
  ];
  edge [
    fontname="{FONT}",
    fontsize=11,
    color="#3D5159",
    penwidth=1.2,
    arrowsize=0.8
  ];
'''

FOOT = "}\n"


def render_dot(name: str, body: str) -> None:
    src = OUT / f"{name}.dot"
    src.write_text(HEAD + body + FOOT, encoding="utf-8")
    for fmt in ("svg", "png"):
        cmd = ["dot", f"-T{fmt}", f"-o{OUT / (name + '.' + fmt)}", str(src)]
        if fmt == "png":
            cmd = ["dot", "-Tpng", "-Gdpi=150", f"-o{OUT / (name + '.png')}", str(src)]
        subprocess.run(cmd, check=True)


def fig_potok() -> None:
    render_dot(
        "01-potok-chteniya",
        f'''
  label="Рис. 1. Путь чтения: толпа остаётся на CDN";
  labelloc=t;
  fontsize=20;
  fontname="{FONT}";
  rankdir=TB;
  newrank=true;

  browser [label="Браузер\\nоболочка один раз, снимок каждые 2 с ± 0,5 с\\nномер очереди считается на клиенте", fillcolor="#F3F4F6"];
  {{ rank=min; browser; }}

  subgraph cluster_read {{
    label="Чтение. Сюда приходят 100 000 запросов/с";
    fontname="{FONT}";
    fontsize=14;
    color="#1F7A6B";
    penwidth=1.5;
    style="rounded";
    bgcolor="#F4FBFA";

    shell [label="CDN: оболочка\\nTTL 10 мин\\nописание, площадка, время", fillcolor="#E5F4F1"];
    snap [label="CDN: снимок\\nTTL 1 с\\nстатус, serving, три счётчика", fillcolor="#E5F4F1"];
    origin [label="Origin оболочки\\nтолько промах, не больше\\nодного запроса на узел", fillcolor="#F7F7F5"];
    redis_snap [label="Redis снимка\\nготовый JSON", fillcolor="#FFF4DE", color="#A15C07"];
    worker [label="Воркер, раз в 200 мс\\nas_of — время реплики", fillcolor="#FFF4DE", color="#A15C07"];
    replica [label="Реплика первичного узла\\nагрегат наличия\\nпродажу не разрешает", fillcolor="#E7EEF8", color="#2451A3"];

    shell -> origin [style=dashed, label="промах"];
    snap -> redis_snap [style=dashed, label="промах\\nпосле схлопывания"];
    worker -> redis_snap [label="публикация"];
    replica -> worker [label="COUNT и SUM"];
  }}

  subgraph cluster_buy {{
    label="Покупка. В базу уходит не больше бюджета холдов";
    fontname="{FONT}";
    fontsize=14;
    color="#B42318";
    penwidth=1.5;
    style="rounded";
    bgcolor="#FDF8F8";

    queue [label="Сервис очереди\\nодин номер на user_id\\nокно 60 с", fillcolor="#F3F4F6"];
    redis_q [label="Redis очереди\\nномер и serving", fillcolor="#FFF4DE", color="#A15C07"];
    token [label="Жетон holds:primary\\nобщий для всех процессов\\nпроверка до BEGIN", fillcolor="#FDECEC", color="#B42318"];
    primary [label="Первичный Postgres\\nfree → held\\nповторная проверка строки", fillcolor="#E7EEF8", color="#2451A3"];

    queue -> redis_q;
    queue -> token [label="холд только\\nесли окно открыто"];
    token -> primary [label="жетон есть"];
  }}

  browser -> shell [label="оболочка"];
  browser -> snap [label="снимок"];
  browser -> queue [label="вход в зал"];
''',
    )


def fig_schema() -> None:
    def table(title: str, rows: list[str], head: str) -> str:
        body = "".join(
            f'<TR><TD ALIGN="LEFT" BGCOLOR="#FFFFFF"><FONT FACE="{FONT}" POINT-SIZE="12">{row}</FONT></TD></TR>'
            for row in rows
        )
        return (
            '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5" COLOR="#1C2B33">'
            f'<TR><TD BGCOLOR="{head}"><FONT FACE="{FONT}" COLOR="white" POINT-SIZE="14"><B>{title}</B></FONT></TD></TR>'
            f"{body}</TABLE>>"
        )

    events = table(
        "events",
        ["sale_status", "on_sale_at", "home_region", "title, venue, starts_at", "description"],
        "#1F3A4D",
    )
    sectors = table("sectors", ["event_id", "title", "kind: numbered | box | ga"], "#1F3A4D")
    units = table(
        "inventory_units",
        [
            "kind, label",
            "row, seat — только место",
            "admits ≥ 1",
            "price_amount",
            "status: free | held | sold",
        ],
        "#2451A3",
    )
    lines = table(
        "order_lines",
        [
            "снимок события и сектора",
            "kind, label, row, seat, admits",
            "price_amount, price_scope",
            "confirmed_text — текст PDF",
        ],
        "#1F7A6B",
    )
    orders = table("orders", ["user_id", "status, idempotency_key", "переходы статуса — работа 2"], "#5C6B73")
    note = table(
        "Ограничение вида",
        [
            "место: ряд, место, admits = 1",
            "ложа: без ряда, admits ≥ 1",
            "входной: без места, admits = 1",
            "пустой label или admits нельзя сохранить",
        ],
        "#7A4E12",
    )
    render_dot(
        "02-sxema-dannyh",
        f'''
  label="Рис. 2. Схема данных: билет печатает снимок, не сектор";
  labelloc=t;
  fontsize=20;
  fontname="{FONT}";
  rankdir=LR;
  node [shape=plain, style="", margin="0"];

  events [label={events}];
  sectors [label={sectors}];
  units [label={units}];
  lines [label={lines}];
  orders [label={orders}];
  note [label={note}];

  events -> sectors [label="1 → N"];
  sectors -> units [label="1 → N\\nвид совпадает"];
  units -> lines [label="снимок\\nв момент холда"];
  orders -> lines [label="1 → N"];
  units -> note [style=dashed, arrowhead=none, color="#A15C07"];
''',
    )


def fig_kinds() -> None:
    render_dot(
        "03-tri-vida",
        f'''
  label="Рис. 3. Три вида единицы и три строки на странице";
  labelloc=t;
  fontsize=20;
  fontname="{FONT}";
  rankdir=LR;

  seat [label="Место\\nnumbered_seat\\nadmits = 1\\nряд и место обязательны\\nцена за кресло", fillcolor="#E7EEF8", color="#2451A3"];
  box [label="Ложа\\nbox\\nadmits ≥ 1\\nряда нет\\nцена за всю ложу", fillcolor="#FFF4DE", color="#A15C07"];
  ga [label="Входной билет\\nga_admission\\nadmits = 1\\nместа нет\\nцена за человека", fillcolor="#E5F4F1", color="#1F7A6B"];

  page [shape=box, label="Страница показывает три строки\\n12 400 нумерованных мест\\n4 ложи, в них 48 гостей\\n3 200 входных билетов", fillcolor="#F7F7F5"];
  banned [label="Общего поля «осталось мест» нет\\n12 400 + 4 + 3 200 = 15 604 — не показываем\\n12 400 + 48 + 3 200 = 15 648 — не показываем", fillcolor="#FDECEC", color="#B42318"];

  seat -> page;
  box -> page;
  ga -> page;
  page -> banned [style=dashed, label="сложить нельзя"];
''',
    )


def fig_gates() -> None:
    render_dot(
        "04-dva-mehanizma",
        f'''
  label="Рис. 4. Два механизма до базы";
  labelloc=t;
  fontsize=20;
  fontname="{FONT}";

  click [label="Нажатие «лучшее свободное место»", fillcolor="#F3F4F6"];
  gate1 [label="1. Окно очереди\\nномер уже допущен\\nи 60 секунд не истекли?", shape=diamond, fillcolor="#FFF4DE", color="#A15C07"];
  no1 [label="Отказ\\nPostgres не вызывается", fillcolor="#FDECEC", color="#B42318"];
  gate2 [label="2. Жетон holds:primary\\nобщий бюджет холдов\\nжетон на эту секунду есть?", shape=diamond, fillcolor="#FFF4DE", color="#A15C07"];
  no2 [label="«Окно ещё ваше,\\nповторите через секунду»\\nBEGIN нет", fillcolor="#FDECEC", color="#B42318"];
  db [label="Первичный Postgres\\nусловный переход free → held\\nповторная проверка строки", fillcolor="#E7EEF8", color="#2451A3"];

  click -> gate1;
  gate1 -> no1 [label="нет"];
  gate1 -> gate2 [label="да"];
  gate2 -> no2 [label="нет"];
  gate2 -> db [label="да"];
''',
    )


def fig_age() -> None:
    render_dot(
        "06-vozrast-snimka",
        f'''
  label="Рис. 6. Пока на экране цифры, их возраст ограничен";
  labelloc=t;
  fontsize=20;
  fontname="{FONT}";
  rankdir=LR;

  lag [label="Отставание реплики\\nбюджет ≤ 200 мс\\nдольше — цифры снимаются", fillcolor="#E7EEF8", color="#2451A3"];
  worker [label="Воркер\\n200 мс", fillcolor="#FFF4DE", color="#A15C07"];
  cdn [label="TTL снимка на CDN\\n1 с", fillcolor="#E5F4F1", color="#1F7A6B"];
  age [label="Возраст ≤ 1,4 с\\n0,2 + 0,2 + 1,0", fillcolor="#F7F7F5"];
  err [label="Ошибка free_units\\n≲ холды/с × единиц в холде × возраст\\nдешёвый сектор: 500 × 1 × 1,4 ≈ 700", fillcolor="#F3F4F6"];
  admits [label="Ошибка free_admits считается отдельно\\nложа на 12 гостей: 500 × 12 × 1,4 = 8 400", fillcolor="#FFF4DE", color="#A15C07"];
  stale [label="Реплика старше 200 мс\\nили as_of старше 5 с\\n«наличие уточняется»", fillcolor="#FDECEC", color="#B42318"];

  lag -> worker -> cdn -> age -> err;
  err -> admits;
  lag -> stale [style=dashed, label="предохранитель"];
''',
    )


def fig_sequence() -> None:
    actors = [
        ("Браузер", "#F3F4F6", "#374151"),
        ("CDN", "#E5F4F1", "#1F7A6B"),
        ("Redis\nочереди и жетона", "#FFF4DE", "#A15C07"),
        ("Первичный\nPostgres", "#E7EEF8", "#2451A3"),
    ]
    width, height = 1280, 860
    margin_x = 90
    top = 118
    col_w = (width - 2 * margin_x) / len(actors)
    xs = [margin_x + col_w * (i + 0.5) for i in range(len(actors))]
    header_h = 64

    messages = [
        (0, 1, "1. GET оболочка", False),
        (1, 0, "2. Из кэша, origin не вызывается", False),
        (0, 1, "3. GET снимок", False),
        (1, 0, "4. serving, as_of, три счётчика", False),
        (0, 0, "5. Ждёт (номер − serving) / 500", True),
        (0, 2, "6. POST холд, когда окно открыто", False),
        (2, 2, "7. Окна нет или жетона нет — ответ без BEGIN", True),
        (2, 3, "8. Жетон есть: условный переход free → held", False),
        (3, 0, "9. Ответ из снимка строки, PDF = confirmed_text", False),
    ]

    y0 = top + header_h + 36
    gap = 72
    ys = [y0 + i * gap for i in range(len(messages))]

    def esc(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="42" text-anchor="middle" font-family="{FONT}" font-size="22" fill="#1C2B33">Рис. 5. Что происходит в 12:00:00</text>',
        f'<text x="{width/2}" y="70" text-anchor="middle" font-family="{FONT}" font-size="13" fill="#5C6B73">Горячий путь не рисует origin: оболочка и снимок уже на CDN</text>',
    ]
    bottom = ys[-1] + 28
    for i, (title, fill, stroke) in enumerate(actors):
        x = xs[i]
        lines = title.split("\n")
        box_w = 210
        parts.append(
            f'<rect x="{x - box_w/2}" y="{top}" width="{box_w}" height="{header_h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
        )
        for j, line in enumerate(lines):
            ly = top + 26 + j * 18
            parts.append(
                f'<text x="{x}" y="{ly}" text-anchor="middle" font-family="{FONT}" font-size="14" fill="#1C2B33">{esc(line)}</text>'
            )
        parts.append(
            f'<line x1="{x}" y1="{top + header_h}" x2="{x}" y2="{bottom}" stroke="#8AA0A8" stroke-width="1.4" stroke-dasharray="5 5"/>'
        )

    for idx, ((src, dst, label, note), y) in enumerate(zip(messages, ys)):
        color = "#B42318" if note and src == dst and "BEGIN" in label else "#3D5159"
        if src == dst:
            x = xs[src]
            side = -1 if src >= len(actors) / 2 else 1
            parts.append(
                f'<path d="M {x} {y} C {x + side * 64} {y}, {x + side * 64} {y + 28}, {x} {y + 34}" fill="none" stroke="{color}" stroke-width="1.4"/>'
            )
            parts.append(
                f'<polygon points="{x},{y+40} {x+side*8},{y+28} {x-side*2},{y+30}" fill="{color}"/>'
            )
            anchor = "end" if side < 0 else "start"
            tx = x + side * 74
            parts.append(
                f'<text x="{tx}" y="{y + 14}" text-anchor="{anchor}" font-family="{FONT}" font-size="13" fill="{color}">{esc(label)}</text>'
            )
        else:
            x1, x2 = xs[src], xs[dst]
            direction = 1 if x2 > x1 else -1
            parts.append(
                f'<line x1="{x1}" y1="{y}" x2="{x2 - direction * 10}" y2="{y}" stroke="{color}" stroke-width="1.5"/>'
            )
            tip = x2 - direction * 2
            parts.append(
                f'<polygon points="{tip},{y} {tip - direction * 10},{y - 5} {tip - direction * 10},{y + 5}" fill="{color}"/>'
            )
            mx = (x1 + x2) / 2
            parts.append(
                f'<rect x="{mx - 230}" y="{y - 22}" width="460" height="18" fill="white"/>'
            )
            parts.append(
                f'<text x="{mx}" y="{y - 8}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="#1C2B33">{esc(label)}</text>'
            )

    parts.append("</svg>")
    svg = "\n".join(parts)
    (OUT / "05-posledovatelnost.svg").write_text(svg, encoding="utf-8")
    # PNG через rsvg или convert, если есть. Иначе оставим SVG и снимем PNG отдельно.
    png = OUT / "05-posledovatelnost.png"
    for cmd in (
        ["rsvg-convert", "-w", "1600", "-o", str(png), str(OUT / "05-posledovatelnost.svg")],
        ["convert", "-background", "white", "-density", "140", str(OUT / "05-posledovatelnost.svg"), str(png)],
    ):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise SystemExit("Нет rsvg-convert и convert, чтобы сделать PNG последовательности")


def main() -> None:
    fig_potok()
    fig_schema()
    fig_kinds()
    fig_gates()
    fig_age()
    fig_sequence()


if __name__ == "__main__":
    main()
