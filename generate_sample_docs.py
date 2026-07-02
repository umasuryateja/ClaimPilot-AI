import os
import subprocess
import sys

def install_reportlab():
    print("Installing reportlab for PDF generation...")
    # Use the virtual environment's pip
    pip_path = os.path.join("venv", "Scripts", "pip.exe")
    if not os.path.exists(pip_path):
        pip_path = "pip" # Fallback
    subprocess.check_call([pip_path, "install", "reportlab"])

def create_documents():
    from PIL import Image, ImageDraw
    from reportlab.pdfgen import canvas

    os.makedirs("sample_documents", exist_ok=True)
    
    # ----------------------------------------------------
    # Claim 1: Clean, complete claim (should Fast-track)
    # ----------------------------------------------------
    claim_1_content = """FIRST NOTICE OF LOSS (FNOL)
===========================
Policy Information:
- Policy Number: POL-883721-09
- Policyholder Name: Charles Sterling
- Effective Dates: 2025-01-01 to 2025-12-31

Incident Information:
- Date: 2026-05-12
- Time: 14:30
- Location: 1422 Elm Street, Springfield
- Description: While backing out of the driveway, the policyholder scraped the rear bumper of the vehicle against a low concrete pillar. The scratch is deep but purely cosmetic.

Involved Parties:
- Claimant: Charles Sterling
- Third Parties: None
- Contact Details: csterling@email.com, 555-0199

Asset Details:
- Asset Type: 2022 Honda Civic (Sedan)
- Asset ID: VIN-1HGFA1FP0381
- Estimated Damage: $1,200.00

Other Mandatory Fields:
- Claim Type: Collision
- Attachments: None
- Initial Estimate: $1,200.00
"""
    with open("sample_documents/claim_1_fasttrack.txt", "w", encoding="utf-8") as f:
        f.write(claim_1_content)
    print("Created claim_1_fasttrack.txt")

    # ----------------------------------------------------
    # Claim 2: Missing mandatory fields (should Manual Review)
    # ----------------------------------------------------
    claim_2_lines = [
        "FIRST NOTICE OF LOSS (FNOL) REPORT",
        "----------------------------------",
        "Policy Information:",
        "- Policy Number: POL-992211-04",
        "- Policyholder Name: ", # Blank
        "- Effective Dates: 2025-06-01 to 2026-06-01",
        "",
        "Incident Information:",
        "- Date: 2026-02-18",
        "- Time: 08:15 AM",
        "- Location: ", # Blank
        "- Description: The claimant parked their car in a public parking lot. Upon returning, they discovered the driver-side door had a large dent, apparently from another car door swinging open.",
        "",
        "Involved Parties:",
        "- Claimant: Arthur Pendelton",
        "- Third Parties: Unknown",
        "- Contact Details: arthur.p@email.com",
        "",
        "Asset Details:",
        "- Asset Type: 2019 Toyota RAV4",
        "- Asset ID: VIN-JT3HPRFV029",
        "- Estimated Damage: $850.00",
        "",
        "Other Fields:",
        "- Claim Type: Property Damage",
        "- Attachments: N/A",
        "- Initial Estimate: $1,000.00"
    ]
    
    c2 = canvas.Canvas("sample_documents/claim_2_missing.pdf")
    y = 800
    c2.setFont("Helvetica-Bold", 16)
    c2.drawString(50, y, claim_2_lines[0])
    c2.setFont("Helvetica", 10)
    y -= 25
    c2.drawString(50, y, claim_2_lines[1])
    y -= 20
    
    for line in claim_2_lines[2:]:
        c2.drawString(50, y, line)
        y -= 18
        if y < 50:
            c2.showPage()
            y = 800
    c2.save()
    print("Created claim_2_missing.pdf")

    # ----------------------------------------------------
    # Claim 3: Fraud/Staged language in description (should Investigation Flag)
    # ----------------------------------------------------
    claim_3_lines = [
        "FNOL STATEMENT - POTENTIAL FRAUD TEST CASE",
        "=========================================",
        "Policy Information:",
        "- Policy Number: POL-445588-12",
        "- Policyholder Name: Sandra Vance",
        "- Effective Dates: 2025-09-01 to 2026-09-01",
        "",
        "Incident Information:",
        "- Date: 2026-06-25",
        "- Time: 23:45",
        "- Location: Intersection of 5th Ave and Main St",
        "- Description: The claimant reports that they collided with another vehicle at the intersection. However, witnesses at the scene reported that the crash appeared entirely staged to generate insurance payouts, and the claimant's description of events is highly inconsistent with physical tire marks on the road.",
        "",
        "Involved Parties:",
        "- Claimant: Sandra Vance",
        "- Third Parties: None",
        "- Contact Details: svance@email.com, 555-0244",
        "",
        "Asset Details:",
        "- Asset Type: 2021 BMW 330i",
        "- Asset ID: VIN-WBA5R1C014",
        "- Estimated Damage: $28,500.00",
        "",
        "Other Fields:",
        "- Claim Type: Collision",
        "- Attachments: No attachments",
        "- Initial Estimate: $30,000.00"
    ]
    
    c3 = canvas.Canvas("sample_documents/claim_3_fraud.pdf")
    y = 800
    c3.setFont("Helvetica-Bold", 16)
    c3.drawString(50, y, claim_3_lines[0])
    c3.setFont("Helvetica", 10)
    y -= 25
    c3.drawString(50, y, claim_3_lines[1])
    y -= 20
    
    for line in claim_3_lines[2:]:
        # Split description line if too long for pdf drawing
        if len(line) > 90 and "- Description:" in line:
            desc_part1 = line[:90]
            desc_part2 = line[90:]
            c3.drawString(50, y, desc_part1)
            y -= 18
            c3.drawString(70, y, desc_part2)
            y -= 18
        else:
            c3.drawString(50, y, line)
            y -= 18
        if y < 50:
            c3.showPage()
            y = 800
    c3.save()
    print("Created claim_3_fraud.pdf")

    # ----------------------------------------------------
    # Claim 4: Injury claim (should Specialist Queue)
    # ----------------------------------------------------
    claim_4_content = """FNOL INTAKE FORM
----------------
Policy Information:
- Policy Number: POL-112233-08
- Policyholder Name: Richard Vance
- Effective Dates: 2025-10-15 to 2026-10-15

Incident Information:
- Date: 2026-03-10
- Time: 11:00
- Location: Highway 101, Mile Marker 45
- Description: The policyholder's vehicle was rear-ended by a third party at high speed. The impact pushed the car into the barrier. The policyholder sustained whiplash and minor head injuries, requiring immediate transport to the emergency room.

Involved Parties:
- Claimant: Richard Vance
- Third Parties: Driver of vehicle 2 (John Doe)
- Contact Details: rvance@email.com, 555-8833

Asset Details:
- Asset Type: 2020 Ford Explorer
- Asset ID: VIN-1FM5K8D84
- Estimated Damage: $18,500.00

Other Fields:
- Claim Type: Injury
- Attachments: Medical report page 1, Vehicle damage photos
- Initial Estimate: $22,000.00
"""
    with open("sample_documents/claim_4_injury.txt", "w", encoding="utf-8") as f:
        f.write(claim_4_content)
    print("Created claim_4_injury.txt")

    # ----------------------------------------------------
    # Claim 5: Scanned/Image-based PDF (OCR Fallback)
    # ----------------------------------------------------
    claim_5_lines = [
        "SCANNED INSURANCE INTAKE REPORT",
        "Policy Number: POL-776655-11",
        "Policyholder Name: Edward Murphy",
        "Effective Dates: 2025-03-01 to 2026-03-01",
        "Incident Date: 2026-04-05",
        "Incident Location: 998 Oak Road, Centerville",
        "Claimant: Edward Murphy",
        "Asset Type: 2018 Chevrolet Silverado",
        "Estimated Damage: $4,500.00",
        "Claim Type: Collision",
        "Attachments: None",
        "Initial Estimate: $4,500.00",
        "Incident Description: A fallen tree branch struck the hood of the truck while parked overnight. Denting on the hood and minor paint scratching."
    ]
    
    # We create a white PIL image, draw text as black pixels, and save it as a PDF
    # Since pdfplumber extracts 0 text, this will force OCR path to trigger.
    # We use a large enough resolution and spacing so OCR works reliably.
    img = Image.new('RGB', (1000, 1400), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    y = 60
    for line in claim_5_lines:
        # Drawing with default bitmap font (which is basic, but readable at high dpi)
        # To make it readable, we write it in a clear spacing
        d.text((80, y), line, fill=(0, 0, 0))
        y += 45
        
    img.save("sample_documents/claim_5_scanned.pdf", "PDF", resolution=150.0)
    print("Created claim_5_scanned.pdf")

if __name__ == "__main__":
    install_reportlab()
    create_documents()
