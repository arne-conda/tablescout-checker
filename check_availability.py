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
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
        )
        page = context.new_page()
        
        try:
            print("Starting availability check...")
            # Navigate to the page
            page.goto('https://cru.superbexperience.com/', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path="results/1_before_cookies.png")
            
            # Handle cookie consent
            print("Looking for cookie consent...")
            if page.is_visible('button:has-text("ACCEPT")'):
                print("Accepting cookies...")
                page.click('button:has-text("ACCEPT")')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path="results/2_after_cookies.png")
            else:
                print("No cookie consent found")
            
            # Click "Reserve your table" button
            print("Looking for 'Reserve your table' button...")
            reserve_button_selectors = [
                'button:has-text("Reserve your table")',
                'button:has-text("RESERVE YOUR TABLE")',
                'a:has-text("Reserve your table")',
                'a:has-text("RESERVE YOUR TABLE")'
            ]
            
            for selector in reserve_button_selectors:
                if page.is_visible(selector):
                    print(f"Found and clicking reserve button with selector: {selector}")
                    page.click(selector)
                    page.wait_for_load_state('networkidle')
                    time.sleep(2)
                    page.screenshot(path="results/3_after_reserve.png")
                    break
            else:
                print("Reserve button not found with common selectors, trying to locate it...")
                # Print all button texts for debugging
                buttons = page.query_selector_all('button, a')
                print("Available buttons/links:")
                for button in buttons:
                    print(f"Text: '{button.inner_text()}', Tag: {button.evaluate('el => el.tagName')}")
            
            # Wait for and click a la carte option
            print("Waiting for A La Carte option...")
            page.wait_for_selector('text=A La carte', timeout=30000)
            print("Clicking A La Carte...")
            page.click('text=A La carte')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path="results/4_after_alacarte.png")
            
            # Select number of guests
            print(f"Selecting {guests} guests...")
            page.wait_for_selector('text=Number of guests', timeout=30000)
            for _ in range(guests-1):
                page.click('button:has-text("+")')
                time.sleep(0.5)
            page.wait_for_load_state('networkidle')
            page.screenshot(path="results/5_after_guests.png")
            
            # Click continue
            print("Clicking continue...")
            page.click('button:has-text("Continue")')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path="results/6_after_continue.png")
            
            # Wait for calendar
            print("Waiting for calendar...")
            page.wait_for_selector('[data-testid="date-picker-day"]', timeout=30000)
            page.screenshot(path="results/7_calendar_visible.png")
            
            # Check dates for current and next month
            for month in range(2):
                print(f"Checking month {month + 1}")
                dates = page.query_selector_all('button[data-testid="date-picker-day"]')
                print(f"Found {len(dates)} dates")
                
                for date in dates:
                    try:
                        date_text = date.get_attribute('aria-label')
                        disabled = date.get_attribute('disabled')
                        print(f"Checking date: {date_text}, disabled: {disabled}")
                        
                        if not date_text or disabled is not None:
                            continue
                        
                        date.click()
                        page.wait_for_load_state('networkidle')
                        time.sleep(1)
                        
                        time_slots = page.query_selector_all('button:has-text(":")')
                        times = [slot.inner_text() for slot in time_slots]
                        
                        if times:
                            print(f"Found times for {date_text}: {times}")
                            results['available_dates'].append({
                                'date': date_text,
                                'times': times
                            })
                    except Exception as e:
                        print(f"Error checking date {date_text}: {str(e)}")
                        continue
                
                if month == 0:
                    next_month = page.query_selector('button[aria-label="Next month"]')
                    if next_month:
                        print("Moving to next month")
                        next_month.click()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)
                        page.screenshot(path=f"results/8_next_month.png")
                    else:
                        print("No next month button found")
            
        except Exception as e:
            print(f"Error during check: {str(e)}")
            page.screenshot(path="results/error_state.png")
        finally:
            browser.close()
    
    return results

def save_results(results):
    """Save results to a JSON file"""
    os.makedirs('results', exist_ok=True)
    
    filename = f"results/availability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    with open('results/latest.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved:")
    print(f"Found {len(results['available_dates'])} dates with availability")
    if results['available_dates']:
        print("\nAvailable dates:")
        for date_info in results['available_dates']:
            print(f"\n{date_info['date']}:")
            print(f"Times: {', '.join(date_info['times'])}")

def main():
    results = check_cru_availability(guests=2)
    save_results(results)

if __name__ == '__main__':
    main()
