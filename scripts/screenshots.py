"""Capture real screenshots of the running SPA for the README (spec §36)."""
import os
import time

from playwright.sync_api import sync_playwright

BASE = os.environ.get("SPA_URL", "http://localhost:4173")
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots")
os.makedirs(OUT, exist_ok=True)


def shot(page, name):
    page.wait_for_timeout(700)
    page.screenshot(path=os.path.join(OUT, f"{name}.png"))
    print("captured", name)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 860})

    page.goto(BASE, wait_until="networkidle")
    shot(page, "01-login")

    page.fill('input[type="email"]', "demo@example.com")
    page.fill('input[type="password"]', "demopassword123")
    page.click('button[type="submit"]')
    page.wait_for_selector("text=Dashboard", timeout=10000)
    shot(page, "02-dashboard")

    page.click("text=Create")
    page.wait_for_selector("text=Create research", timeout=5000)
    page.fill('input', "Note-taking app for students")
    textareas = page.query_selector_all("textarea")
    textareas[0].fill("A smart note-taking app that summarizes lecture recordings for students.")
    textareas[1].fill("University students who record lectures and revise from notes.")
    textareas[2].fill("Decide whether to prioritize transcription accuracy or summary quality.")
    shot(page, "03-create-research")

    # Open the seeded completed project from the dashboard.
    page.click("text=Dashboard")
    page.wait_for_selector("text=Placement Prep AI", timeout=5000)
    page.click("text=Placement Prep AI")
    page.wait_for_selector("text=Overview", timeout=8000)
    shot(page, "04-research-overview")

    page.click("button.tab:has-text('Personas')")
    page.wait_for_selector(".persona-card", timeout=8000)
    shot(page, "05-persona-explorer")

    page.click("button.tab:has-text('Insights')")
    page.wait_for_selector("text=Executive summary", timeout=8000)
    shot(page, "06-insights")

    # Persona chat
    page.click("button.tab:has-text('Personas')")
    page.wait_for_selector(".persona-card", timeout=8000)
    page.click("text=Chat with")
    page.wait_for_selector(".chat-window", timeout=8000)
    page.fill(".chat-input input", "What would make you actually use this product?")
    page.click(".chat-input button")
    page.wait_for_selector(".bubble-persona", timeout=8000)
    shot(page, "07-persona-chat")

    browser.close()
    print("done")
