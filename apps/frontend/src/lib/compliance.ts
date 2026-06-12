export const SENSITIVE_WORDS = [
  '处方药', '诊断', '治疗', '治愈', '疗效', '根治', '最好', '第一', '唯一',
  '绝对', '保证', '承诺', '无效退款', '国家级', '最高级', '顶级',
]

export function highlightCompliance(text: string): { html: string; hits: number } {
  let hits = 0
  const pattern = new RegExp(
    `(${SENSITIVE_WORDS.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
    'gi'
  )
  const html = text.replace(pattern, (m) => {
    hits++
    return `<mark class="bg-yellow-200 dark:bg-yellow-700 rounded px-0.5">${m}</mark>`
  })
  return { html, hits }
}
