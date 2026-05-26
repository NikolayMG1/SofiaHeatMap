"""
Sofia Urban Heat Island Dataset Generator
==========================================
Подаваш квартали на София и година/години → получаваш CSV с дневни температури.

Използва Open-Meteo API (безплатно, без регистрация).

Употреба:
    python sofia_heat_data.py --districts "Център,Люлин,Младост" --year 2023
    python sofia_heat_data.py --all --year 2023
    python sofia_heat_data.py --all --years 2015-2023
    python sofia_heat_data.py --all --years 2010,2015,2020
    python sofia_heat_data.py --list
"""

import argparse
import requests
import pandas as pd
from datetime import date

# ──────────────────────────────────────────────
# Всички 24 официални района на София + популярни квартали
# ──────────────────────────────────────────────
SOFIA_DISTRICTS = {
    # 24 официални района
    "Bancя":              (42.7272, 23.2458),
    "Витоша":             (42.6539, 23.2514),
    "Възраждане":         (42.7000, 23.3150),
    "Изгрев":             (42.6700, 23.3483),
    "Илинден":            (42.7128, 23.2900),
    "Искър":              (42.6628, 23.4186),
    "Красна поляна":      (42.7000, 23.2500),
    "Красно село":        (42.6820, 23.2980),
    "Кремиковци":         (42.7500, 23.5000),
    "Лозенец":            (42.6710, 23.3300),
    "Люлин":              (42.7063, 23.2621),
    "Младост":            (42.6439, 23.3775),
    "Надежда":            (42.7325, 23.2986),
    "Нови Искър":         (42.8000, 23.3500),
    "Оборище":            (42.7000, 23.3380),
    "Овча купел":         (42.6900, 23.2500),
    "Панчарево":          (42.5900, 23.4000),
    "Подуяне":            (42.7000, 23.3670),
    "Сердика":            (42.7050, 23.3050),
    "Слатина":            (42.6890, 23.3720),
    "Средец":             (42.6977, 23.3219),
    "Студентски":         (42.6490, 23.3530),
    "Триадица":           (42.6772, 23.3089),
    "Връбница":           (42.7350, 23.2600),

    # Популярни квартали (допълнително)
    "Бояна":              (42.6350, 23.2650),
    "Горна баня":         (42.6600, 23.2300),
    "Дружба":             (42.6680, 23.4080),
    "Драгалевци":         (42.6200, 23.3400),
    "Захарна фабрика":    (42.7150, 23.2800),
    "Иван Вазов":         (42.6850, 23.3100),
    "Малашевци":          (42.7300, 23.3800),
    "Малинова долина":    (42.6300, 23.3700),
    "Модерно предградие": (42.7400, 23.2700),
    "Обеля":              (42.7500, 23.2600),
    "Павлово":            (42.6600, 23.2900),
    "Симеоново":          (42.6300, 23.3200),
    "Суха река":          (42.7050, 23.3700),
    "Хаджи Димитър":      (42.7100, 23.3500),
    "Център":             (42.6950, 23.3250),
    "Яворов":             (42.6800, 23.3500),
}


