# backend/app/services/pdf_report.py

import json
from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.app.services.config import THRESHOLDS

class OutputGenerator:
    def generate_sms_alert(self, anomaly: Dict[str, Any], recommendation: Dict[str, Any] = None) -> str:
        event_type = anomaly["type"].upper()
        severity = anomaly["severity"].upper()
        time_window = anomaly.get("time_window", "Immediate")
        lat = anomaly["location"]["lat"]
        lon = anomaly["location"]["lon"]
        
        msg = (
            f"⚠️ CLIMATE ALERT: {severity} {event_type} predicted at Lat {lat:.2f}, Lon {lon:.2f}.\n"
            f"⏱️ Timeframe: {time_window}.\n"
            f"📊 Confidence: {anomaly['confidence']*100:.1f}%.\n"
        )
        
        if recommendation:
            msg += f"👉 Recommended Mitigation: {recommendation['strategy_name']} (Simulated Risk Reduction: {recommendation['risk_reduction_pct']}%)."
        else:
            msg += f"👉 Recommended: Monitor and prepare emergency evacuations."
            
        return msg

    def generate_geojson(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        event_type = anomaly["type"]
        severity = anomaly["severity"]
        lat = anomaly["location"]["lat"]
        lon = anomaly["location"]["lon"]
        
        import numpy as np
        num_vertices = 16
        radius_deg = 0.45 if severity == "critical" else (0.3 if severity in ("high", "severe") else 0.15)
        
        coordinates = []
        for i in range(num_vertices + 1):
            angle = i * (2.0 * np.pi / num_vertices)
            c_lat = lat + radius_deg * np.sin(angle)
            c_lon = lon + radius_deg * np.cos(angle)
            coordinates.append([round(c_lon, 4), round(c_lat, 4)])
            
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "hazard_type": event_type,
                        "severity": severity,
                        "confidence_pct": round(anomaly["confidence"] * 100, 1),
                        "time_window": anomaly.get("time_window", "Immediate"),
                        "center_lat": lat,
                        "center_lon": lon
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coordinates]
                    }
                }
            ]
        }
        return geojson

    def generate_explainability_report(self, anomaly: Dict[str, Any]) -> str:
        event_type = anomaly["type"]
        metrics = anomaly.get("metrics", {})
        
        report = f"### AI Diagnosis: {event_type.replace('_', ' ').capitalize()} Detection Rationale\n\n"
        report += f"The digital twin flagged this region because localized sensor feeds breached established warning thresholds:\n\n"
        
        for k, v in metrics.items():
            report += f"- **{k}**: {v:.2f} "
            
            if event_type == "flood":
                if k == "Rainfall":
                    report += f"(Breached threshold of >= {THRESHOLDS['flood']['precipitation_min']} mm/hr)\n"
                elif k == "Soil Moisture":
                    report += f"(Saturated at {v*100:.1f}%, exceeding soil capacity threshold of >= {THRESHOLDS['flood']['soil_moisture_min']*100:.1f}%)\n"
            elif event_type == "cyclone":
                if k == "SST":
                    report += f"(Sea surface warmth at {v:.1f}°C, exceeding thermodynamic threshold of >= {THRESHOLDS['cyclone']['sst_min']}°C)\n"
                elif k == "Wind Speed":
                    report += f"(Wind velocity at {v:.1f} km/h, exceeding kinetic threshold of >= {THRESHOLDS['cyclone']['wind_speed_min']} km/h)\n"
            elif event_type in ("heatwave", "urban_heat_island") and k == "Temperature":
                report += f"(Ambient air temperature reached {v:.1f}°C, exceeding thermal limits of >= {THRESHOLDS['heatwave']['temperature_min']}°C)\n"
            elif event_type == "forest_fire":
                if k == "Temperature":
                    report += f"(Air temperature at {v:.1f}°C >= threshold of {THRESHOLDS['forest_fire']['temperature_min']}°C)\n"
                elif k == "Humidity":
                    report += f"(Relative humidity dropped to {v:.1f}% <= fire propagation threshold of {THRESHOLDS['forest_fire']['humidity_max']}%)\n"
                elif k == "Wind Speed":
                    report += f"(Wind velocity at {v:.1f} km/h >= spreading threshold of {THRESHOLDS['forest_fire']['wind_speed_min']} km/h)\n"
            else:
                report += "\n"
                
        report += f"\n**Physical Dynamics Summary**: "
        if event_type == "flood":
            report += "When soil moisture is near saturation, the ground loses all infiltration capacity. Any additional heavy rainfall immediately converts to overland surface runoff, resulting in rapid-onset flooding."
        elif event_type == "cyclone":
            report += "Sufficiently warm sea surface temperatures (SST) act as a heat engine, feeding moisture into the convective updraft, while high wind velocities verify the formation of a low-pressure cyclonic vortex."
        elif event_type in ("heatwave", "urban_heat_island"):
            report += "Stagnant high-pressure domes prevent cloud cover and trap terrestrial solar radiation, driving surface air temperature to critical levels hazardous to humans and livestock."
        elif event_type == "forest_fire":
            report += "High temperatures dry out ground leaf litter (fuel), while low humidity maximizes fuel flammability. Strong winds feed oxygen to the combustion site and carry embers forward, causing rapid spread."
        elif event_type in ("drought", "cold_wave"):
            report += "Protracted lack of rainfall combined with elevated temperatures accelerates evaporation, depleting shallow soil moisture tables and causing agricultural water stress."
        else:
            report += "A significant meteorological divergence has been recorded, indicating high spatial anomaly gradients."
            
        return report

    def generate_action_checklist(self, anomaly: Dict[str, Any], recommendation: Dict[str, Any] = None) -> List[str]:
        event_type = anomaly["type"]
        rec_name = recommendation["strategy_name"] if recommendation else "Do Nothing"
        
        checklist = []
        checklist.append("1. **Phase 1 (Immediate Alerting)**: Dispatch alerts to regional relief headquarters and trigger sirens in target coordinates.")
        
        if event_type == "cyclone":
            checklist.append("2. **Phase 2 (Coastal Safety)**: Suspend fishing and marine operations along predicted coastlines. Enforce harbor safety protocols.")
            if "Evacuation" in rec_name:
                checklist.append("3. **Phase 3 (Evacuation)**: Initiate mandatory evac routes from low-lying coastal zones to designated concrete cyclone shelters.")
            checklist.append("4. **Phase 4 (Medical Pre-positioning)**: Dispatch mobile medical units and pre-position emergency drinking water supply.")
        elif event_type in ("flood", "heavy_rain"):
            if "Pump" in rec_name:
                checklist.append("2. **Phase 2 (Deploy Assets)**: Deploy heavy duty high-volume dewatering pumps to local low-lying urban nodes.")
            if "Drainage" in rec_name:
                checklist.append("3. **Phase 3 (Drainage Check)**: Clear stormwater blockages and open barrage gates in a controlled sequence.")
            checklist.append("4. **Phase 4 (Rescue readiness)**: Position inflatable rescue boats (NDRF) at key staging hubs near coordinates.")
        elif event_type == "forest_fire":
            if "Air-drop" in rec_name:
                checklist.append("2. **Phase 2 (Fire Containment)**: Authorize helicopter water air-drops on the fire periphery to suppress spread.")
            checklist.append("3. **Phase 3 (Buffer creation)**: Excavate fire breaks using bulldozers to remove dry fuel lines.")
            checklist.append("4. **Phase 4 (Evacuation)**: Evacuate forest settlements and establish temporary relief camps upwind.")
        elif event_type in ("heatwave", "urban_heat_island"):
            checklist.append("2. **Phase 2 (Cooling Centers)**: Activate air-conditioned cooling shelters and water kiosks.")
            checklist.append("3. **Phase 3 (Grid management)**: Request power grids to coordinate load balancing to prevent brownouts from AC usage.")
            checklist.append("4. **Phase 4 (Labor orders)**: Implement mandatory work suspension for outdoor laborers between 12:00 PM and 4:00 PM.")
        elif event_type in ("drought", "cold_wave"):
            checklist.append("2. **Phase 2 (Water allocation)**: Restrict industrial water draws and prioritize agricultural and domestic supply.")
            checklist.append("3. **Phase 3 (Water trucking)**: Deploy municipal water tankers to affected talukas.")
            checklist.append("4. **Phase 4 (Fodder camps)**: Setup cattle fodder camps and distribute crop subsidies.")
        else:
            checklist.append("2. **Phase 2 (Monitoring)**: Enhance meteorological observation frequency.")
            checklist.append("3. **Phase 3 (Coordination)**: Brief administrative officers on stand-by protocols.")

        return checklist

