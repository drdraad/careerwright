// A minimal parser for the `text/event-stream` format (HTML Living Standard, "Server-sent
// events"). The browser's EventSource cannot send an Authorization header, so the workspace
// stream is read with fetch and parsed here.

export type SseItem =
  | { type: "message"; id: string | undefined; event: string; data: string }
  | { type: "retry"; ms: number };

export class SseParser {
  private buffer = "";
  private data: string[] = [];
  private event = "";
  private id: string | undefined;

  /** Feeds a decoded chunk; returns every item completed by it, in order. */
  push(chunk: string): SseItem[] {
    this.buffer += chunk;
    const items: SseItem[] = [];
    // A line ends at CRLF, LF or CR; a trailing CR may be the first half of a CRLF.
    for (;;) {
      const match = /\r\n|\n|\r(?!$)/.exec(this.buffer);
      if (match === null) break;
      const line = this.buffer.slice(0, match.index);
      this.buffer = this.buffer.slice(match.index + match[0].length);
      const item = this.line(line);
      if (item !== null) items.push(item);
    }
    return items;
  }

  private line(line: string): SseItem | null {
    if (line === "") return this.dispatch();
    if (line.startsWith(":")) return null;
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    switch (field) {
      case "data":
        this.data.push(value);
        return null;
      case "event":
        this.event = value;
        return null;
      case "id":
        if (!value.includes("\0")) this.id = value;
        return null;
      case "retry":
        return /^\d+$/.test(value) ? { type: "retry", ms: Number(value) } : null;
      default:
        return null;
    }
  }

  private dispatch(): SseItem | null {
    const data = this.data;
    const event = this.event || "message";
    const id = this.id;
    this.data = [];
    this.event = "";
    this.id = undefined;
    if (data.length === 0) return null;
    return { type: "message", id, event, data: data.join("\n") };
  }
}
