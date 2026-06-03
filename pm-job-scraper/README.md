# PM Job Scraper

סורק יומי שמחפש משרות **Product Manager** באתרי הקריירה של חברות הייטק (לא סייבר),
מסנן **ישראל בלבד**, ומציג את התוצאות בדשבורד סטטי ב-GitHub Pages.

ראו אפיון מלא: הקובץ הזה מתמצת; התכנון המלא נכתב בתהליך התכנון.

## איך זה עובד

1. **GitHub Action** (`.github/workflows/scrape-jobs.yml`) רץ כל בוקר ב-cron.
2. הסקרייפר (`scraper/`) קורא את רשימת החברות מ-`data/companies.yaml`.
3. לכל חברה, ה-**adapter** המתאים (Comeet / Greenhouse / Lever) מושך את המשרות דרך ה-API הציבורי.
4. סינון: רק תפקידי **Product Manager** (כל הדרגות), רק **ישראל**.
5. חישוב "**חדש מאז אתמול**" מול `data/history.json`.
6. כתיבת `data/jobs.json`, commit ע"י ה-Action.
7. **דשבורד** סטטי (`docs/`) ב-GitHub Pages קורא את ה-JSON ומציג טבלה עם הדגשת משרות חדשות.

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

ערכו את `data/companies.yaml`:
```yaml
- name: "Example"
  ats: "greenhouse"     # comeet | greenhouse | lever
  token: "example"      # מזהה החברה בפלטפורמה
  homepage: "https://example.com/careers"
  category: "saas"      # אל תוסיפו חברות סייבר
```

> **הערה:** חברות סייבר לא נכללות ברשימה במכוון — זו ההחרגה.
