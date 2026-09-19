"""
분당대진고등학교 '오늘'의 중식/석식 정보를 이메일로 보내는 스크립트.

GitHub Actions가 매일 아침 6시(KST)에 이 스크립트를 실행하도록
.github/workflows/daily-meal-email.yml 에 예약되어 있습니다.

이메일 발송은 네이버 메일 SMTP(smtp.naver.com)를 사용합니다.

필요한 환경변수 (GitHub 저장소 Secrets에 등록):
- NAVER_EMAIL: 발신용 네이버 이메일 주소 (예: myid@naver.com)
- NAVER_PASSWORD: 위 네이버 계정의 로그인 비밀번호
  (네이버 계정에 2단계 인증이 켜져 있다면, 일반 비밀번호 대신 네이버 아이디 관리
  페이지에서 발급받은 "애플리케이션 비밀번호"를 사용해야 합니다.)
- RECIPIENT_EMAIL: 급식 안내를 받을 이메일 주소 (생략하면 NAVER_EMAIL로 보냄)

네이버 메일에서 "환경설정 > POP3/IMAP 설정"에서 IMAP/SMTP 사용을 켜야
아래 코드로 로그인/발송이 가능합니다.
"""

import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from bundang_daejin_meal import get_meal_for_date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KST = timezone(timedelta(hours=9))
WEEKDAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]

NAVER_SMTP_HOST = "smtp.naver.com"
NAVER_SMTP_PORT = 465


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


def send_email(subject, body, sender_email, sender_password, recipient_email):
    message = MIMEText(body, _charset="utf-8")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email

    with smtplib.SMTP_SSL(NAVER_SMTP_HOST, NAVER_SMTP_PORT) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [recipient_email], message.as_string())


def main():
    sender_email = os.environ["NAVER_EMAIL"]
    sender_password = os.environ["NAVER_PASSWORD"]
    recipient_email = os.environ.get("RECIPIENT_EMAIL", sender_email)

    today = datetime.now(KST).date()
    meals_of_day = get_meal_for_date(today)

    subject = f"[분당대진고] {today.strftime('%Y-%m-%d')} 중식/석식 안내"
    body = build_email_body(today, meals_of_day)

    send_email(subject, body, sender_email, sender_password, recipient_email)

    print("이메일 전송 완료:", recipient_email)
    print(body)


if __name__ == "__main__":
    main()
