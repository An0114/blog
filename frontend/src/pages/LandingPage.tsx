import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { SiteLogo } from '../components/SiteLogo'

/**
 * 着陆页（PRD A14）：网站第一个页面。
 * 鼠标向下滚动（或触摸上滑）时淡出，首页以淡入 + 右侧滑入过渡进入。
 */
const POSITIONING = ['长期写作', '私人笔记', '阅读痕迹', '生活片段']

export function LandingPage() {
  const navigate = useNavigate()
  const [leaving, setLeaving] = useState(false)
  const leavingRef = useRef(false)

  useEffect(() => {
    const goHome = () => {
      if (leavingRef.current) return
      leavingRef.current = true
      setLeaving(true)
      // 等待淡出动画完成后进入首页
      window.setTimeout(() => navigate('/home'), 700)
    }

    const onWheel = (e: WheelEvent) => {
      if (e.deltaY > 0) goHome()
    }

    // 移动端：触摸上滑触发
    let touchStartY = 0
    const onTouchStart = (e: TouchEvent) => {
      touchStartY = e.touches[0]?.clientY ?? 0
    }
    const onTouchEnd = (e: TouchEvent) => {
      const dy = touchStartY - (e.changedTouches[0]?.clientY ?? touchStartY)
      if (dy > 40) goHome()
    }

    window.addEventListener('wheel', onWheel, { passive: true })
    window.addEventListener('touchstart', onTouchStart, { passive: true })
    window.addEventListener('touchend', onTouchEnd, { passive: true })
    return () => {
      window.removeEventListener('wheel', onWheel)
      window.removeEventListener('touchstart', onTouchStart)
      window.removeEventListener('touchend', onTouchEnd)
    }
  }, [navigate])

  return (
    <div className={`landing${leaving ? ' landing-leaving' : ''}`}>
      <div className="landing-decor landing-note">有些文字只写给自己，<br />有些可以被世界看见。</div>
      <div className="landing-decor landing-calendar">2026</div>
      <div className="landing-decor landing-notebook">未完成的页</div>

      <div className="landing-center">
        <SiteLogo size={110} />
        <h1 className="landing-title">未完成的页</h1>
        <p className="landing-slogan">这里只放我真正在乎的文字</p>
        <p className="landing-positioning">
          {POSITIONING.map((item) => (
            <span key={item} className="badge">
              {item}
            </span>
          ))}
        </p>
        <p className="landing-hint">进入后将看到你的写作后台与公开文章</p>
        <p className="landing-scroll">↓ 向下滚动进入</p>
      </div>
    </div>
  )
}
