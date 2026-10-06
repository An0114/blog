/**
 * 关于我（/about）：博主简介页（静态页，无后端依赖；文案在 SITE 常量中可自行修改）。
 * 参考 UI 设计图"未完成的页"个人板块：头像 + 引用 + 定位 + 标签墙。
 */

const SITE = {
  quote: '有些文字只写给自己，有些可以被世界看见。',
  intro:
    '你好，欢迎来到「未完成的页」。这里是我存放真正在乎的文字的地方——开发的项目、生活的日常，与写给自己的日记。',
  positioning: ['长期写作', '私人笔记', '阅读痕迹', '生活片段'],
  tags: ['项目', '生活', '阅读', '情绪'],
}

export function AboutPage() {
  return (
    <div className="page">
      <div className="about-hero">
        <span className="avatar">页</span>
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
      <h2>标签墙</h2>
      <p className="post-card-meta">
        {SITE.tags.map((tag) => (
          <span key={tag} className="badge">
            {tag}
          </span>
        ))}
      </p>
    </div>
  )
}
