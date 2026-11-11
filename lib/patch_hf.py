"""Narrow HF-specific ports; no cloud jobs or model downloads at build time."""
import pathlib,re
P=pathlib.Path
SPLIT = ''  # Compatibility import: no shared authored methodology is appended.
def change(s,old,new):
 if old not in s:raise ValueError('HF source anchor missing: '+old[:90])
 return s.replace(old,new)
def patch(name,out):
 p=out/'SKILL.md';s=p.read_text()
 if name=='hf-cli':
  s=re.sub(r'(?m)^description:.*$', 'description: Hugging Face-specific Hub CLI operations on named models, datasets, Spaces, repositories or explicitly authorized jobs. Use installed hf help for exact flags; generic ML, paper search and storage needs do not trigger this leaf.',s)
  s=change(s,'Install: `curl -LsSf https://hf.co/cli/install.sh | bash -s`.','Install the compatible immutable `huggingface_hub` package in an isolated locked environment at commissioning. This source catalog was generated against2.4.0; verify the chosen exact package and hash, then query its actual installed help. Never pipe a mutable installer into a shell.')
  s=change(s,'The Hugging Face Hub CLI tool `hf` is available.','Verify whether the project-locked `hf` executable is available; this source does not establish installation.')
  s=change(s,'Generated with `huggingface_hub v2.4.0`. Run `hf skills add --force` to regenerate.','Generated with `huggingface_hub v2.4.0`. Do not regenerate or globally install skills; use only the reviewed project shelf.')
  reference=s[s.index('## Commands'):]
  notice='> Native authority: Use the recorded immutable hf runtime and its actual help. Commands below grant no new account, upload, deployment, spending or installation authority. Reuse the task\'s existing scope; never inspect token stores or print keys (`hf auth list` / `hf auth token` are not admitted).\n\n'
  s=s.replace('## Commands\n',notice+'## Commands\n',1)
  folder=out/'references';folder.mkdir(exist_ok=True);(folder/'command-catalog.md').write_text('# Pinned upstream command reference\n\nCommands reflect the reviewed source catalog. Check installed help, immutable runtime lock and task authority; do not execute latest updates, skill installers, whole-session uploads or paid jobs from these examples.\n\n'+reference)
 elif name=='huggingface-local-models':
  s=change(s,'make\n','cmake -B build -DCMAKE_BUILD_TYPE=Release\ncmake --build build --config Release\n')
  s=change(s,'git clone https://github.com/ggml-org/llama.cpp\ncd llama.cpp','git clone https://github.com/ggml-org/llama.cpp\ncd llama.cpp\ngit checkout --detach "$NSTACK_REVIEWED_LLAMA_COMMIT"  # required immutable compatible runtime lock')
  s=change(s,'4. Confirm exact `.gguf` filenames with `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`.','4. Resolve the exact model commit and inspect its tree at that revision; record model-card rights, exact GGUF/projector filenames and file digests. Never treat main as an immutable lock.')
  s=change(s,'5. Launch with `llama-cli -hf <repo>:<QUANT>` or `llama-server -hf <repo>:<QUANT>`.','5. Download the exact reviewed revision and verified GGUF locally; launch the locked runtime with `-m /verified/path/model.gguf`. Direct -hf examples below are discovery sketches and must be converted to immutable local artifacts before execution.')
  s=change(s,'hf download <repo-without-gguf> --local-dir ./model-src','hf download <repo-without-gguf> --revision "$NSTACK_MODEL_COMMIT" --local-dir ./model-src')
 elif name=='trl-training':
  pass  # Preserve the upstream training method without an appended framework.
 elif name=='huggingface-datasets':
  s=s[:s.index('## Agent Traces')].rstrip()+'\n'
  s=change(s,'## Creating and Uploading Datasets','## Explicitly authorized dataset publication\n\nThis is a separate outbound task, not the read-only discovery default. Require named repository, artifact, visibility and redistribution rights; private by default. Never upload native session/transcript directories from this leaf. Resolve compatible uploader package to an immutable lock and use installed help; unpinned npx examples below are reference syntax only.')
 elif name=='huggingface-spaces':
  s=change(s,'If not, `pip install -U huggingface_hub`.','If absent, use the exact compatible package in the project lock; do not run an unbounded upgrade.')
  s=re.sub(r'The `hf-cli` skill teaches.*?(?=\n\n)', 'Use only the reviewed project-local hf-cli leaf if command help is needed. Do not run upstream skill installers or global collection installs.',s,flags=re.S)
  s=change(s,'--public|--private|--protected \\', '--private \\')
  s=change(s,'- Visibility: `--public` (anyone can view), `--private` (only you), `--protected` (app is reachable but git repo / Files tab is private).','- Visibility defaults to private. Use public or protected only when the user explicitly authorizes that audience; protected still exposes the app.')
  s=s.replace('.launch(mcp_server=True)', '.launch(share=False, mcp_server=False)')
  s=change(s,'- **Launch with `demo.launch(mcp_server=True)`** (Gradio 5+) so the Space doubles as an MCP server: each API function becomes an MCP tool described by its docstring and hints.','- **MCP endpoint exposure is opt-in.** Default to `demo.launch(share=False, mcp_server=False)`. Enable an endpoint only for an explicit scoped request after reviewing its exposed methods, data and access control.') if '- **Launch with `demo.launch(mcp_server=True)`**' in s else s
  # The generic replacement above changed the quoted instruction too.
  s=s.replace('- **Launch with `demo.launch(share=False, mcp_server=False)`** (Gradio 5+) so the Space doubles as an MCP server: each API function becomes an MCP tool described by its docstring and hints.','- **MCP exposure is opt-in.** Default to share=False and mcp_server=False. Review exposed methods, data and access control before explicitly authorized enablement.')
  notice='> Native authority: The hosted iteration below applies to the task\'s already authorized Space and account/budget scope. It grants no new paid compute, provider, account, public-audience or MCP authority. Current user/host instructions control validation; reuse authority already given and never inspect token stores or echo keys.\n\n'
  s=s.replace('# Hugging Face Spaces\n','# Hugging Face Spaces\n\n'+notice,1)
 else:raise ValueError('HF leaf not mapped')
 p.write_text(s)
