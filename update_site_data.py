"""
docs/data.json에 앞으로 30일치 분당대진고등학교 급식 정보를 JSON으로 써주는 스크립트.

GitHub Pages가 서빙하는 docs/index.html이 이 JSON을 fetch해서 달력 형태로 그려줍니다.
GitHub Actions가 매일 밤 22시(KST)에 update_readme.py와 함께 이 스크립트를 실행한 뒤,
바뀐 파일들을 자동으로 커밋/푸시하도록 .github/workflows/daily-meal-readme.yml 에
예약되어 있습니다.
"""

import json
import sys
from datetime import datetime, timedelta

from bundang_daejin_meal import get_full_meal_info_for_date
from food_emoji import get_food_emojis
from update_readme import KST, WEEKDAY_NAMES

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA_PATH = "docs/data.json"
DAYS_AHEAD = 30


def build_day_entry(target_date):
    """하루치 급식 정보를 index.html이 쓰는 JSON 구조로 만듭니다."""
    meals_of_day = get_full_meal_info_for_date(target_date)
    entry = {
        "date": target_date.strftime("%Y-%m-%d"),
        "weekday": WEEKDAY_NAMES[target_date.weekday()],
        "meals": {},
    }

    for meal_name in ["중식", "석식"]:
        info = meals_of_day.get(meal_name)
        if info is None:
            entry["meals"][meal_name] = None
            continue

        entry["meals"][meal_name] = {
            "calorie": info["calorie"],
            "nutrition": info["nutrition"],
            "dishes": [
                {"name": dish, "emojis": get_food_emojis(dish)}
                for dish in info["dishes"]
            ],
        }

    return entry


def main():
    today = datetime.now(KST).date()
    days = [build_day_entry(today + timedelta(days=i)) for i in range(DAYS_AHEAD)]

    payload = {
        "generated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "days": days,
    }

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"{len(days)}일치 급식 정보 생성 완료")


if __name__ == "__main__":
    main()
