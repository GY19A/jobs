import json
import csv
import os
import math

def main():
    # 1. Load scores (AI Exposure)
    scores = {}
    if os.path.exists("../scores.json"):
        with open("../scores.json", "r", encoding="utf-8") as f:
            for item in json.load(f):
                scores[item["slug"]] = item
    else:
        print("Error: ../scores.json not found")
        return

    # 2. Load occupations details from CSV
    occupations = []
    if os.path.exists("../occupations.csv"):
        with open("../occupations.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                occupations.append(row)
    else:
        print("Error: ../occupations.csv not found")
        return

    # 3. Education hierarchy (highest to lowest for vertical layout)
    education_order = [
        "Doctoral or professional degree",
        "Master's degree",
        "Bachelor's degree",
        "Associate's degree",
        "Postsecondary nondegree award",
        "Some college, no degree",
        "High school diploma or equivalent",
        "No formal educational credential",
        "See How to Become One" 
    ]

    education_labels = {
        "Doctoral or professional degree": "Doctoral",
        "Master's degree": "Master's",
        "Bachelor's degree": "Bachelor's",
        "Associate's degree": "Associate's",
        "Postsecondary nondegree award": "Postsec Award",
        "Some college, no degree": "Some College",
        "High school diploma or equivalent": "High School",
        "No formal educational credential": "No Credential",
        "See How to Become One": "Variable"
    }

    # 4. Merge data
    nodes = []
    
    for row in occupations:
        slug = row["slug"]
        if slug not in scores:
            continue
            
        score_data = scores[slug]
        
        if "exposure" not in score_data or score_data["exposure"] is None:
            continue
            
        edu_raw = row.get("entry_education", "See How to Become One")
        
        try:
            jobs_count = int(row.get("num_jobs_2024", 0))
            jobs_count = jobs_count if jobs_count > 0 else 1000
        except ValueError:
            jobs_count = 1000
            
        try:
            pay = int(row.get("median_pay_annual", 0))
        except ValueError:
            pay = 0

        # Radius mapping (non-linear for better visualization of huge gaps)
        radius = max(3, math.pow(jobs_count, 0.4) / 4)

        # Color mapping logic based on exposure (0-10)
        exposure = score_data["exposure"]
        if exposure <= 3:
            color = "#00FFAA" # Neon Green
        elif exposure <= 6:
            color = "#FFD700" # Neon Yellow
        elif exposure <= 8:
            color = "#FF6347" # Neon Orange
        else:
            color = "#FF003C" # Neon Red/Pink

        nodes.append({
            "id": slug,
            "title": row["title"],
            "category": row["category"],
            "education": education_labels.get(edu_raw, edu_raw),
            "education_level": education_order.index(edu_raw) if edu_raw in education_order else 8,
            "exposure": exposure,
            "rationale": score_data.get("rationale", ""),
            "jobs": jobs_count,
            "pay": pay,
            "radius": radius,
            "color": color
        })

    # Sort nodes by education and then exposure
    nodes.sort(key=lambda x: (x["education_level"], x["exposure"]))

    # 5. Save final JSON
    output = {
        "nodes": nodes,
        "education_levels": [
            {"id": i, "label": education_labels.get(edu, edu)}
            for i, edu in enumerate(education_order)
            if edu != "See How to Become One"
        ]
    }

    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(',', ':'))

    print(f"Successfully processed {len(nodes)} occupations into data.json")

if __name__ == "__main__":
    main()