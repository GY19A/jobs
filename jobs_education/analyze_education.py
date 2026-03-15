import json
import csv
import os

def main():
    print("Analyzing Education Paradox Data...")
    
    # 1. Load AI Exposure scores
    scores = {}
    if os.path.exists("../scores.json"):
        with open("../scores.json", "r", encoding="utf-8") as f:
            for item in json.load(f):
                scores[item["slug"]] = item
    else:
        print("Error: ../scores.json not found")
        return

    # 2. Load occupations details
    occupations = []
    if os.path.exists("../occupations.csv"):
        with open("../occupations.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                occupations.append(row)
    else:
        print("Error: ../occupations.csv not found")
        return

    # 3. Define Education Levels
    # This precisely matches the BLS terminology but groups them into logical tiers
    edu_tiers = {
        "No Degree / HS": ["No formal educational credential", "High school diploma or equivalent"],
        "Postsec / Assoc": ["Postsecondary nondegree award", "Some college, no degree", "Associate's degree"],
        "Bachelor's": ["Bachelor's degree"],
        "Master's / Doc": ["Master's degree", "Doctoral or professional degree"]
    }

    def get_tier(edu_str):
        for tier, matches in edu_tiers.items():
            if edu_str in matches:
                return tier
        return "Unknown"

    nodes = []
    
    # 4. Process and Merge
    for row in occupations:
        slug = row["slug"]
        if slug not in scores:
            continue
            
        score_data = scores[slug]
        if "exposure" not in score_data or score_data["exposure"] is None:
            continue
            
        edu_raw = row.get("entry_education", "")
        tier = get_tier(edu_raw)
        
        # Keep jobs with unknown/variable education as 'Other' to maintain the 143M total
        if tier == "Unknown":
            tier = "Other / Unknown"

        try:
            jobs_count = int(row.get("num_jobs_2024", 0))
        except ValueError:
            jobs_count = 0
            
        try:
            pay = int(row.get("median_pay_annual", 0))
        except ValueError:
            pay = 0

        try:
            outlook = int(row.get("outlook_pct", 0))
        except ValueError:
            outlook = 0

        nodes.append({
            "title": row["title"],
            "category": row["category"],
            "slug": slug,
            "education": edu_raw,
            "education_tier": tier,
            "exposure": score_data["exposure"],
            "exposure_rationale": score_data.get("rationale", ""),
            "jobs": jobs_count,
            "pay": pay,
            "outlook": outlook,
            "outlook_desc": row.get("outlook_desc", ""),
            "url": row.get("url", "")
        })

    # Sort descending by exposure so hot items draw on top
    nodes.sort(key=lambda x: x["exposure"], reverse=True)

    # 5. Output
    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, separators=(',', ':'))

    print(f"Successfully processed {len(nodes)} occupations to site/data.json")

if __name__ == "__main__":
    main()