def fetch_temperature(lat: float, lon: float, year: int) -> pd.DataFrame:
    """Изтегля дневни температури от Open-Meteo за дадена точка и година."""
    import time
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": f"{year}-01-01",
        "end_date":   f"{year}-12-31",
        "daily":      ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean"],
        "timezone":   "Europe/Sofia",
    }

    for attempt in range(5):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            wait = 10 * (attempt + 1)
            print(f"    ⚠️  Rate limit — изчакване {wait}с...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        break
    else:
        raise Exception("Твърде много заявки. Опитай по-късно.")

    data = resp.json()["daily"]
    df = pd.DataFrame({
        "date":      data["time"],
        "temp_max":  data["temperature_2m_max"],
        "temp_min":  data["temperature_2m_min"],
        "temp_mean": data["temperature_2m_mean"],
    })
    df["date"] = pd.to_datetime(df["date"])
    time.sleep(0.5)  # пауза между заявки
    return df


def build_dataset(districts: list, year: int) -> pd.DataFrame:
    unknown = [d for d in districts if d not in SOFIA_DISTRICTS]
    if unknown:
        available = ", ".join(SOFIA_DISTRICTS.keys())
        raise ValueError(f"Непознати квартали: {unknown}\nНалични: {available}")

    frames = []
    for district in districts:
        lat, lon = SOFIA_DISTRICTS[district]
        print(f"  ↓ {district} ({lat}, {lon})...")
        df = fetch_temperature(lat, lon, year)
        df.insert(0, "district", district)
        df["lat"] = lat
        df["lon"] = lon
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def parse_years(years_str: str) -> list:
    """
    Парсира години от string:
      "2023"        → [2023]
      "2015-2023"   → [2015, 2016, ..., 2023]
      "2010,2015,2020" → [2010, 2015, 2020]
    """
    years_str = years_str.strip()
    current = date.today().year

    if "-" in years_str and "," not in years_str:
        parts = years_str.split("-")
        start, end = int(parts[0]), int(parts[1])
        years = list(range(start, end + 1))
    elif "," in years_str:
        years = [int(y.strip()) for y in years_str.split(",")]
    else:
        years = [int(years_str)]

    invalid = [y for y in years if y >= current]
    if invalid:
        raise ValueError(f"Годините трябва да са преди {current}. Невалидни: {invalid}")

    return sorted(years)


def main():
    parser = argparse.ArgumentParser(
        description="Sofia Urban Heat Island — температурен dataset по квартали"
    )
    parser.add_argument("--districts", "-d", type=str,
        help='Квартали разделени със запетая: "Център,Люлин,Младост"')
    parser.add_argument("--all", action="store_true",
        help="Изтегли данни за всички квартали")
    parser.add_argument("--year", "-y", type=str,
        help="Една година (напр. 2023)")
    parser.add_argument("--years", type=str,
        help='Range или списък с години: "2015-2023" или "2010,2015,2020"')
    parser.add_argument("--output", "-o", type=str, default=None,
        help="Изходен CSV файл")
    parser.add_argument("--list", action="store_true",
        help="Покажи всички налични квартали")
    args = parser.parse_args()

    if args.list:
        print(f"\n{'Квартал':<25} {'Lat':>10} {'Lon':>10}")
        print("-" * 48)
        for name, (lat, lon) in sorted(SOFIA_DISTRICTS.items()):
            print(f"{name:<25} {lat:>10.4f} {lon:>10.4f}")
        print(f"\nОбщо: {len(SOFIA_DISTRICTS)} квартала")
        return

    # Определи годините
    if args.years:
        years = parse_years(args.years)
    elif args.year:
        years = parse_years(args.year)
    else:
        parser.error("Задай --year 2023 или --years 2015-2023")

    # Определи кварталите
    if args.all:
        districts = list(SOFIA_DISTRICTS.keys())
    elif args.districts:
        districts = [d.strip() for d in args.districts.split(",")]
    else:
        parser.error("Задай --districts или --all")

    print(f"\n🌡️  Sofia Heat Dataset Generator")
    print(f"   Квартали : {len(districts)} броя")
    print(f"   Години   : {years[0]}–{years[-1]} ({len(years)} год.)")
    print(f"   Очаквани редове: ~{len(districts) * len(years) * 365}\n")

    # Изтегли данни за всяка година
    all_frames = []
    for i, year in enumerate(years, 1):
        print(f"📅 Година {year} ({i}/{len(years)}):")
        df = build_dataset(districts, year)
        all_frames.append(df)

    combined = pd.concat(all_frames, ignore_index=True)

    # Изходен файл
    if args.output:
        out_path = args.output
    else:
        yr_label = f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])
        dist_label = "всички" if args.all else f"{len(districts)}кв"
        out_path = f"sofia_heat_{dist_label}_{yr_label}.csv"

    combined.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n✅ Запазено: {out_path}")
    print(f"   Редове  : {len(combined)}")
    print(f"   Периoд  : {combined['date'].min().date()} → {combined['date'].max().date()}")
    print(f"\n📊 Средни температури по квартал (всички години):")
    summary = (
        combined.groupby("district")["temp_mean"]
        .mean().round(2)
        .sort_values(ascending=False)
    )
    for district, temp in summary.items():
        print(f"   {district:<25} {temp}°C")


if __name__ == "__main__":
    main()