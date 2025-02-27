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
        # Launch browser in headless mode with required arguments for CI
        browser = p.chromium.launch(
            headless=True,  # Must be headless for CI
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
        )
        page = context.new_page()
        
        try:
            print("Starting availability check...")
            # Set extra headers to look more like a real browser
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,nb;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Try to navigate directly to the booking page
            print("Navigating to booking page...")
            page.goto('https://cru.superbexperience.com/booking', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(2)
            page.screenshot(path="results/1_initial_page.png")
            
            print("Current URL:", page.url)
            print("Page content length:", len(page.content()))
            
            # Wait for and click a la carte option if needed
            if page.is_visible('text=A La carte'):
                print("Clicking A La Carte...")
                page.click('text=A La carte')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path="results/2_after_alacarte.png")
            
            # Select number of guests if the selector is visible
            if page.is_visible('text=Number of guests'):
                print(f"Selecting {guests} guests...")
                for _ in range(guests-1):
                    page.click('button:has-text("+")')
                    time.sleep(0.5)
                page.wait_for_load_state('networkidle')
                page.screenshot(path="results/3_after_guests.png")
                
                # Click continue
                if page.is_visible('button:has-text("Continue")'):
                    page.click('button:has-text("Continue")')
                    page.wait_for_load_state('networkidle')
                    time.sleep(2)
                    page.screenshot(path="results/4_after_continue.png")
            
            # Check if we can find the calendar
            if page.is_visible('[data-testid="date-picker-day"]'):
                print("Calendar found, checking dates...")
                page.screenshot(path="results/5_calendar_visible.png")
                
                # Get all dates
                dates = page.query_selector_all('button[data-testid="date-picker-day"]')
                print(f"Found {len(dates)} date elements")
                
                for date in dates:
                    try:
                        date_text = date.get_attribute('aria-label')
                        disabled = date.get_attribute('disabled')
                        print(f"Date: {date_text}, Disabled: {disabled}")
                        
                        if not date_text or disabled is not None:
                            continue
                        
                        print(f"Checking {date_text}...")
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
            else:
                print("Calendar not found!")
                page.screenshot(path="results/error_no_calendar.png")
            
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
