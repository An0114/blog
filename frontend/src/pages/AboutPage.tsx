import type { ReactNode } from 'react'

import { SiteLogo } from '../components/SiteLogo'

/**
 * 关于我（/about）：博主简介页（静态页，无后端依赖；文案在 SITE 常量中可自行修改）。
 * PRD A15：无标签墙，展示多种联系方式（平台 + 账号 + 链接，图标为内联 SVG，不引入图标库）。
 */

const SITE = {
  quote: '有些文字只写给自己，有些可以被世界看见。',
  intro:
    '你好，欢迎来到「未完成的页」。这里是我存放真正在乎的文字的地方——开发的项目、生活的日常，与写给自己的日记。',
  positioning: ['长期写作', '私人笔记', '阅读痕迹', '生活片段'],
}

interface Contact {
  name: string
  account: string
  href: string
}

const CONTACTS: Contact[] = [
  { name: '邮箱', account: 'hello@example.com', href: 'mailto:hello@example.com' },
  { name: 'B站', account: '未完成的页', href: 'https://space.bilibili.com' },
  { name: '微博', account: '未完成的页', href: 'https://weibo.com' },
  { name: '微信', account: '未完成的页', href: '' },
]

/** 内联 SVG 线条图标（随主题色变化，用 currentColor）。 */
function ContactIcon({ kind }: { kind: 'mail' | 'play' | 'chat' | 'at' }) {
  const paths: Record<string, ReactNode> = {
    mail: (
      <path d="M3 6h18v12H3z M3 7l9 6 9-6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    ),
    play: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M10 9.5l5 2.5-5 2.5z" fill="currentColor" />
      </>
    ),
    chat: (
      <path
        d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-4 3v-3H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    ),
    at: (
      <>
        <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M16 12a4 4 0 0 1-8 0 4 4 0 0 1 8 0zm0 0v2a2 2 0 0 0 4 0v-2c0-3.3-3-6-6-6s-6 2.7-6 6 2.7 6 6 6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </>
    ),
  }
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      {paths[kind]}
    </svg>
  )
}

export function AboutPage() {
  return (
    <div className="page">
      <div className="about-hero">
        <SiteLogo size={96} />
        <h1>未完成的页</h1>
        <p className="about-quote">{SITE.quote}</p>
      </div>
      <p>{SITE.intro}</p>
      <p className="post-card-meta">
        {SITE.positioning.map((item) => (
          <span key={item} className="badge">
            {item}
          </span>
        ))}
      </p>
      <h2>联系方式</h2>
      <div className="contact-grid">
        {CONTACTS.map((c) => {
          const body = (
            <>
              <span className="contact-icon">
                <ContactIcon kind={c.name === '邮箱' ? 'mail' : c.name === 'B站' ? 'play' : c.name === '微信' ? 'chat' : 'at'} />
              </span>
              <span className="contact-name">{c.name}</span>
              <span className="contact-account">{c.account}</span>
            </>
          )
          return c.href ? (
            <a key={c.name} className="contact-card" href={c.href} target="_blank" rel="noreferrer">
              {body}
            </a>
          ) : (
            <div key={c.name} className="contact-card">
              {body}
            </div>
          )
        })}
      </div>
    </div>
  )
}
