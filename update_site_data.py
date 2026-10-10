"""
docs/data.json에 '내일' 분당대진고등학교 급식 정보를 JSON으로 써주는 스크립트.

GitHub Pages가 서빙하는 docs/index.html이 이 JSON을 fetch해서 화면에 그려줍니다.
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


def build_payload(target_date, meals_of_day):
    """index.html이 fetch해서 쓰는 JSON 구조를 만듭니다."""
    payload = {
        "date": target_date.strftime("%Y-%m-%d"),
        "weekday": WEEKDAY_NAMES[target_date.weekday()],
        "updated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "meals": {},
    }

    for meal_name in ["중식", "석식"]:
        info = meals_of_day.get(meal_name)
        if info is None:
            payload["meals"][meal_name] = None
            continue

        payload["meals"][meal_name] = {
            "calorie": info["calorie"],
            "nutrition": info["nutrition"],
            "dishes": [
                {"name": dish, "emojis": get_food_emojis(dish)}
                for dish in info["dishes"]
            ],
        }

    return payload


def main():
    tomorrow = datetime.now(KST).date() + timedelta(days=1)
    meals_of_day = get_full_meal_info_for_date(tomorrow)
    payload = build_payload(tomorrow, meals_of_day)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
