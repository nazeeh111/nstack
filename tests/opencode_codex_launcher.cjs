"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const test = require("node:test");
const source = fs.readFileSync(require("node:path").join(__dirname,
  "../integrations/opencode-codex/gui-experimental.cjs"), "utf8");
function fixture() {
  const module = { exports: {} };
  vm.runInNewContext(source, { module, require: id => {
    assert.equal(id, "@opencode/plugin/gui");
    return { Plugin: { define: value => value }, Command: {} };
  }});
  const calls = [], shown = [], errors = [];
  const session = { key: "local\n1", id: "1", directory: "/tmp/a ' ; $(touch nope)",
    pending: false, server: { builtin: true, client: { experimental: { persistentPty: {
      list: async () => calls,
      create: async value => { const item = { ...value, id: "pty1", status: "running" }; calls.push(item); return item; },
    }}}}};
  let definition;
  module.exports.setup({ sessions: { current: () => session },
    options: { codex: "/opt/native Codex/bin/codex" },
    add: (_registry, create) => { definition = create; },
    layout: { open: (...args) => shown.push(args) },
    toast: { show: value => errors.push(value) },
  });
  return { session, calls, shown, errors, command: () => definition() };
}
test("opens actual native engine with literal cwd and no permission/model overrides; reuses it", async () => {
  const f = fixture();
  await Promise.all([f.command().run(), f.command().run()]);
  assert.equal(f.calls.length, 1);
  const request = f.calls[0];
  assert.equal(request.command, "/opt/native Codex/bin/codex");
  assert.equal(request.cwd, f.session.directory);
  assert.equal(JSON.stringify(request.args), "[]");
  assert.equal(JSON.stringify(request.env), "{}");
  assert.equal(f.shown[0][0], "terminal:pty1");
  await f.command().run(); assert.equal(f.calls.length, 1);
});
test("remote or pending sessions cannot launch the local executable", async () => {
  const f = fixture(); f.session.server.builtin = false;
  assert.equal(f.command().enabled, false); await f.command().run();
  f.session.server.builtin = true; f.session.pending = true;
  assert.equal(f.command().enabled, false); await f.command().run();
  assert.equal(f.calls.length, 0);
});
test("a native denial is reported, never retried through another route", async () => {
  const f = fixture();
  f.session.server.client.experimental.persistentPty.list = async () => { throw new Error("native denied"); };
  await f.command().run();
  assert.equal(f.calls.length, 0); assert.equal(f.errors[0].description, "native denied");
});
