"""
Manual PDF Report Generation Utility Script.
Run this script in VS Code (F5) or terminal to generate an executive weekly PDF report.
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pdf_generator import pdf_generator


def main():
    print("Generating sample Weekly Executive PDF Report...")
    file_path, file_name, file_size, start_time, end_time, metrics = pdf_generator.generate_weekly_report(
        title="WEEKLY EXECUTIVE PERFORMANCE & OPERATIONS REPORT",
        custom_metrics={
            "total_revenue": 164500.00,
            "active_subscribers": 1650,
            "messages_sent": 5420,
            "delivery_success_rate": 99.4,
            "growth_rate": 15.2
        }
    )
    print("\n========================================================")
    print(f"Report Generated Successfully!")
    print(f"File Name: {file_name}")
    print(f"File Size: {file_size} bytes ({file_size / 1024:.2f} KB)")
    print(f"Location:  {os.path.abspath(file_path)}")
    print(f"Period:    {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
    print("========================================================\n")


if __name__ == "__main__":
    main()
