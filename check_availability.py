from playwright.sync_api import sync_playwright
import json
from datetime import datetime, timedelta
import os

def check_cru_availability(guests=2):
    """Check availability at Cru restaurant"""
    results = {
        'restaurant': 'Cru',
        'checked_at': datetime.now().isoformat(),
        'available_dates': []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to Cru's booking page
            page.goto('https://cru.superbexperience.com/')
            page.wait_for_load_state('networkidle')
            
            # Click on a la carte option
            page.wait_for_selector('text=A La carte')
            page.click('text=A La carte')
            page.wait_for_load_state('networkidle')
            
            # Select number of guests
            page.wait_for_selector('text=Number of guests')
            # Assuming we need to click multiple times to increase guest count
            for _ in range(guests-1):  # -1 because default is usually 1
                page.click('button:has-text("+")')
            page.wait_for_load_state('networkidle')
            
            # Click continue to get to date selection
            page.click('button:has-text("Continue")')
            page.wait_for_load_state('networkidle')
            
            # Try to find available dates
            available_dates = page.query_selector_all('button[data-testid="date-picker-day"]:not([disabled])')
            
            if available_dates:
                # Check each available date
                for date_elem in available_dates[:5]:  # Limit to first 5 dates
                    date_text = date_elem.get_attribute('aria-label')
                    date_elem.click()
                    page.wait_for_load_state('networkidle')
                    
                    # Get available times
                    time_slots = page.query_selector_all('button:has-text(":")')
                    times = [slot.inner_text() for slot in time_slots]
                    
                    if times:
                        results['available_dates'].append({
                            'date': date_text,
                            'times': times
                        })
            
        except Exception as e:
            print(f"Error checking availability: {str(e)}")
        finally:
            browser.close()
    
    return results

def save_results(results):
    """Save results to a JSON file"""
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Save to timestamped file
    filename = f"results/availability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save to latest file
    with open('results/latest.json', 'w') as f:
        json.dump(results, f, indent=2)

def main():
    # Check for 2 guests by default
    results = check_cru_availability(guests=2)
    
    # Save results
    save_results(results)
    
    # Print summary
    print(f"Checked {results['restaurant']} at {results['checked_at']}")
    print(f"Found {len(results['available_dates'])} dates with availability")
    
    # If we found availability, print details
    if results['available_dates']:
        print("\nAvailable dates:")
        for date_info in results['available_dates']:
            print(f"\n{date_info['date']}:")
            print(f"Times: {', '.join(date_info['times'])}")

if __name__ == '__main__':
    main()
