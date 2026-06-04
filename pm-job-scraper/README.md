# PM Job Scraper

סורק יומי שמחפש משרות **Product Manager** באתרי הקריירה של חברות הייטק (לא סייבר),
מסנן **ישראל בלבד**, ומציג את התוצאות בדשבורד סטטי ב-GitHub Pages.

ראו אפיון מלא: הקובץ הזה מתמצת; התכנון המלא נכתב בתהליך התכנון.

## איך זה עובד

1. **GitHub Action** (`.github/workflows/scrape-jobs.yml`) רץ כל בוקר ב-cron.
2. הסקרייפר (`scraper/`) קורא את רשימת החברות מ-`data/companies.yaml` (**117 חברות**, ללא סייבר).
3. **גילוי ATS אוטומטי** (`scraper/discovery.py`): מתוך `careers_url` מזוהה אוטומטית
   פלטפורמת הגיוס (Comeet / Greenhouse / Lever) והטוקן — אין צורך למלא טוקן ידנית.
4. לכל חברה, ה-**adapter** המתאים מושך את המשרות דרך ה-API הציבורי.
5. סינון: רק תפקידי **Product Manager** (כל הדרגות), רק **ישראל**.
6. חישוב "**חדש מאז אתמול**" מול `data/history.json`.
7. כתיבת `data/jobs.json`, commit ע"י ה-Action.
8. **דשבורד** סטטי (`docs/`) ב-GitHub Pages קורא את ה-JSON ומציג טבלה עם הדגשת משרות חדשות.

## הרצה מקומית

```bash
cd pm-job-scraper
pip install -r requirements.txt
python -m scraper                # מריץ סריקה -> data/jobs.json
python -m http.server -d docs    # דשבורד ב-http://localhost:8000
```

## בדיקות

```bash
cd pm-job-scraper
pip install -r requirements.txt
python -m pytest                 # בודק את לוגיקת הסינון (PM + ישראל)
```

## הוספת חברה

ערכו את `data/companies.yaml` — מספיק כתובת קריירה, ה-ATS מזוהה אוטומטית:
```yaml
- name: "Example"
  description: "תיאור קצר של החברה"
  category: "saas"                       # אל תוסיפו חברות סייבר/סמוכות
  hq: "israel"                           # israel | multinational
  careers_url: "https://example.com/careers"
  # ats: greenhouse   # אופציונלי — קיבוע ידני שעוקף את הגילוי האוטומטי
  # token: example
```

> **הערה:** חברות סייבר *ותחומים סמוכים* (appsec, identity, fraud-prevention,
> data-security) לא נכללות ברשימה במכוון — זו ההחרגה.

> **רב-לאומיות:** חברות עם מרכזי פיתוח בישראל (Google, Microsoft, Intel...) נמצאות
> ברשימה, אך רובן משתמשות ב-Workday/מערכת עצמית — הן יסומנו `unknown` בדו"ח ולא
> ייסרקו עד שיתווסף adapter מתאים. הדו"ח מציג פילוח פלטפורמות בכל ריצה.
