from playwright.sync_api import sync_playwright,expect
import os
import uuid
tag=uuid.uuid4().hex[:8]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    def signup(role):
        page=browser.new_page(viewport={'width':390,'height':820})
        page.goto(os.getenv('CAMPUS_URL', 'http://127.0.0.1:8080'))
        page.get_by_text('New here? Create an account').click()
        page.get_by_label('Your name').fill(role)
        page.get_by_label('Account type').select_option(role)
        if role=='owner': page.get_by_label('Restaurant name').fill('Hostel Kitchen '+tag)
        page.get_by_label('Email').fill(role+tag+'@example.test')
        page.get_by_label('Password').fill('example-pass')
        page.get_by_role('button',name='Create account',exact=True).click()
        return page
    owner=signup('owner')
    owner.get_by_label('Dish name').fill('Masala dosa')
    owner.get_by_label('Price in rupees').fill('65')
    owner.get_by_text('Save dish').click()
    expect(owner.get_by_text('Masala dosa',exact=True)).to_be_visible()
    rider=signup('partner')
    customer=signup('customer')
    customer.get_by_role('combobox').select_option(label='Hostel Kitchen '+tag)
    customer.get_by_label('Add one Masala dosa').click()
    customer.get_by_label('Delivery location').fill('Hostel B, room 12')
    customer.get_by_text('Place order').click()
    expect(customer.get_by_text('Awaiting kitchen')).to_be_visible()
    owner.get_by_role('link',name='Orders').click()
    owner.get_by_text('Accept order').click()
    rider.get_by_text('Confirm pickup').click(timeout=12000)
    rider.get_by_text('Mark delivered').click()
    expect(customer.get_by_text('Delivered',exact=True)).to_be_visible(timeout=12000)
    print('PASS: three mobile browser sessions completed registration, menu creation, checkout, acceptance, pickup, delivery and live tracking.')
