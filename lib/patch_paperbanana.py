"""Trial source adaptation. Provider and verified code isolation remain closed gates."""
import re

def text_port(text,file):
 text=text.replace('$ARGUMENTS[0]','the actual input path supplied in the task').replace('$ARGUMENTS[1]','the task caption or a clear caption inferred from its supplied source')
 text=text.replace('$ARGUMENTS','the actual task inputs')
 text=re.sub(r'(?m)^.*(?:AskUserQuestion|MCP.*first|mcp__.*(?:generate|evaluate)).*$', 'Use the pinned CLI as the primary production interface. Infer clear supplied context; ask only for material ambiguity. Optional MCP is a separate trial and does not replace editable artifact retrieval.',text)
 return text

def helpers(root):
 paths=list(root.rglob('paperbanana/agents/visualizer.py'))
 if len(paths)!=1:raise ValueError('Trial requires complete PaperBanana package')
 p=paths[0];t=p.read_text()
 a=t.index('            logger.error("Plot code execution failed, using placeholder")');b=t.index('\n\n        if self._last_vector_paths:',a)
 t=t[:a]+'''            raise RuntimeError(f"Plot generation failed; inspect saved source {code_path} and execution diagnostics. No placeholder image was accepted.")'''+t[b:]
 a=t.index('    def _execute_plot_code(');b=t.find('\n    def ',a+5)
 if b<0:b=len(t)
 signature=t[a:t.index('\n',t.index('    ) ->',a))+1] if '    ) ->' in t[a:b] else None
 if signature is None:raise ValueError('PaperBanana executor signature changed')
 t=t[:a]+signature+'''        """Generated code requires a separately verified isolated task executor.

        Upstream subprocess inherits host/provider access and is not containment.
        This trial source refuses execution until that capability is commissioned.
        Preserve generated .py and diagnostics for bounded native review.
        """
        raise RuntimeError("nstack.paperbanana.isolation_required: no verified generated-code execution backend is configured")
'''+t[b:]
 p.write_text(t)
