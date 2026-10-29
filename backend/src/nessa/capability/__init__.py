"""Capability assessment (spec sections 8-10: MAP-1, OUT-1, RDY-1; plan section 3, the
capability half of "Capability and catalogue"; ADR 0012).

This module owns what a requirement means and how far evidence meets it: provisional skills
matrices per target, behaviourally anchored levels and rubrics, typed protected gates, the
person's skill evidence and requirement statements, planned course outcomes (OUT-1) and
their rules, readiness and the apply-now case, gaps and the abstract action graph, and the
combined question graph. The opportunity catalogue (`nessa.catalogue`) stores the records it
reads; the review checkpoint owns accepting modelling assumptions (OUT1-11).

Planned learning is never demonstrated skill: a planned outcome counts only in a
conditional scenario and never changes the person's current evidence. Readiness, gaps and
priorities are computed here by deterministic code, never by a model.
"""
