/**
 * 展示格式化纯函数：保持组件内无内联格式化逻辑，便于单测。
 */

/** ISO 时间串 → "2026-10-06 14:30"（本地时区）。 */
export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** 分类 → 中文展示名。 */
export function categoryLabel(category: string): string {
  switch (category) {
    case 'project':
      return '项目'
    case 'daily':
      return '日常'
    case 'diary':
      return '日记'
    default:
      return category
  }
}
