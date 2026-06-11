# -*- coding: utf-8 -*-
"""CMUEAA Alumni CSV — full reprocessing analysis"""
import pandas as pd
import re, json, sys

CSV = "/Users/chawanchiwarattanaphan/Desktop/Claude Code Data/CMUEAA Database/Entaneer_Alumni.csv"
df = pd.read_csv(CSV, dtype=str).fillna("")
df.columns = [c.strip() for c in df.columns]

out = {}
out["total_rows"] = len(df)

# --- Member status ---
out["status"] = df["สถานะสมาชิก"].str.strip().replace("", "(ว่าง)").value_counts().to_dict()

# --- Gender ---
g = df["เพศ"].str.strip().str.lower().replace("", "(ว่าง)")
out["gender"] = g.value_counts().to_dict()

# --- Department ---
out["department"] = df["ภาควิชา"].str.strip().replace("", "(ว่าง)").value_counts().to_dict()

# --- Gear distribution ---
gear = pd.to_numeric(df["เกียร์"].str.strip(), errors="coerce")
out["gear_invalid_or_blank"] = int(gear.isna().sum())
gear_counts = gear.dropna().astype(int).value_counts().sort_index()
out["gear_counts"] = {int(k): int(v) for k, v in gear_counts.items()}

# --- Province ---
prov = df["จังหวัด"].str.strip().replace("", "(ว่าง)")
out["province_top15"] = prov.value_counts().head(15).to_dict()
out["province_blank"] = int((prov == "(ว่าง)").sum())
out["province_unique_nonblank"] = int(prov[prov != "(ว่าง)"].nunique())

# --- Registration year (Buddhist) ---
reg = pd.to_datetime(df["วันที่สมัคร"].str.strip(), errors="coerce")
out["reg_blank_or_invalid"] = int(reg.isna().sum())
reg_year = (reg.dt.year + 543).dropna().astype(int).value_counts().sort_index()
out["reg_year_counts"] = {int(k): int(v) for k, v in reg_year.items()}

# --- Occupation ---
out["occupation_top10"] = df["อาชีพ"].str.strip().replace("", "(ว่าง)").value_counts().head(10).to_dict()

# --- Business type ---
out["business_top10"] = df["ประเภทธุรกิจ"].str.strip().replace("", "(ว่าง)").value_counts().head(10).to_dict()

# --- Completeness per column ---
comp = {}
for c in df.columns:
    blank = int((df[c].str.strip() == "").sum())
    comp[c] = {"blank": blank, "pct_blank": round(blank / len(df) * 100, 1)}
out["completeness"] = comp

# --- Phone analysis ---
ph = df["เบอร์โทรศัพท์"].str.strip()
ph_nonblank = ph[ph != ""]
digits = ph_nonblank.str.replace(r"\D", "", regex=True)
def phone_class(d):
    if len(d) == 9: return "9 หลัก (ขาด 0 นำหน้า)"
    if len(d) == 10 and d.startswith("0"): return "10 หลัก ขึ้น 0 (ปกติ)"
    if len(d) == 10: return "10 หลัก ไม่ขึ้น 0"
    if len(d) == 11 and d.startswith("66"): return "11 หลัก ขึ้น 66 (intl)"
    if len(d) < 9: return "สั้นกว่า 9 หลัก (ใช้ไม่ได้)"
    return "อื่นๆ/ยาวผิดปกติ"
out["phone_blank"] = int((ph == "").sum())
out["phone_classes"] = digits.apply(phone_class).value_counts().to_dict()
out["phone_has_format_chars"] = int(ph_nonblank.str.contains(r"[-\s().]", regex=True).sum())

# --- Email analysis ---
em = df["อีเมล"].str.strip().str.lower()
em_nonblank = em[em != ""]
valid_re = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")
out["email_blank"] = int((em == "").sum())
out["email_invalid_format"] = int((~em_nonblank.str.match(valid_re)).sum())
out["email_dup_count"] = int(em_nonblank.duplicated().sum())
dup_emails = em_nonblank[em_nonblank.duplicated(keep=False)].value_counts().head(8)
out["email_top_dups"] = dup_emails.to_dict()
domains = em_nonblank[em_nonblank.str.match(valid_re)].str.split("@").str[1]
out["email_top_domains"] = domains.value_counts().head(8).to_dict()

# --- Duplicates ---
sid = df["รหัสนักศึกษา"].str.strip()
sid_nonblank = sid[sid != ""]
out["studentid_blank"] = int((sid == "").sum())
out["studentid_dups"] = int(sid_nonblank.duplicated().sum())
out["studentid_dup_examples"] = sid_nonblank[sid_nonblank.duplicated(keep=False)].value_counts().head(8).to_dict()

name_key = (df["ชื่อ"].str.strip() + "|" + df["นามสกุล"].str.strip())
name_nonblank = name_key[(df["ชื่อ"].str.strip() != "") & (df["นามสกุล"].str.strip() != "")]
out["name_dups"] = int(name_nonblank.duplicated().sum())

# --- Birthdate ---
dob = pd.to_datetime(df["วันเกิด"].str.strip(), errors="coerce")
out["dob_blank_or_invalid"] = int(dob.isna().sum())
ages = (pd.Timestamp("2026-06-11") - dob).dt.days // 365
ages_valid = ages.dropna()
out["age_stats"] = {
    "min": int(ages_valid.min()), "max": int(ages_valid.max()),
    "median": int(ages_valid.median()),
    "suspicious_under18": int((ages_valid < 18).sum()),
    "suspicious_over90": int((ages_valid > 90).sum()),
}
# Jan 1 birthdays (common default-date artifact)
jan1 = dob.dropna()
out["dob_jan1_count"] = int(((jan1.dt.month == 1) & (jan1.dt.day == 1)).sum())

# --- Cross-check: Active by gear / dept ---
active = df[df["สถานะสมาชิก"].str.strip() == "Active"]
out["active_total"] = len(active)
out["active_by_dept_top5"] = active["ภาควิชา"].str.strip().replace("", "(ว่าง)").value_counts().head(5).to_dict()

# --- Workplace fields ---
out["workplace_blank"] = int((df["สถานที่ทำงาน"].str.strip() == "").sum())
out["position_blank"] = int((df["ตำแหน่ง"].str.strip() == "").sum())

print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
