"""Native platform bindings for the complete selected pstack methods."""
import re

def text_port(text,file):
 text=text.replace("<skill dir>/scripts/statechart SPEC.tla", 'node "<skill dir>/scripts/statechart.ts" SPEC.tla')
 text=text.replace('The first run installs TLC and Java with mise and needs the network.', 'Use existing compatible Node and Java11+. Set JAVA to the actual Java executable and TLA2TOOLS to the locally verified TLC1.7.4 jar (SHA256936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88). No automatic dependency bootstrap occurs. Inspect custom view code before execution; bound model size and run time.')
 text=text.replace('Render charts with Pele. When the user asks for an image, or a chart is too large to read as text, follow `references/render.md`. Do not use a different renderer unless the user asks for it.', 'Render Mermaid with the existing native viewer or selected diagram export capability. Follow `references/render.md` for mark semantics and source-preserving export; no global renderer installation is required.')
 if file.name=='render.md':
  text=re.sub(r'(?s)Render each.*?(?=## Colors)', 'Keep the actual Mermaid source and use the existing native Mermaid viewer or selected diagram exporter when an SVG/image is needed. Verify labels, bug paths and marks in the exported artifact. A renderer failure does not negate the model result; return source and error. No global Pele install or browser bootstrap is required.\n\n',text,count=1)
  text=text.replace('Pele ignores Mermaid `theme` and `themeVariables`.', 'Historical Pele-specific styles below are reference examples, not a required renderer. Native Mermaid uses its own theme support.')
 text=text.replace('If you cannot stop it, interleave the sides so both see the same noise, and say so in the report.', 'Do not stop unrelated processes; interleave the comparisons under similar load or defer them, and record the confound.')
 text=text.replace('`nproc`','`sysctl -n hw.logicalcpu` on macOS (`nproc` on Linux)')
 text=re.sub(r'(?m)^.*if you cannot stop.*$', 'Do not stop unrelated processes. Record contention and rerun at a suitable time or report the confound.',text)
 return text

def helpers(root):
 for p in root.rglob('scripts/run.ts'):
  t=p.read_text();a=t.index('  const mise =',t.index('async function findTlc'));b=t.index('\n}\n',a)
  t=t[:a]+'''  throw new Error("Set TLA2TOOLS to the verified TLC1.7.4 jar and JAVA to existing Java11+; automatic installs are disabled");'''+t[b:]
  p.write_text(t)
