import { test, expect } from '@playwright/test'

const base = '/CSAPP-tutorial/'

test('homepage links to first chapter and chapter list', async ({ page }) => {
  await page.goto(base)
  await expect(page.getByRole('heading', { name: /CSAPP 中文实践教程/ })).toBeVisible()
  await page.getByRole('link', { name: '从第一章开始' }).click()
  await expect(page).toHaveURL(/\/chapters\/01-introduction\.html$/)
  await expect(page.locator('h1')).toContainText('第一章')
  await expect(page.locator('.VPSidebar')).toBeVisible()
})

test('all 28 canonical chapter routes are reachable', async ({ page }) => {
  const routes = [
    '01-introduction','02-integers','03-floating-point',
    '04-machine-basics','05-machine-control-flow','06-procedures-and-stack',
    '07-data-and-memory-layout','08-isa-design','09-pipelining',
    '10-performance-optimization','11-memory-hierarchy','12-cache',
    '13-static-linking','14-dynamic-linking','15-exceptions-and-processes',
    '16-signals','17-virtual-memory','18-memory-allocation',
    '19-system-io','20-network-fundamentals','21-network-advanced',
    '22-thread-basics','23-concurrency-patterns','24-classic-labs-i',
    '25-classic-labs-ii','26-proxy-lab','27-modern-systems','28-web-server',
  ]
  for (const route of routes) {
    const res = await page.goto(base + 'chapters/' + route + '.html')
    expect(res?.ok(), route).toBeTruthy()
    await expect(page.locator('.vp-doc h1')).toBeVisible()
  }
})

test('legacy chapter URLs redirect to new routes', async ({ page }) => {
  await page.goto(base + '01.html')
  await expect(page).toHaveURL(/\/chapters\/01-introduction\.html$/)
  await page.goto(base + '28.html')
  await expect(page).toHaveURL(/\/chapters\/28-web-server\.html$/)
})

test('mobile chapter navigation and reading are usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(base + 'chapters/03-floating-point.html')
  await expect(page.locator('.vp-doc h1')).toBeVisible()
  await expect(page.locator('body')).not.toHaveCSS('overflow-x', 'scroll')
})


test('local search can find systems concepts', async ({ page }) => {
  await page.goto(base)
  await page.locator('.VPNavBarSearchButton').click()
  const input = page.locator('.VPLocalSearchBox input')
  await expect(input).toBeVisible()
  await input.fill('虚拟内存')
  await expect(page.locator('.VPLocalSearchBox a[href*="17-virtual-memory"]').first()).toBeVisible()
})
