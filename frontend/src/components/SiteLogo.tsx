interface SiteLogoProps {
  /** 徽章直径（px）。着陆页用大号（110），侧栏用小号（40）。 */
  size?: number
}

/**
 * 网站复古圆形徽章 Logo（PRD A14）：环形排布标语 + 中心戴眼镜人物黑白剪影。
 * 风格参考设计稿徽章：黑底细金环 + 米白线条人像，着陆页与侧栏品牌复用；
 * 纯内联 SVG，不引入图片资源，随主题缩放。
 */
export function SiteLogo({ size = 96 }: SiteLogoProps) {
  return (
    <svg
      className="site-logo"
      width={size}
      height={size}
      viewBox="0 0 120 120"
      role="img"
      aria-label="未完成的页 logo"
    >
      <defs>
        <path
          id="site-logo-ring"
          d="M 60,60 m -46,0 a 46,46 0 1,1 92,0 a 46,46 0 1,1 -92,0"
        />
      </defs>

      {/* 徽章底与外环 */}
      <circle cx="60" cy="60" r="59" fill="#14110b" stroke="#b08d57" strokeWidth="2.5" />
      <circle
        cx="60"
        cy="60"
        r="53"
        fill="none"
        stroke="rgba(241, 230, 205, 0.28)"
        strokeWidth="1"
        strokeDasharray="1 5"
      />

      {/* 环形标语：这里只放我真正在乎的文字 · 未完成的页 */}
      <text
        fill="#f1e6cd"
        fontSize="10.5"
        fontFamily="'Kaiti SC','STKaiti','楷体',serif"
        letterSpacing="2.5"
      >
        <textPath href="#site-logo-ring" startOffset="0">
          这里只放我真正在乎的文字 · 未完成的页
        </textPath>
      </text>

      {/* 中心：戴眼镜人物黑白剪影 */}
      <g stroke="#f1e6cd" strokeWidth="1.8" fill="none" strokeLinecap="round">
        {/* 头发（上半圆填充） */}
        <path d="M 43.5 64 A 16.5 16.5 0 0 1 76.5 64 Z" fill="#f1e6cd" stroke="none" />
        {/* 脸 */}
        <circle cx="60" cy="64" r="16.5" />
        {/* 眼镜：镜圈 + 鼻梁 + 镜腿 */}
        <circle cx="52.5" cy="64" r="5" />
        <circle cx="67.5" cy="64" r="5" />
        <path d="M 57.5 64 L 62.5 64" />
        <path d="M 47.5 64 L 43.5 62" />
        <path d="M 72.5 64 L 76.5 62" />
        {/* 嘴 */}
        <path d="M 55.5 73 Q 60 75.5 64.5 73" />
        {/* V 领 */}
        <path d="M 46 90 L 60 79 L 74 90" />
      </g>
    </svg>
  )
}
