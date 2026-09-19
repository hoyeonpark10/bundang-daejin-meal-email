"""
분당대진고등학교 '오늘'의 중식/석식 정보를 이메일로 보내는 스크립트.

GitHub Actions가 매일 아침 6시(KST)에 이 스크립트를 실행하도록
.github/workflows/daily-meal-email.yml 에 예약되어 있습니다.

이메일 발송은 Resend(https://resend.com) API를 사용합니다. (Gmail 앱 비밀번호처럼
구글 계정 보안 정책과 씨름할 필요 없이 API 키 하나로 바로 보낼 수 있습니다.)

필요한 환경변수 (GitHub 저장소 Secrets에 등록):
- RESEND_API_KEY: Resend 대시보드(API Keys 메뉴)에서 발급받은 키
- RECIPIENT_EMAIL: 급식 안내를 받을 이메일 주소
  (도메인 인증 없이 쓰는 기본 발신 주소 onboarding@resend.dev는 Resend 가입 시
  사용한 이메일 주소로만 보낼 수 있습니다. 즉 RECIPIENT_EMAIL은 Resend 가입 이메일과
  같아야 합니다.)
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from bundang_daejin_meal import get_meal_for_date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KST = timezone(timedelta(hours=9))
WEEKDAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]

RESEND_API_URL = "https://api.resend.com/emails"
SENDER_ADDRESS = "Bundang Daejin Meal <onboarding@resend.dev>"


def build_email_body(target_date, meals_of_day):
    """오늘의 중식/석식 정보를 보기 좋은 텍스트로 만듭니다."""
    weekday = WEEKDAY_NAMES[target_date.weekday()]
    date_str = target_date.strftime("%Y년 %m월 %d일")

    lines = []
    lines.append(f"[{date_str} ({weekday})] 분당대진고등학교 급식 안내")
    lines.append("")

    for meal_name in ["중식", "석식"]:
        dish_names = meals_of_day.get(meal_name)
        lines.append(f"■ {meal_name}")
        if dish_names:
            for dish in dish_names:
                lines.append(f"  - {dish}")
        else:
            lines.append(f"  오늘은 {meal_name}을(를) 배식하지 않습니다.")
        lines.append("")

    return "\n".join(lines)


def send_email(subject, body, api_key, recipient_email):
    payload = json.dumps({
        "from": SENDER_ADDRESS,
        "to": [recipient_email],
        "subject": subject,
        "text": body,
    }).encode("utf-8")

    request = urllib.request.Request(
        RESEND_API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        raise RuntimeError(f"이메일 발송 실패 ({error.code}): {error_body}")


def main():
    api_key = os.environ["RESEND_API_KEY"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]

    today = datetime.now(KST).date()
    meals_of_day = get_meal_for_date(today)

    subject = f"[분당대진고] {today.strftime('%Y-%m-%d')} 중식/석식 안내"
    body = build_email_body(today, meals_of_day)

    send_email(subject, body, api_key, recipient_email)

    print("이메일 전송 완료:", recipient_email)
    print(body)


if __name__ == "__main__":
    main()
