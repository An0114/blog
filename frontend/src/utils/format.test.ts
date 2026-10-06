import { describe, expect, it } from 'vitest'

import { categoryLabel, formatDateTime } from './format'

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
