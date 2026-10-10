"""
분당대진고등학교 다음주 급식 조회 함수

오늘 날짜를 넣으면, 다음주(월~일) 분당대진고등학교 급식을 나이스(NEIS) 오픈 API를
통해 조회해서 보기 좋게 출력하고, 딕셔너리로도 돌려주는 함수입니다.
"""

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

# Windows 콘솔(cmd/PowerShell)의 기본 코드페이지가 UTF-8이 아니면 한글 출력이 깨질 수 있어
# 표준 출력 인코딩을 UTF-8로 강제 설정합니다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 나이스 API 프록시 주소 (학교 급식 정보 조회용)
PROXY_BASE_URL = "https://k-skill-proxy.nomadamas.org"

# 분당대진고등학교 정보 (경기도교육청)
EDUCATION_OFFICE_CODE = "J10"
SCHOOL_CODE = "7530160"


def _fetch_meal_rows(target_date):
    """특정 날짜의 NEIS 급식 원본 row 리스트를 가져옵니다. 없으면 빈 리스트."""
    meal_date_str = target_date.strftime("%Y%m%d")

    query = {
        "educationOfficeCode": EDUCATION_OFFICE_CODE,
        "schoolCode": SCHOOL_CODE,
        "mealDate": meal_date_str,
    }
    url = PROXY_BASE_URL + "/v1/neis/school-meal?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})

    try:
        response = urllib.request.urlopen(request, timeout=10)
        response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        response_text = error.read().decode("utf-8")

    data = json.loads(response_text)

    # 급식 정보가 없는 날은 "mealServiceDietInfo" 안에 결과 행(row)이 없습니다.
    service_info = data.get("mealServiceDietInfo")
    if service_info is None or len(service_info) < 2:
        return []

    return service_info[1]["row"]


def get_meal_for_date(target_date):
    """
    특정 날짜(target_date, datetime.date)의 급식 정보를 조회해서
    {"조식": [...], "중식": [...], "석식": [...]} 형태의 딕셔너리로 돌려줍니다.
    급식 정보가 없는 날(주말, 방학 등)이면 빈 딕셔너리를 돌려줍니다.
    """
    meals_of_day = {}
    for row in _fetch_meal_rows(target_date):
        meal_name = row["MMEAL_SC_NM"]  # "조식", "중식", "석식"
        meals_of_day[meal_name] = clean_dish_list(row["DDISH_NM"])

    return meals_of_day


def get_full_meal_info_for_date(target_date):
    """
    특정 날짜의 급식 정보를 메뉴뿐 아니라 칼로리·영양정보까지 포함해서 돌려줍니다.

    {
        "중식": {
            "dishes": ["차조밥", "뼈없는감자탕", ...],
            "calorie": "838.9 Kcal",
            "nutrition": {"탄수화물(g)": "156.7", "단백질(g)": "30.6", ...},
        },
        "석식": {...},
    }
    """
    meals_of_day = {}
    for row in _fetch_meal_rows(target_date):
        meal_name = row["MMEAL_SC_NM"]
        meals_of_day[meal_name] = {
            "dishes": clean_dish_list(row["DDISH_NM"]),
            "calorie": row.get("CAL_INFO", "").strip(),
            "nutrition": parse_nutrition_info(row.get("NTR_INFO", "")),
        }

    return meals_of_day


def parse_nutrition_info(nutrition_text):
    """NEIS의 NTR_INFO 문자열("탄수화물(g) : 156.7<br/>...")을 딕셔너리로 바꿔줍니다."""
    nutrition = {}
    for item in nutrition_text.split("<br/>"):
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        nutrition[key.strip()] = value.strip()
    return nutrition


def clean_dish_list(dish_text):
    """
    NEIS가 주는 DDISH_NM 문자열(예: "차조밥 <br/>뼈없는감자탕 (5.6.10.16)<br/>...")을
    ["차조밥", "뼈없는감자탕", ...] 같은 깔끔한 메뉴 리스트로 바꿔줍니다.
    """
    dish_names = []
    for item in dish_text.split("<br/>"):
        item = item.strip()
        item = re.sub(r"\([0-9.]+\)", "", item)  # 알레르기 표시 번호 제거, 예: (5.6.10)
        item = item.strip()
        if item:
            dish_names.append(item)
    return dish_names


def get_next_week_dates(today):
    """오늘(today) 기준 '다음 주' 월요일부터 일요일까지 날짜 리스트를 돌려줍니다."""
    days_until_next_monday = 7 - today.weekday()  # today.weekday(): 월요일=0, 일요일=6
    next_monday = today + timedelta(days=days_until_next_monday)

    next_week_dates = []
    for i in range(7):
        next_week_dates.append(next_monday + timedelta(days=i))
    return next_week_dates


def get_next_week_bundang_daejin_meals(today):
    """
    오늘 날짜(today, datetime.date)를 입력하면 다음주 분당대진고등학교 급식을
    조회해서 화면에 출력하고, 아래와 같은 형태의 딕셔너리로 돌려줍니다.

    {
        "2026-09-21": {"조식": [...], "중식": [...], "석식": [...]},
        "2026-09-22": {"중식": [...], "석식": [...]},
        ...
    }

    급식 정보가 없는 날(주말, 공휴일 등)은 딕셔너리에 포함되지 않습니다.
    """
    next_week_meals = {}

    for target_date in get_next_week_dates(today):
        meals_of_day = get_meal_for_date(target_date)
        if not meals_of_day:
            continue

        date_key = target_date.strftime("%Y-%m-%d")
        next_week_meals[date_key] = meals_of_day

    print_meals(next_week_meals)
    return next_week_meals


def print_meals(meals_by_date):
    """딕셔너리 형태의 급식 정보를 보기 좋게 출력합니다."""
    weekday_names = ["월", "화", "수", "목", "금", "토", "일"]

    print("=== 분당대진고등학교 다음주 급식 ===")
    for date_key, meals_of_day in meals_by_date.items():
        year, month, day = date_key.split("-")
        weekday = date(int(year), int(month), int(day)).weekday()
        print(f"\n[{date_key} ({weekday_names[weekday]})]")

        for meal_name, dish_names in meals_of_day.items():
            print(f"  {meal_name}: " + ", ".join(dish_names))


if __name__ == "__main__":
    today = date.today()
    get_next_week_bundang_daejin_meals(today)
