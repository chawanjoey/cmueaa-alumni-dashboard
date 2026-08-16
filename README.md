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

## แบบฟอร์มสมาชิก (`cf-register-form/`)

ต้นแบบระบบรับสมัครและอัปเดตข้อมูลสมาชิก deploy บน Cloudflare Pages: https://cmueaa-register-form.pages.dev

| หน้า | เนื้อหา |
|---|---|
| `index.html` | ฟอร์มสมัคร 9 ช่องบังคับ, คำนวณรุ่นเกียร์จากรหัสนักศึกษา, ตรวจสมัครซ้ำ |
| `consent.html` | หน้าขอความยินยอมก่อนเชื่อมต่อ LINE เพื่อดึงชื่อ-อีเมลอัตโนมัติ |
| `profile.html` | โปรไฟล์เต็ม — ที่ทำงาน (หลายรายการ), ใบ กว., ธุรกิจของสมาชิก, ตั้งค่าความเป็นส่วนตัวรายช่อง |
| `workflow.html` | ผังการรับสมัครและอัปเดตข้อมูล 7 หัวข้อ (Mermaid) |
| `privacy.html` | นโยบายความเป็นส่วนตัวตาม พ.ร.บ.คุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 |
| `assets/brand.css` | ชุดรูปแบบส่วนกลาง — ตราสมาคม สี ตัวอักษร การเคลื่อนไหว |

ทุกหน้าเป็น static HTML ไม่มี backend — ปุ่มส่งข้อมูลแสดง payload ที่จะส่งเข้าระบบจริงเท่านั้น

## Tech
Static HTML + Chart.js 4 (dashboard) · Mermaid 11 (ผังงาน) · Chakra Petch + IBM Plex Sans Thai
