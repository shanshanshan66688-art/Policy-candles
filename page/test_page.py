"""Render the page headlessly with the local d3 build and capture screenshots + console errors."""
import sys, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

D3 = Path('/opt/npm-tools/node_modules/d3/dist/d3.min.js').read_text()
OUT = Path('/home/claude/policy_bt/page/shots')
OUT.mkdir(exist_ok=True)


async def run(page_file, tag, width=1280, scheme='light', actions=None, full=True, clip_sel=None, lang=None):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': width, 'height': 900}, color_scheme=scheme, device_scale_factor=1)
        page = await ctx.new_page()
        errs = []
        page.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        page.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))

        async def route(r):
            u = r.request.url
            if 'd3.min.js' in u:
                await r.fulfill(body=D3, content_type='application/javascript')
            elif u.startswith('file://'):
                await r.continue_()
            else:
                await r.abort()
        await page.route('**/*', route)
        if lang:
            await page.add_init_script(f"localStorage.setItem('pc.lang', JSON.stringify('{lang}'))")
        await page.goto('file://' + str(page_file))
        await page.wait_for_timeout(800)
        if actions:
            await actions(page)
        if clip_sel:
            el = await page.query_selector(clip_sel)
            await el.screenshot(path=str(OUT / f'{tag}.png'))
        else:
            await page.screenshot(path=str(OUT / f'{tag}.png'), full_page=full)
        sw = await page.evaluate('document.documentElement.scrollWidth')
        await b.close()
        return errs, sw


async def main():
    f = Path(sys.argv[1]).resolve()
    which = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if which in ('all', 'desk'):
        errs, sw = await run(f, 'desk_light', 1280, 'light')
        print('desk_light', 'scrollWidth', sw, errs[:12])
    if which in ('all', 'dark'):
        errs, sw = await run(f, 'desk_dark', 1280, 'dark')
        print('desk_dark', 'scrollWidth', sw, errs[:12])
    if which in ('all', 'mobile'):
        errs, sw = await run(f, 'mobile', 400, 'light')
        print('mobile', 'scrollWidth', sw, errs[:12])
    if which in ('all', 'en'):
        errs, sw = await run(f, 'desk_en', 1280, 'light', lang='en')
        print('desk_en', 'scrollWidth', sw, errs[:12])
    if which in ('all', 'replay'):
        async def act(page):
            await page.click('#playBtn')
            await page.wait_for_timeout(2500)
        errs, sw = await run(f, 'replay', 1280, 'light', actions=act, clip_sel='#industry')
        print('replay', errs[:12])
    if which in ('all', 'hover'):
        async def act(page):
            el = await page.query_selector('#kwrap svg')
            await el.scroll_into_view_if_needed()
            await page.wait_for_timeout(200)
            bb = await el.bounding_box()
            await page.mouse.move(bb['x'] + bb['width'] * 0.6, bb['y'] + 120)
            await page.wait_for_timeout(300)
        errs, sw = await run(f, 'hover', 1280, 'light', actions=act, clip_sel='#kwrap')
        print('hover', errs[:12])

asyncio.run(main())
