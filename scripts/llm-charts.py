"""Draws the data charts in content/ai/llm: params.svg and context.svg.

Usage: python3 scripts/llm-charts.py content/ai/llm

The charts are plain SVG in the site's greys, with their own dark-mode
colors. They are 960px wide, so on phones they scroll sideways instead of
shrinking. Every number here comes from a source in the note's references.
"""
import math, sys
out = sys.argv[1]
k = 960 / 680
W, H = 960, 540
L, R, T, B = 100, 100, 42, 72
X0, X1 = 2018.0, 2027.0
def x(t): return L + (t - X0) / (X1 - X0) * (W - L - R)
STYLE = '''<style>
.ink{fill:#222} .muted{fill:#666} .grid{stroke:#e5e5e5} .axis{stroke:#999}
.dot{fill:#222} .ring{fill:#fff;stroke:#222;stroke-width:3} .link{stroke:#999;stroke-width:3}
.step{stroke:#222;stroke-width:3;fill:none}
text{font-family:"Libre Franklin",-apple-system,"Helvetica Neue",Arial,sans-serif;font-size:24px}
@media (prefers-color-scheme: dark){.ink{fill:#ddd}.muted{fill:#aaa}.grid{stroke:#333}.axis{stroke:#666}.dot{fill:#ddd}.ring{fill:#111;stroke:#ddd}.link{stroke:#777}.step{stroke:#ddd}}
</style>'''
def chart(name, ymin, ymax, ticks, pts, pairs, unit_label, title, legend=False):
    def y(v): return T + (1 - (math.log10(v) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin))) * (H - T - B)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title}">', STYLE]
    for v, lab in ticks:
        s.append(f'<line class="grid" x1="{L}" x2="{W-R}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
        s.append(f'<text class="muted" x="{L-12}" y="{y(v)+8:.1f}" text-anchor="end">{lab}</text>')
    for yr in range(2018, 2027, 2):
        s.append(f'<text class="muted" x="{x(yr):.1f}" y="{H-B+32}" text-anchor="middle">{yr}</text>')
    s.append(f'<line class="axis" x1="{L}" x2="{W-R}" y1="{H-B}" y2="{H-B}"/>')
    s.append(f'<text class="muted" x="{L}" y="{H-6}">{unit_label}</text>')
    for (t, a, b) in pairs:
        s.append(f'<line class="link" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{y(a):.1f}" y2="{y(b):.1f}"/>')
    for (t, v, lab, dx, dy, anchor, hollow) in pts:
        cls = 'ring' if hollow else 'dot'
        s.append(f'<circle class="{cls}" cx="{x(t):.1f}" cy="{y(v):.1f}" r="7"/>')
        if lab:
            s.append(f'<text class="ink" x="{x(t)+dx*k:.1f}" y="{y(v)+dy*k:.1f}" text-anchor="{anchor}">{lab}</text>')
    if legend:
        lx, ly = x(2021.0), 300
        s.append(f'<circle class="dot" cx="{lx:.1f}" cy="{ly}" r="7"/><text class="ink" x="{lx+18:.1f}" y="{ly+8}">total parameters</text>')
        s.append(f'<circle class="ring" cx="{lx:.1f}" cy="{ly+36}" r="7"/><text class="ink" x="{lx+18:.1f}" y="{ly+44}">used per token (mixture of experts)</text>')
    s.append('</svg>')
    open(f'{out}/{name}.svg', 'w').write('\n'.join(s) + '\n')

B_ = 1e9
chart('params', 1e8, 5e12,
      [(1e8, '100M'), (1e9, '1B'), (1e10, '10B'), (1e11, '100B'), (1e12, '1T')],
      [(2018.45, 117e6, 'GPT-1', 0, -12, 'middle', False),
       (2019.12, 1.5*B_, 'GPT-2', 0, -12, 'middle', False),
       (2020.4, 175*B_, 'GPT-3', 0, -12, 'middle', False),
       (2023.15, 65*B_, 'LLaMA', 0, -12, 'middle', False),
       (2024.55, 405*B_, 'Llama 3.1', 0, 24, 'middle', False),
       (2024.95, 671*B_, 'DeepSeek-V3', -8, -10, 'end', False), (2024.95, 37*B_, '', 0, 0, 'start', True),
       (2025.55, 1000*B_, 'Kimi K2', 0, -12, 'middle', False), (2025.55, 32*B_, '', 0, 0, 'start', True),
       (2026.3, 1600*B_, 'DeepSeek-V4-Pro', -20, -34, 'middle', False), (2026.3, 49*B_, '', 0, 0, 'start', True),
       (2026.55, 2800*B_, 'Kimi K3', 8, 5, 'start', False), (2026.55, 104*B_, '', 0, 0, 'start', True)],
      [(2024.95, 671*B_, 37*B_), (2025.55, 1000*B_, 32*B_), (2026.3, 1600*B_, 49*B_), (2026.55, 2800*B_, 104*B_)],
      'parameters, log scale', 'Published parameter counts, 2018 to 2026', legend=True)
chart('context', 256, 8e6,
      [(1e3, '1K'), (1e4, '10K'), (1e5, '100K'), (1e6, '1M')],
      [(2018.45, 512, 'GPT-1', 10, 6, 'start', False),
       (2019.12, 1024, 'GPT-2', 0, -12, 'middle', False),
       (2020.4, 2048, 'GPT-3', 0, -12, 'middle', False),
       (2023.2, 32768, 'GPT-4', -8, 5, 'end', False),
       (2023.37, 100000, 'Claude', -8, -8, 'end', False),
       (2023.9, 200000, 'Claude 2.1', 8, 16, 'start', False),
       (2024.12, 1e6, 'Gemini 1.5', -8, -8, 'end', False),
       (2025.04, 4e6, 'MiniMax-01', 0, -12, 'middle', False),
       (2026.3, 1e6, 'DeepSeek-V4-Pro', -8, 22, 'end', False)],
      [], 'context window in tokens, log scale', 'Context windows, 2018 to 2026')
