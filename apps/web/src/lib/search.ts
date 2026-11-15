/**
 * Accent- and case-insensitive matching with an explainable rank, shared by the search palette
 * and the help center. "curriculo" finds "Currículo", "estudio" finds "Estúdio".
 */

export function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

export interface Rankable {
  /** What the person reads: the strongest field. */
  label: string;
  /** Secondary text (title, description). */
  detail?: string;
  /** Synonyms and words people type; never shown. */
  keywords?: string;
}

/**
 * 0 means no match. Every query word must match somewhere (AND); the score rewards where it
 * matched: label start > label word start > label substring > keyword > detail.
 */
export function rank(query: string, item: Rankable): number {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  if (!words.length) return 0;
  const label = normalize(item.label);
  const labelWords = label.split(/[^\p{L}\p{N}]+/u);
  const keywords = normalize(item.keywords ?? "");
  const detail = normalize(item.detail ?? "");
  let score = 0;
  for (const word of words) {
    if (label.startsWith(word)) score += 100;
    else if (labelWords.some((part) => part.startsWith(word))) score += 60;
    else if (label.includes(word)) score += 40;
    else if (keywords.split(/\s+/).some((part) => part.startsWith(word))) score += 25;
    else if (detail.includes(word)) score += 10;
    else return 0;
  }
  return score;
}

/** Items that match, best first; ties keep the original order (the registry's order). */
export function search<T>(query: string, items: T[], toRankable: (item: T) => Rankable): T[] {
  return items
    .map((item, index) => ({ item, index, score: rank(query, toRankable(item)) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map((entry) => entry.item);
}

/**
 * Split text into parts for highlighting the query words without HTML injection: the caller
 * renders the parts as React text, marking `match: true` ones.
 */
export function highlight(text: string, query: string): { text: string; match: boolean }[] {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  if (!words.length) return [{ text, match: false }];
  // Map each normalized char back to the original index (NFD removal keeps 1:1 for Latin).
  const folded = [...text].map((char) => normalize(char) || char);
  const flat = folded.join("");
  const marks = new Array<boolean>(folded.length).fill(false);
  for (const word of words) {
    let from = 0;
    for (;;) {
      const at = flat.indexOf(word, from);
      if (at < 0) break;
      // folded chars are length 1 for letters; guard if not
      let pos = 0;
      for (let i = 0; i < folded.length; i++) {
        const end = pos + folded[i].length;
        if (end > at && pos < at + word.length) marks[i] = true;
        pos = end;
      }
      from = at + word.length;
    }
  }
  const parts: { text: string; match: boolean }[] = [];
  [...text].forEach((char, i) => {
    const last = parts.at(-1);
    if (last && last.match === marks[i]) last.text += char;
    else parts.push({ text: char, match: marks[i] });
  });
  return parts;
}
