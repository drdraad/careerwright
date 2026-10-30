// The spike's truth rules, as tests: the revelation comes from a stated deterministic source,
// joins roles by shared essential skills (never by shared title words), and says only what the
// list supports. Run with `pnpm test` (Node's own test runner; no extra dependency).
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ROLES, SKILLS, type Role } from "./data.ts";
import {
  MAX_DESTINATIONS,
  MIN_CONNECTION_SHARED,
  MIN_DESTINATION_SHARED,
  connectionSentence,
  destinationsFor,
  matchRoles,
  sharedSkills,
  titleWords,
  unexpectedConnection,
} from "./model.ts";

const byId = (id: string): Role => {
  const role = ROLES.find((r) => r.id === id);
  assert.ok(role, `role ${id} exists`);
  return role;
};

const mini = (id: string, field: string, skills: string[]): Role => ({
  id,
  title: id,
  plural: `${id}s`,
  field,
  skills,
});

describe("the made-up list", () => {
  it("gives every role eight distinct skills that exist", () => {
    const ids = new Set(SKILLS.map((s) => s.id));
    for (const role of ROLES) {
      assert.equal(role.skills.length, 8, role.id);
      assert.equal(new Set(role.skills).size, 8, role.id);
      for (const skill of role.skills) assert.ok(ids.has(skill), `${role.id}: ${skill}`);
    }
  });

  it("gives every role an unexpected connection, so the demo always has one", () => {
    for (const role of ROLES) assert.ok(unexpectedConnection(role, ROLES), role.id);
  });
});

describe("type-ahead", () => {
  it("matches the start of any word in a title, ignoring case", () => {
    const titles = matchRoles("NURSE", ROLES).map((r) => r.title);
    assert.deepEqual(titles, ["Nurse", "Nursery worker", "Dental nurse"]);
  });

  it("puts titles that start with the text before later-word matches", () => {
    const titles = matchRoles("car", ROLES).map((r) => r.title);
    assert.deepEqual(titles, ["Care worker", "Carpenter"]);
  });

  it("never matches the middle of a word, and never invents a match", () => {
    assert.deepEqual(matchRoles("arpent", ROLES), []);
    assert.deepEqual(matchRoles("astronaut", ROLES), []);
    assert.deepEqual(matchRoles("   ", ROLES), []);
  });
});

describe("the unexpected connection", () => {
  it("is a role from another field, sharing no title word, with the most shared skills", () => {
    for (const person of ROLES) {
      const found = unexpectedConnection(person, ROLES);
      assert.ok(found);
      assert.notEqual(found.role.field, person.field);
      const words = titleWords(person.title);
      for (const word of titleWords(found.role.title)) assert.ok(!words.has(word), person.id);
      assert.deepEqual(found.shared, sharedSkills(person, found.role));
      assert.ok(found.shared.length >= MIN_CONNECTION_SHARED);
      for (const other of ROLES) {
        const eligible =
          other.field !== person.field &&
          ![...titleWords(other.title)].some((w) => words.has(w));
        if (eligible) assert.ok(sharedSkills(person, other).length <= found.shared.length);
      }
    }
  });

  it("joins a chef to firefighters by the five skills the two roles share", () => {
    const found = unexpectedConnection(byId("chef"), ROLES);
    assert.ok(found);
    assert.equal(found.role.id, "firefighter");
    assert.deepEqual(found.shared, ["deadlines", "calm", "lead", "safety", "equipment"]);
    assert.deepEqual(found.unknown, ["firstaid", "emergency", "risks"]);
  });

  it("lists as not known yet only the destination's skills the person's role does not share", () => {
    for (const person of ROLES) {
      const found = unexpectedConnection(person, ROLES);
      assert.ok(found);
      for (const skill of found.unknown) assert.ok(!person.skills.includes(skill));
      assert.equal(found.unknown.length + found.shared.length, found.role.skills.length);
    }
  });

  it("breaks a tie by title, so the same answer always gives the same connection", () => {
    const person = mini("cook", "food", ["a", "b", "c", "d", "e"]);
    const list = [
      person,
      mini("zebra keeper", "zoo", ["a", "b", "c", "d"]),
      mini("archer", "sport", ["b", "c", "d", "e"]),
    ];
    assert.equal(unexpectedConnection(person, list)?.role.id, "archer");
  });

  it("is absent when no other field shares enough skills: no source, no revelation", () => {
    const person = mini("cook", "food", ["a", "b", "c", "d"]);
    const list = [person, mini("baker", "food", ["a", "b", "c", "d"]), mini("pilot", "air", ["a", "b"])];
    assert.equal(unexpectedConnection(person, list), null);
  });

  it("never counts a role whose title shares a word with the person's", () => {
    const person = mini("shop supervisor", "shops", ["a", "b", "c", "d"]);
    const list = [person, mini("warehouse supervisor", "transport", ["a", "b", "c", "d"])];
    assert.equal(unexpectedConnection(person, list), null);
  });

  it("is worded as a fact about the two roles, never about the person", () => {
    const person = byId("chef");
    const found = unexpectedConnection(person, ROLES);
    assert.ok(found);
    const sentence = connectionSentence(person, found);
    assert.equal(sentence, "Chefs and firefighters share 5 essential skills.");
    assert.doesNotMatch(sentence, /\byou/i);
  });
});

describe("the first destinations", () => {
  it("are other roles sharing enough skills, at most five, without the person or the connection", () => {
    for (const person of ROLES) {
      const found = unexpectedConnection(person, ROLES);
      const exclude = new Set(found ? [found.role.id] : []);
      const destinations = destinationsFor(person, ROLES, exclude);
      assert.ok(destinations.length <= MAX_DESTINATIONS);
      for (const d of destinations) {
        assert.notEqual(d.role.id, person.id);
        assert.ok(!exclude.has(d.role.id));
        assert.ok(d.shared.length >= MIN_DESTINATION_SHARED);
        assert.deepEqual(d.shared, sharedSkills(person, d.role));
      }
    }
  });

  it("are listed by title, so position never means rank", () => {
    const destinations = destinationsFor(byId("care-worker"), ROLES, new Set());
    const titles = destinations.map((d) => d.role.title);
    assert.deepEqual(titles, [...titles].sort((a, b) => a.localeCompare(b)));
  });
});
