import MarkdownIt from 'markdown-it'

// html: false чтоб из шага не прилетел левый html
const md = new MarkdownIt({ html: false, linkify: true, breaks: false, typographer: true })

const defaultLink = md.renderer.rules.link_open
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  tokens[idx]!.attrSet('target', '_blank')
  tokens[idx]!.attrSet('rel', 'noopener noreferrer nofollow')
  return defaultLink ? defaultLink(tokens, idx, options, env, self) : self.renderToken(tokens, idx, options)
}

export function renderMarkdown(src: string): string {
  return md.render(src || '')
}

export function stripMarkdown(src: string): string {
  return (src || '').replace(/```[\s\S]*?```/g, ' ').replace(/[#>*_`~[\]()!-]+/g, ' ').replace(/\s+/g, ' ').trim()
}
