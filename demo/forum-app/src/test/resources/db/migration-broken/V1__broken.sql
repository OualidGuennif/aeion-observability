-- A migration that creates a table and then fails: the probe table must not survive.

CREATE TABLE probe (id TEXT PRIMARY KEY);

CREATE TABLE probe (id TEXT PRIMARY KEY);