output_generator = OutputGenerator()

def generate_pdf_report(anomaly: Dict[str, Any], recommendation: Dict[str, Any], resources: List[Dict[str, Any]], buffer: BytesIO):
    """
    Generates a beautifully structured PDF document summarizing:
    - Event information
    - Recommended mitigation strategy
    - Diagnostic explainability
    - Action checklists
    - Assigned resource allocations
    """
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette matches Design System
    c_primary = colors.HexColor("#0d1421")
    c_accent = colors.HexColor("#2979ff")
    c_red = colors.HexColor("#ff3d57")
    c_text = colors.HexColor("#2c3e50")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=c_primary,
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=c_accent,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        textColor=c_text,
        leading=14,
        spaceAfter=8
    )
    
    alert_style = ParagraphStyle(
        'Alert',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=c_red,
        spaceAfter=10
    )
    
    story = []
    
    # Header Banner
    story.append(Paragraph("BHOOMI-DRISHTI EMERGENCY ALERT REPORT", title_style))
    story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
    story.append(Spacer(1, 10))
    
    # Event Summary Panel
    story.append(Paragraph("1. Climate Hazard Diagnostic", section_style))
    event_details = (
        f"<b>Event ID:</b> {anomaly['id']}<br/>"
        f"<b>Hazard Type:</b> {anomaly['type'].replace('_', ' ').upper()}<br/>"
        f"<b>Location:</b> {anomaly['district']}, {anomaly['state']} (Lat {anomaly['location']['lat']:.3f}, Lon {anomaly['location']['lon']:.3f})<br/>"
        f"<b>Severity Level:</b> <font color='red'><b>{anomaly['severity'].upper()}</b></font><br/>"
        f"<b>AI Forecast Confidence:</b> {anomaly['confidence']*100:.1f}%<br/>"
    )
    story.append(Paragraph(event_details, body_style))
    story.append(Spacer(1, 8))
    
    # Explainability diagnosis
    diag_text = output_generator.generate_explainability_report(anomaly)
    # clean markdown markers for PDF formatting
    diag_formatted = diag_text.replace("### AI Diagnosis: ", "<b>AI Diagnosis:</b> ").replace("- **", "• <b>").replace("**: ", "</b>: ").replace("\n\n", "<br/>").replace("\n", "<br/>")
    story.append(Paragraph(diag_formatted, body_style))
    story.append(Spacer(1, 12))
    
    # Mitigation strategy recommendation
    story.append(Paragraph("2. Recommended Mitigation Action Plan", section_style))
    if recommendation:
        strat_details = (
            f"<b>Recommended Strategy:</b> {recommendation['strategy_name']}<br/>"
            f"<b>Est. Implementation Cost:</b> {recommendation['cost']:,.1f} INR<br/>"
            f"<b>Simulated Risk Reduction:</b> {recommendation['risk_reduction_pct']}%<br/>"
            f"<b>AI Utility Optimization Score:</b> {recommendation['score']:.1f}%<br/>"
            f"<b>Feasibility / Readiness:</b> {recommendation['feasibility_score']*100:.0f}%<br/>"
            f"<b>Estimated Rescue ETA:</b> {recommendation['time_efficiency']*60:.0f} minutes<br/>"
        )
    else:
        strat_details = "<b>Recommended Strategy:</b> Do Nothing (No active strategy selected. Standby monitoring active)."
    story.append(Paragraph(strat_details, body_style))
    
    # Action checklist
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Operational Execution Checklist:</b>", body_style))
    checklist_items = output_generator.generate_action_checklist(anomaly, recommendation)
    for idx, item in enumerate(checklist_items):
        clean_item = item.replace("1. ", "").replace("2. ", "").replace("3. ", "").replace("4. ", "").replace("**", "<b>").replace("**", "</b>")
        story.append(Paragraph(f"• {clean_item}", body_style))
        
    # Page Break for Resources
    story.append(PageBreak())
    
    # Resource Allocations
    story.append(Paragraph("3. Emergency Resource Dispatch Plan", section_style))
    story.append(Paragraph("The following resources have been reserved and routed by the linear-assignment optimization engine:", body_style))
    story.append(Spacer(1, 10))
    
    # Table layout for resources
    data = [["Resource Type", "Qty Allocated", "Available Pool", "Est. ETA"]]
    for res in resources:
        data.append([
            res["resource_type"],
            str(res["allocated"]),
            str(res["available"]),
            f"{res['eta_minutes']:.0f} mins"
        ])
        
    res_table = Table(data, colWidths=[200, 100, 100, 100])
    res_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0d1421")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#bdc3c7")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8f9fa")]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(res_table)
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Note: This is an automated climate intelligence report generated by Bhoomi-Drishti under ISRO Bharatiya Antariksh guidelines. Dispatched payloads are synced with regional ground control stations.</i>", body_style))
    
    doc.build(story)
