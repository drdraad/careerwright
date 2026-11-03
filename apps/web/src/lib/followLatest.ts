"use client";
// The conversation follows its newest part, as a chat does (Task W2F slice E; the product
// owner's re-test: "The conversation doesn't autoscroll to the bottom of the conversation like
// ChatGPT does"). Once the person sends, the window keeps the end of the conversation (the
// reply field) in view while the message, Muse's streamed reply and its review card arrive,
// but never scrolls the person's own newest message above the top, so the reply reads from its
// start and the card's first decision stays near it. Scrolling up to read stops it following;
// coming back to the end starts it again. Opening the chapter never scrolls it. It only
// scrolls the window: keyboard focus never moves. Under reduced motion or calm mode it jumps
// instead of gliding.
import { type RefObject, useCallback, useEffect, useRef } from "react";

/** How close to the end counts as being at it, and the room left above the newest message. */
const AT_END = 48;
const ABOVE_NEWEST = 16;

function still(): boolean {
  return (
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true ||
    document.documentElement.dataset.calm === "true"
  );
}

/** The window's scroll padding (the open sheet, a sticky bar), which nothing should sit under. */
function padding(): { top: number; bottom: number } {
  const style = getComputedStyle(document.documentElement);
  return {
    top: Number.parseFloat(style.scrollPaddingTop) || 0,
    bottom: Number.parseFloat(style.scrollPaddingBottom) || 0,
  };
}

/**
 * `thread`: the conversation, watched for changes in size; `end`: what marks its end (the
 * reply field), or the conversation's own end while there is none (a review card waits).
 * Returns `follow`, called when the person sends: from then on the newest part is kept in view.
 */
export function useFollowLatest(
  thread: RefObject<HTMLElement | null>,
  end: RefObject<HTMLElement | null>,
): () => void {
  const following = useRef(false);

  const atEnd = useCallback(() => {
    const element = end.current ?? thread.current;
    return (
      element !== null &&
      element.getBoundingClientRect().bottom <= window.innerHeight - padding().bottom + AT_END
    );
  }, [thread, end]);

  const keep = useCallback(() => {
    const conversation = thread.current;
    const element = end.current ?? conversation;
    // A hidden view (another of the chapter's tabs is open) is never scrolled to.
    if (!following.current || conversation === null || element === null) return;
    if (conversation.closest("[hidden]") !== null) return;
    const { top, bottom } = padding();
    const below = element.getBoundingClientRect().bottom - (window.innerHeight - bottom);
    const messages = conversation.querySelectorAll(".turn-you");
    const newest = messages[messages.length - 1];
    const room =
      newest === undefined ? below : newest.getBoundingClientRect().top - top - ABOVE_NEWEST;
    const by = Math.min(below, room);
    if (by > 1) window.scrollBy({ top: by, behavior: still() ? "instant" : "smooth" });
  }, [thread, end]);

  // The person's own scrolling: up stops following, back at the end starts it again. A fall
  // in position at the very bottom is the page getting shorter, not the person scrolling.
  useEffect(() => {
    let last = window.scrollY;
    const scrolled = () => {
      const y = window.scrollY;
      const bottomMost = document.documentElement.scrollHeight - window.innerHeight;
      if (y < last - 1 && y < bottomMost - 1) following.current = false;
      else if (atEnd()) following.current = true;
      last = y;
    };
    window.addEventListener("scroll", scrolled, { passive: true });
    return () => window.removeEventListener("scroll", scrolled);
  }, [atEnd]);

  // The conversation grows: a message sent, a reply streaming, a card arriving.
  useEffect(() => {
    const conversation = thread.current;
    if (conversation === null) return;
    const watch = new ResizeObserver(keep);
    watch.observe(conversation);
    return () => watch.disconnect();
  }, [thread, keep]);

  return useCallback(() => {
    following.current = true;
    keep();
  }, [keep]);
}
