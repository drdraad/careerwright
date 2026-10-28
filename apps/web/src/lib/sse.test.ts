import { describe, expect, it } from "vitest";
import { SseParser } from "./sse";

describe("[DUR-03] server-sent events are parsed per the HTML event-stream format", () => {
  it("dispatches a message with its id, event name and data on a blank line", () => {
    const parser = new SseParser();

    expect(parser.push('id: 7\ndata: {"seq":7}\n\n')).toEqual([
      { type: "message", id: "7", event: "message", data: '{"seq":7}' },
    ]);
  });

  it("joins chunks that split lines and fields anywhere", () => {
    const parser = new SseParser();
    const received = [
      ...parser.push("id: 1"),
      ...parser.push("2\nda"),
      ...parser.push("ta: a\r"),
      ...parser.push("\n\r\n"),
    ];

    expect(received).toEqual([{ type: "message", id: "12", event: "message", data: "a" }]);
  });

  it("reports the retry interval and ignores comments and empty blocks", () => {
    const parser = new SseParser();

    expect(parser.push("retry: 2000\n\n: keep-alive\n\n\n")).toEqual([{ type: "retry", ms: 2000 }]);
  });

  it("keeps named events with their data, including multi-line data", () => {
    const parser = new SseParser();

    expect(
      parser.push("event: reauthenticate\ndata: {}\n\nevent: x\ndata: a\ndata: b\n\n"),
    ).toEqual([
      { type: "message", id: undefined, event: "reauthenticate", data: "{}" },
      { type: "message", id: undefined, event: "x", data: "a\nb" },
    ]);
  });

  it("does not dispatch a block without data, and holds an unfinished block", () => {
    const parser = new SseParser();

    expect(parser.push("id: 3\n\nid: 4\ndata: half")).toEqual([]);
    expect(parser.push("\n\n")).toEqual([
      { type: "message", id: "4", event: "message", data: "half" },
    ]);
  });

  it("ignores a non-numeric retry value and unknown fields", () => {
    const parser = new SseParser();

    expect(parser.push("retry: soon\nfoo: bar\ndata: ok\n\n")).toEqual([
      { type: "message", id: undefined, event: "message", data: "ok" },
    ]);
  });
});
