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
        # Use more browser-like settings
        browser = p.chromium.launch(
            headless=False,  # Try with visible browser first
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
        )
        page = context.new_page()
        
        try:
            print("Starting availability check...")
            # Navigate with extra headers
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })
            
            # Navigate to Cru's booking page
            page.goto('https://cru.superbexperience.com/', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            time.sleep(5)  # Give it extra time
            page.screenshot(path="results/1_initial_page.png")
            
            # Rest of the code remains the same...
            print("Page title:", page.title())
            print("Current URL:", page.url)
            
            if "403" in page.url or "forbidden" in page.url.lower():
                print("Got blocked with 403 - trying alternative approach...")
                # Try mobile user agent
                context.close()
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                    viewport={'width': 375, 'height': 812},
                )
                page = context.new_page()
                page.goto('https://cru.superbexperience.com/', wait_until='networkidle')
                page.wait_for_load_state('networkidle')
                time.sleep(5)
                page.screenshot(path="results/1_initial_page_mobile.png")
            
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

def main():
    results = check_cru_availability(guests=2)
    save_results(results)

if __name__ == '__main__':
    main()
