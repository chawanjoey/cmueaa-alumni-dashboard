# CMUEAA Alumni Dashboard

Dashboard ฐานข้อมูลศิษย์เก่าคณะวิศวกรรมศาสตร์ มหาวิทยาลัยเชียงใหม่ (CMUEAA)

- **Live (Vercel):** https://cmueaa-dashboard.vercel.app
- **Live (GitHub Pages):** https://chawanjoey.github.io/cmueaa-alumni-dashboard/

## Pipeline

| Script | หน้าที่ |
|---|---|
| `build_master.py` | Merge ข้อมูล backend + CSV เดิม → master file (dedupe, ลบ spam, normalize เบอร์โทร, enrich จังหวัดจากรหัสไปรษณีย์) |
| `analyze.py` | วิเคราะห์คุณภาพข้อมูล CSV |
| `generate_dashboard.py` | อ่าน master CSV → สร้าง `index.html` (static, Chart.js) |

หมายเหตุ: ไฟล์ข้อมูลสมาชิก (CSV/XLSX) ไม่อยู่ใน repo นี้ — มีข้อมูลส่วนบุคคล ห้าม push

## Tech
Static HTML single file + Chart.js 4 (CDN) + Sarabun font, dark theme
