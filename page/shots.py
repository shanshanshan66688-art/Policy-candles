"""Capture section screenshots in one session: python3 shots.py PAGE [width] [scheme] [lang] [prefix] [sel1,sel2,...]"""
import sys, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

D3 = Path('/opt/npm-tools/node_modules/d3/dist/d3.min.js').read_text()
OUT = Path('/home/claude/policy_bt/page/shots')
OUT.mkdir(exist_ok=True)


async def main():
    f = Path(sys.argv[1]).resolve()
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 1280
    scheme = sys.argv[3] if len(sys.argv) > 3 else 'light'
    lang = sys.argv[4] if len(sys.argv) > 4 else 'zh'
    prefix = sys.argv[5] if len(sys.argv) > 5 else 's'
    sels = sys.argv[6].split(',') if len(sys.argv) > 6 else ['.mast', '#overview', '#industry', '#plans', '#backtest', '#data']
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': width, 'height': 1000}, color_scheme=scheme, device_scale_factor=1)
        page = await ctx.new_page()
        errs = []
        page.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') and 'Failed to load resource' not in m.text else None)
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
        await page.add_init_script(f"try{{localStorage.setItem('pc.lang', JSON.stringify('{lang}'))}}catch(e){{}}")
        await page.goto('file://' + str(f))
        await page.wait_for_timeout(900)
        for i, s in enumerate(sels):
            el = await page.query_selector(s)
            if not el:
                print('missing', s)
                continue
            await el.scroll_into_view_if_needed()
            await page.wait_for_timeout(200)
            await el.screenshot(path=str(OUT / f'{prefix}_{i}.png'))
        sw = await page.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
        print('scroll/client width', sw, 'errors:', errs[:10])
        await b.close()

asyncio.run(main())
