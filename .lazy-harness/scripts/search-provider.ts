/**
 * SearchProvider — AI-first 검색 추상화
 *
 * lazy-harness 가 "검색 알고리즘 직접 구현" 을 떠나 AI 가 검색을 주도하는
 * 모델로 전환하기 위한 단일 인터페이스 (ADR 0024).
 *
 * 3 가지 구현:
 *   - DirectAISearch (default): AI 가 context window 에서 직접 의미론적 매칭.
 *     본 파일은 default 인터페이스 + 단순 fallback 만 정의. 실제 AI 검색은
 *     호출 측 (host AI) 이 grep + Read 로 수행하고 결과를 framework 에
 *     넘기는 방식.
 *
 *   - SubagentSearch (optional, 미구현): Task tool 을 통해 전용 검색 에이전트
 *     위임. 비용/지연 trade-off 시.
 *
 *   - RAGSearch (future, 미구현): 벡터 DB 기반. report-and-knowledge-roadmap.md
 *     의 미래.
 *
 * 본 abstraction 의 목적은 N2 의 IDF/burst/stopwords/ADR-keyword 같은 검색
 * 알고리즘 직접 구현 패턴을 분리하고, 그 자리에 AI 위임을 끼우는 것.
 *
 * 사용 시점:
 *   - N2.5 reference-resolver 가 keyword 매칭 폴백으로 호출
 *   - N3 side-effect / regression / domain-invariant 스캐너가 record 검색에 사용
 *   - N6 drift detector 가 term 충돌 탐지에 사용
 *
 * AI-first 원칙 (ADR 0024 §1):
 *   - 검색 알고리즘 직접 구현 금지
 *   - AGENTS.md 가 AI 에게 "어디서·언제·어떻게 검색" 지시 (grammar)
 *   - 실제 검색 결과 해석은 AI 의 의미론적 판단
 */

import { existsSync, readFileSync, readdirSync, statSync } from 'fs'
import * as path from 'path'

// ─────────────────────────────────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────────────────────────────────

export type Layer = 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr' | 'ssot'

export interface SearchQuery {
  /** 검색 키워드 / 토큰 (AI 가 정한 의미 단위) */
  terms: string[]
  /** 대상 layer 목록. 비우면 모든 layer */
  layers?: Layer[]
  /** 입력 파일 경로 (관련성 판단 컨텍스트) */
  inputFile?: string
  /** 결과 최대 개수 */
  limit?: number
}

export interface SearchResult {
  /** 매치된 record 파일 경로 */
  recordPath: string
  /** record 의 layer */
  layer: Layer
  /** 매치 근거 (어떤 토큰이 어디서 발견됐는지) */
  evidence: Array<{
    term: string
    line?: number
    snippet?: string
  }>
  /** 검색 제공자가 산출한 관련성 점수 (0~1, 의미는 제공자 의존) */
  score: number
  /** 검색 제공자 식별자 ("direct-ai" / "subagent" / "rag") */
  provider: string
}

export interface SearchProvider {
  readonly name: string
  search(query: SearchQuery): Promise<SearchResult[]>
}

// ─────────────────────────────────────────────────────────────────────────
// 공통 헬퍼 — record 디렉토리 walking
// ─────────────────────────────────────────────────────────────────────────

const RECORD_DIRS: Record<Layer, string> = {
  ddd: '.lazy-harness/ddd',
  sdd: '.lazy-harness/sdd',
  bdd: '.lazy-harness/bdd',
  tdd: '.lazy-harness/tdd',
  adr: '.lazy-harness/decisions',
  ssot: '.lazy-harness/ssot'
}

function walkRecordFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      out.push(...walkRecordFiles(full))
    } else if (entry.isFile() && entry.name !== 'README.md') {
      out.push(full)
    }
  }
  return out
}

// ─────────────────────────────────────────────────────────────────────────
// DirectAISearch — default 구현
// ─────────────────────────────────────────────────────────────────────────

