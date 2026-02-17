# services/export_service.py - Alert Export Service (PDF & CSV)
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO, StringIO
import csv

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.enums import TA_CENTER, TA_LEFT

try:
    import pandas as pd
except ImportError:
    pd = None


class ExportService:
    """Service for exporting alerts to PDF and CSV"""
    
    @staticmethod
    def generate_pdf_report(
        alerts: List[Dict[str, Any]],
        user_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> BytesIO:
        """
        Generate a PDF report with alerts and statistics
        
        Args:
            alerts: List of alert documents
            user_name: Name of user requesting report
            filters: Optional filters applied
            
        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("Alert-Pro<br/>Alert Report", title_style)
        elements.append(title)
        
        # Report metadata
        meta_data = [
            ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')],
            ['User:', user_name],
            ['Total Alerts:', str(len(alerts))],
        ]
        
        if filters:
            if filters.get('severity'):
                meta_data.append(['Severity Filter:', filters['severity']])
            if filters.get('type'):
                meta_data.append(['Type Filter:', filters['type']])
            if filters.get('since'):
                meta_data.append(['Date From:', filters['since'].strftime('%Y-%m-%d')])
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 20))
        
        # Statistics Section
        elements.append(Paragraph("📊 Statistics Overview", heading_style))
        
        # Calculate statistics
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        type_counts = {}
        resolved_count = 0
        
        for alert in alerts:
            severity = alert.get('severity', 'low')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            alert_type = alert.get('type', 'system')
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            
            if alert.get('resolved', False):
                resolved_count += 1
        
        # Statistics table
        stats_data = [
            ['Metric', 'Value'],
            ['Total Alerts', str(len(alerts))],
            ['Resolved', str(resolved_count)],
            ['Unresolved', str(len(alerts) - resolved_count)],
            ['Critical', str(severity_counts['critical'])],
            ['High', str(severity_counts['high'])],
            ['Medium', str(severity_counts['medium'])],
            ['Low', str(severity_counts['low'])],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Severity Distribution Pie Chart
        if len(alerts) > 0:
            elements.append(Paragraph("Severity Distribution", heading_style))
            
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            
            # Data for pie chart
            pie.data = [
                severity_counts['critical'],
                severity_counts['high'],
                severity_counts['medium'],
                severity_counts['low']
            ]
            pie.labels = [
                f"Critical ({severity_counts['critical']})",
                f"High ({severity_counts['high']})",
                f"Medium ({severity_counts['medium']})",
                f"Low ({severity_counts['low']})"
            ]
            pie.slices.strokeWidth = 0.5
            pie.slices[0].fillColor = colors.HexColor('#ef4444')  # Red
            pie.slices[1].fillColor = colors.HexColor('#f97316')  # Orange
            pie.slices[2].fillColor = colors.HexColor('#f59e0b')  # Yellow
            pie.slices[3].fillColor = colors.HexColor('#22c55e')  # Green
            
            drawing.add(pie)
            elements.append(drawing)
            elements.append(Spacer(1, 20))
        
        # Alerts Detail Table
        elements.append(Paragraph("🚨 Alert Details", heading_style))
        
        if len(alerts) == 0:
            elements.append(Paragraph("No alerts found.", styles['Normal']))
        else:
            # Prepare table data (limit to first 50 for PDF size)
            table_data = [['Date', 'Severity', 'Type', 'Message', 'Status']]
            
            for alert in alerts[:50]:  # Limit to 50 alerts in PDF
                date_str = alert.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
                severity = alert.get('severity', 'low')
                alert_type = alert.get('type', 'system')
                message = alert.get('message', '')[:50] + ('...' if len(alert.get('message', '')) > 50 else '')
                status = 'Resolved' if alert.get('resolved', False) else 'Active'
                
                table_data.append([date_str, severity.upper(), alert_type, message, status])
            
            alerts_table = Table(table_data, colWidths=[1.2*inch, 0.9*inch, 0.9*inch, 2.5*inch, 0.8*inch])
            alerts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            elements.append(alerts_table)
            
            if len(alerts) > 50:
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(
                    f"<i>Showing first 50 of {len(alerts)} alerts. Download CSV for complete data.</i>",
                    styles['Normal']
                ))
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "Generated by Alert-Pro • Confidential",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_csv_export(alerts: List[Dict[str, Any]]) -> BytesIO:
        """
        Generate a CSV export of alerts
        
        Args:
            alerts: List of alert documents
            
        Returns:
            BytesIO buffer containing CSV
        """
        # Prepare data for export
        data = []
        for alert in alerts:
            data.append({
                'Alert ID': str(alert.get('_id', '')),
                'Created Date': alert.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S'),
                'Severity': alert.get('severity', 'low'),
                'Type': alert.get('type', 'system'),
                'Message': alert.get('message', ''),
                'Device ID': alert.get('device_id', ''),
                'Device Name': alert.get('device', {}).get('name', '') if alert.get('device') else '',
                'Resolved': 'Yes' if alert.get('resolved', False) else 'No',
                'Resolved Date': alert.get('resolved_at', '').strftime('%Y-%m-%d %H:%M:%S') if alert.get('resolved_at') else '',
                'Context': str(alert.get('context', {}))
            })
        
        fieldnames = [
            'Alert ID',
            'Created Date',
            'Severity',
            'Type',
            'Message',
            'Device ID',
            'Device Name',
            'Resolved',
            'Resolved Date',
            'Context'
        ]

        if pd is not None:
            buffer = BytesIO()
            df = pd.DataFrame(data, columns=fieldnames)
            df.to_csv(buffer, index=False, encoding='utf-8')
            buffer.seek(0)
            return buffer

        text_buffer = StringIO()
        writer = csv.DictWriter(text_buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        buffer = BytesIO(text_buffer.getvalue().encode('utf-8'))
        buffer.seek(0)
        return buffer
    
    @staticmethod
    async def save_export_history(db, user_id, export_type: str, filename: str, file_size: int, alert_count: int):
        """Save export history to database"""
        export_doc = {
            'user_id': user_id,
            'export_type': export_type,  # 'pdf' or 'csv'
            'filename': filename,
            'file_size': file_size,
            'alert_count': alert_count,
            'created_at': datetime.utcnow()
        }
        
        result = await db.exports.insert_one(export_doc)
        return str(result.inserted_id)
