import { defineConfig } from 'vitepress'

// V0.1: reserved for the V0.2 Markdown migration. Not used by build:site yet.
export default defineConfig({
  lang: 'zh-CN',
  title: 'CSAPP 中文实践教程',
  description: '从计算机系统原理到可验证的工程实践',
  base: '/CSAPP-tutorial/',
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '学习路线', link: '/guides/learning-path' },
      { text: '实验', link: '/labs/' },
    ],
    sidebar: [
      { text: '入门', items: [{ text: '学习路线', link: '/guides/learning-path' }] },
      { text: '实验', items: [{ text: '实验总览', link: '/labs/' }] },
    ],
    search: { provider: 'local' },
  },
})