/**
 * Default 구현. AI 가 직접 호출하는 환경 (Edit/Read tool 사용) 에서는 본
 * 클래스가 단순 substring 매칭만 수행. AI 가 결과를 보고 의미론적 필터링
 * 한다 (AGENTS.md 의 Layer 매핑 룰 따라).
 *
 * 즉 본 클래스는 "후보 record 를 빠르게 좁히는 prefilter" 역할이지,
 * "관련성 판단" 은 호출자 (AI) 가 한다. 이 책임 분리가 AI-first 의 핵심.
 *
 * N2 의 IDF/burst/stopwords/keyword 같은 매직 상수 0 개.
 */
export class DirectAISearch implements SearchProvider {
  readonly name = 'direct-ai'

  async search(query: SearchQuery): Promise<SearchResult[]> {
    const terms = query.terms.map((t) => t.toLowerCase()).filter((t) => t.length > 0)
    if (terms.length === 0) return []

    const layers = query.layers ?? (Object.keys(RECORD_DIRS) as Layer[])
    const results: SearchResult[] = []

    for (const layer of layers) {
      const files = walkRecordFiles(RECORD_DIRS[layer])
      for (const recordPath of files) {
        let body = ''
        try {
          body = readFileSync(recordPath, 'utf8').toLowerCase()
        } catch {
          continue
        }
        const evidence: SearchResult['evidence'] = []
        for (const term of terms) {
          if (body.includes(term)) {
            const lines = body.split('\n')
            const lineIdx = lines.findIndex((l) => l.includes(term))
            evidence.push({
              term,
              line: lineIdx >= 0 ? lineIdx + 1 : undefined,
              snippet: lineIdx >= 0 ? lines[lineIdx].slice(0, 160) : undefined
            })
          }
        }
        if (evidence.length === 0) continue
        // 점수는 매치된 term 비율만 반영. 의미론적 판단은 호출자 (AI) 가 함.
        const score = evidence.length / terms.length
        results.push({
          recordPath,
          layer,
          evidence,
          score,
          provider: this.name
        })
      }
    }

    // 점수 내림차순, limit 적용
    results.sort((a, b) => b.score - a.score)
    return query.limit ? results.slice(0, query.limit) : results
  }
}

// ─────────────────────────────────────────────────────────────────────────
// SubagentSearch — placeholder (미구현)
// ─────────────────────────────────────────────────────────────────────────

/**
 * Task tool 을 통해 전용 검색 에이전트 위임. 비용/지연이 큰 의미론적 검색이
 * 필요할 때만. N2.5 에서는 구현 안 함 — 인터페이스만 예약.
 */
export class SubagentSearch implements SearchProvider {
  readonly name = 'subagent'
  async search(_query: SearchQuery): Promise<SearchResult[]> {
    throw new Error(
      'SubagentSearch not implemented. Future work (post-N5). ' +
        'Use DirectAISearch + AI 의 능동 grep + Read for now.'
    )
  }
}

// ─────────────────────────────────────────────────────────────────────────
// RAGSearch — placeholder (미구현)
// ─────────────────────────────────────────────────────────────────────────

/**
 * 벡터 DB 기반. record corpus 가 수백 건 이상으로 자랐을 때만 의미 있음.
 * report-and-knowledge-roadmap.md 의 future work.
 */
export class RAGSearch implements SearchProvider {
  readonly name = 'rag'
  async search(_query: SearchQuery): Promise<SearchResult[]> {
    throw new Error(
      'RAGSearch not implemented. Future work (corpus 가 200+ records 자란 후 검토). ' +
        'Use DirectAISearch for now.'
    )
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Factory
// ─────────────────────────────────────────────────────────────────────────

export function createSearchProvider(name: 'direct-ai' | 'subagent' | 'rag' = 'direct-ai'): SearchProvider {
  switch (name) {
    case 'direct-ai':
      return new DirectAISearch()
    case 'subagent':
      return new SubagentSearch()
    case 'rag':
      return new RAGSearch()
    default:
      throw new Error(`Unknown SearchProvider: ${name}`)
  }
}

// suppress "unused stat import" — kept for future provider implementations
void statSync
