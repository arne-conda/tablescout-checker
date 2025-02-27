from playwright.sync_api import sync_playwright
import json
from datetime import datetime, timedelta
import os
import time

def check_cru_availability(guests=2):
    """Check availability at Cru restaurant"""
    results = {
        'restaurant': 'Cru',
        'checked_at': datetime.now().isoformat(),
        'available_dates': []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("Starting availability check...")
            # Navigate to Cru's booking page
            page.goto('https://cru.superbexperience.com/')
            page.wait_for_load_state('networkidle')
            page.screenshot(path="results/1_initial_page.png")
            
            # Click on a la carte option
            print("Selecting A La Carte...")
            page.wait_for_selector('text=A La carte', timeout=30000)
            page.screenshot(path="results/2_before_alacarte.png")
            page.click('text=A La carte')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path="results/3_after_alacarte.png")
            
            # Select number of guests
            print(f"Selecting {guests} guests...")
            page.wait_for_selector('text=Number of guests', timeout=30000)
            page.screenshot(path="results/4_before_guests.png")
            # Assuming we need to click multiple times to increase guest count
            for _ in range(guests-1):  # -1 because default is usually 1
                page.click('button:has-text("+")')
                time.sleep(0.5)
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path="results/5_after_guests.png")
            
            # Click continue to get to date selection
            continue_button = page.get_by_role("button", name="Continue")
            print("HTML around continue button:", continue_button.evaluate('el => el.outerHTML'))
            continue_button.click()
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path="results/6_after_continue.png")
            
            # Wait for calendar to be visible
            page.wait_for_selector('[data-testid="date-picker-day"]', timeout=30000)
            page.screenshot(path="results/7_calendar_visible.png")
            
            # Get all dates in the calendar
            print("Checking dates...")
            for month in range(2):  # Check current and next month
                print(f"Checking month {month + 1}")
                dates = page.query_selector_all('button[data-testid="date-picker-day"]')
                print(f"Found {len(dates)} date elements")
                
                for date in dates:
                    try:
                        # Get the date text
                        date_text = date.get_attribute('aria-label')
                        disabled = date.get_attribute('disabled')
                        print(f"Found date: {date_text}, disabled: {disabled}")
                        
                        if not date_text or disabled is not None:
                            continue
                            
                        print(f"Checking {date_text}...")
                        # Click the date
                        date.click()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)
                        
                        # Get available times
                        time_slots = page.query_selector_all('button:has-text(":")')
                        times = [slot.inner_text() for slot in time_slots]
                        
                        if times:
                            print(f"Found times for {date_text}: {times}")
                            results['available_dates'].append({
                                'date': date_text,
                                'times': times
                            })
                            page.screenshot(path=f"results/time_slots_{date_text.replace(' ', '_')}.png")
                    except Exception as e:
                        print(f"Error checking date {date_text}: {str(e)}")
                        continue
                
                if month == 0:  # Only try next month on first iteration
                    # Click next month if available
                    next_month = page.query_selector('button[aria-label="Next month"]')
                    if next_month:
                        print("Clicking next month")
                        next_month.click()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)
                        page.screenshot(path=f"results/next_month_{month}.png")
                    else:
                        print("No next month button found")
            
        except Exception as e:
            print(f"Error checking availability: {str(e)}")
            page.screenshot(path="results/error_state.png")
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
    
    # Print summary
    print(f"\nResults saved:")
    print(f"Found {len(results['available_dates'])} dates with availability")
    if results['available_dates']:
        print("\nAvailable dates:")
        for date_info in results['available_dates']:
            print(f"\n{date_info['date']}:")
            print(f"Times: {', '.join(date_info['times'])}")

def main():
    # Check for 2 guests by default
    results = check_cru_availability(guests=2)
    
    # Save results
    save_results(results)

if __name__ == '__main__':
    main()
