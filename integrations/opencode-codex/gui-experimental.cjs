"use strict";
const { Command, Plugin } = require("@opencode/plugin/gui");

// Runs the installed native engine in a session terminal. No model or auth bridge.
module.exports = Plugin.define({
  setup(ctx) {
    const starting = new Map();
    ctx.add(Command, () => {
      const current = ctx.sessions.current();
      return {
        id: "open",
        title: "Open Codex harness",
        description: "Run native Codex in this project's terminal",
        keywords: "nstack codex harness",
        section: "terminal",
        slash: { name: "codex" },
        enabled: !!current && !current.pending && current.server.builtin,
        run: async () => {
          const session = ctx.sessions.current();
          const binary = ctx.options.codex;
          if (!session || session.pending || !session.server.builtin ||
              typeof binary !== "string" || !binary.startsWith("/")) return false;
          if (starting.has(session.key)) return starting.get(session.key);
          const open = async () => {
            const pty = session.server.client.experimental.persistentPty;
            const existing = await pty.list({ sessionID: session.id });
            const terminal = existing.find(t => t.command === binary &&
              t.args.length === 0 && t.cwd === session.directory && t.status === "running") ||
              await pty.create({ sessionID: session.id, command: binary, args: [],
                cwd: session.directory, title: "Codex", env: {} });
            ctx.layout.open("terminal:" + terminal.id, session, { tab: "select" });
          };
          const pending = open().catch(error => {
            ctx.toast.show({ variant: "error", title: "Could not open Codex",
              description: String(error.message || error) });
          }).finally(() => starting.delete(session.key));
          starting.set(session.key, pending);
          return pending;
        },
      };
    });
  },
});
