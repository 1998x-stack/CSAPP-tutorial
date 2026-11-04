import { defineConfig } from 'vitepress'
import courseManifest from '../../courses.json'

const chapters = courseManifest.chapters.map((chapter) => ({
  text: chapter.num + ' · ' + chapter.title,
  link: '/chapters/' + chapter.slug,
}))

const groups = [
  { text: '系统入门与数据表示', range: [0, 3] },
  { text: '机器级程序与处理器', range: [3, 10] },
  { text: '内存、链接与异常', range: [10, 18] },
  { text: '系统 I/O 与并发', range: [18, 23] },
  { text: '实验与综合拓展', range: [23, 28] },
].map(({ text, range }) => ({
  text,
  collapsed: false,
  items: chapters.slice(range[0], range[1]),
}))

export default defineConfig({
  lang: 'zh-CN',
  title: 'CSAPP 中文实践教程',
  description: '从数据表示到系统编程，一起理解计算机如何运行',
  base: '/CSAPP-tutorial/',
  cleanUrls: false,
  lastUpdated: true,
  sitemap: { hostname: 'https://1998x-stack.github.io/CSAPP-tutorial/' },
  head: [
    ['meta', { name: 'theme-color', content: '#247c65' }],
    ['meta', { name: 'description', content: '28 章深入理解计算机系统中文教程与可验证示例' }],
  ],
  themeConfig: {
    logo: '/logo.svg',
    nav: [
      { text: '首页', link: '/' },
      { text: '全部章节', link: '/chapters/' },
      { text: '学习路线', link: '/guides/learning-path' },
      { text: '实践实验', link: '/labs/' },
    ],
    sidebar: {
      '/chapters/': groups,
      '/guides/': [
        { text: '学习路线', link: '/guides/learning-path' },
        { text: '内容质量规范', link: '/guides/content-style' },
      ],
      '/labs/': [
        { text: '实验总览', link: '/labs/' },
        { text: '实验练习与验收', link: '/labs/exercises' },
      ],
    },
    outline: { level: [2, 3], label: '本页目录' },
    sidebarMenuLabel: '章节导航',
    returnToTopLabel: '返回顶部',
    docFooter: { prev: '上一节', next: '下一节' },
    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: { buttonText: '搜索课程', buttonAriaLabel: '搜索课程' },
              modal: {
                displayDetails: '显示详情',
                resetButtonTitle: '清除',
                backButtonTitle: '返回',
                noResultsText: '没有找到相关内容',
                footer: { selectText: '选择', navigateText: '导航', closeText: '关闭' },
              },
            },
          },
        },
      },
    },
    socialLinks: [{ icon: 'github', link: 'https://github.com/1998x-stack/CSAPP-tutorial' }],
    editLink: {
      pattern: 'https://github.com/1998x-stack/CSAPP-tutorial/edit/main/docs/:path',
      text: '编辑此页',
    },
    footer: {
      message: '独立中文教学项目，非 CS:APP 或 CMU 官方出版物。',
      copyright: '源码与自有内容许可见仓库 LICENSE，第三方资料按各自许可使用。',
    },
  },
})
