interface SiteLogoProps {
  /** 徽章直径（px）。着陆页用大号（96），侧栏用小号（40）。 */
  size?: number
}

/**
 * 网站圆形 Logo（PRD A14）：古铜金渐变圆形徽章 + "页"字。
 * 来自着陆页设计图"未完成的页"上方的圆形徽章，着陆页与侧栏品牌复用。
 */
export function SiteLogo({ size = 96 }: SiteLogoProps) {
  return (
    <span
      className="site-logo"
      style={{ width: size, height: size, fontSize: size * 0.42 }}
      aria-label="未完成的页 logo"
    >
      页
    </span>
  )
}
