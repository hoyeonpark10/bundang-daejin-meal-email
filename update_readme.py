"""
README.md에 '내일' 분당대진고등학교 급식(중식/석식) 정보를 채워 넣는 스크립트.

GitHub Actions가 매일 밤 22시(KST)에 이 스크립트를 실행한 뒤, 바뀐 README.md를
자동으로 커밋/푸시하도록 .github/workflows/daily-meal-readme.yml 에 예약되어 있습니다.
"""

import re
import sys
from datetime import datetime, timedelta, timezone

from bundang_daejin_meal import get_full_meal_info_for_date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KST = timezone(timedelta(hours=9))
WEEKDAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]
MEAL_EMOJI = {"조식": "🌅", "중식": "🍱", "석식": "🌙"}

README_PATH = "README.md"
START_MARKER = "<!-- MEAL:START -->"
END_MARKER = "<!-- MEAL:END -->"


def build_meal_block(meal_name, meal_info):
    """한 끼(중식/석식)에 대한 마크다운 블록을 만듭니다."""
    emoji = MEAL_EMOJI.get(meal_name, "🍽️")
    lines = []

    if meal_info is None:
        lines.append(f"### {emoji} {meal_name}")
        lines.append(f"오늘은 {meal_name}을(를) 배식하지 않습니다.")
        lines.append("")
        return lines

    dishes = meal_info["dishes"]
    calorie = meal_info["calorie"]
    nutrition = meal_info["nutrition"]

    heading = f"### {emoji} {meal_name}"
    if calorie:
        heading += f" · {calorie}"
    lines.append(heading)
    lines.append("")

    for dish in dishes:
        lines.append(f"- {dish}")
    lines.append("")

    if nutrition:
        lines.append("<details>")
        lines.append("<summary>영양 정보</summary>")
        lines.append("")
        lines.append("| 영양소 | 값 |")
        lines.append("|---|---|")
        for key, value in nutrition.items():
            lines.append(f"| {key} | {value} |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    return lines


def build_meal_section(target_date, meals_of_day):
    """주어진 날짜의 중식/석식 정보를 README에 들어갈 마크다운 블록으로 만듭니다."""
    weekday = WEEKDAY_NAMES[target_date.weekday()]
    date_str = target_date.strftime("%Y-%m-%d")

    lines = [START_MARKER, ""]
    lines.append(f"## 📅 {date_str} ({weekday}) 분당대진고등학교 급식")
    lines.append("")

    for meal_name in ["중식", "석식"]:
        lines.extend(build_meal_block(meal_name, meals_of_day.get(meal_name)))

    updated_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    lines.append("---")
    lines.append(f"_마지막 업데이트: {updated_at} (KST)_")
    lines.append("")
    lines.append(END_MARKER)

    return "\n".join(lines)


def update_readme(new_section):
    """README.md 안의 MEAL:START~MEAL:END 구간을 새 내용으로 교체합니다."""
    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)

    if pattern.search(content):
        content = pattern.sub(new_section, content)
    else:
        content = content.rstrip() + "\n\n" + new_section + "\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    tomorrow = datetime.now(KST).date() + timedelta(days=1)
    meals_of_day = get_full_meal_info_for_date(tomorrow)

    section = build_meal_section(tomorrow, meals_of_day)
    update_readme(section)

    print(section)


if __name__ == "__main__":
    main()
