import { describe, expect, it } from 'vitest'

import { categoryLabel, formatDateTime, readingMinutes } from './format'

describe('formatDateTime', () => {
  it('把 ISO 时间格式化为本地 "YYYY-MM-DD HH:mm"', () => {
    // 使用本地时区构造，避免 CI/本机时区差异
    const local = new Date(2026, 9, 6, 14, 5) // 2026-10-06 14:05
    expect(formatDateTime(local.toISOString())).toBe('2026-10-06 14:05')
  })

  it('非法时间串原样返回', () => {
    expect(formatDateTime('not-a-date')).toBe('not-a-date')
  })
})

describe('categoryLabel', () => {
  it('映射三个内置分类', () => {
    expect(categoryLabel('project')).toBe('项目')
    expect(categoryLabel('daily')).toBe('日常')
    expect(categoryLabel('diary')).toBe('日记')
  })

  it('未知分类原样返回', () => {
    expect(categoryLabel('unknown')).toBe('unknown')
  })
})

describe('readingMinutes', () => {
  it('按 300 字/分钟估算，向上取整', () => {
    expect(readingMinutes('字'.repeat(300))).toBe(1)
    expect(readingMinutes('字'.repeat(301))).toBe(2)
    expect(readingMinutes('字'.repeat(750))).toBe(3)
  })

  it('空白不计入字数，且至少 1 分钟', () => {
    expect(readingMinutes('')).toBe(1)
    expect(readingMinutes('   \n  ')).toBe(1)
  })
})
