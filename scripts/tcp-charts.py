"""Draws the data chart in content/networking/tcp: transfer.svg.

Usage: python3 scripts/tcp-charts.py content/networking/tcp

The chart is plain SVG in the site's greys, with its own dark-mode colors.
It is 960px wide, so on phones it scrolls sideways instead of shrinking.
The points are the receiver's cumulative ACKs, in KB, from two packet
captures of 1,000,000 bytes sent over a 50 ms round trip: one with no loss,
and one with a single data segment dropped 160 ms in.
"""
import sys
out = sys.argv[1]
W, H = 960, 540
L, R, T, B = 100, 40, 30, 72
X1, Y1 = 1300, 1000
def x(ms): return L + ms / X1 * (W - L - R)
def y(kb): return T + (1 - kb / Y1) * (H - T - B)

clean = [(28, 0.0), (82, 1.4), (136, 15.9), (190, 44.9), (240, 102.8), (295, 218.6),
         (348, 450.3), (404, 913.7), (404, 1000.0)]
lossy = [(27, 0.0), (81, 1.4), (134, 15.9), (186, 42.0), (241, 98.5), (292, 137.6),
         (344, 178.1), (396, 220.1), (447, 262.1), (498, 307.0), (550, 351.9), (603, 396.8),
         (654, 441.6), (704, 535.8), (756, 583.5), (809, 631.3), (859, 679.1), (912, 726.9),
         (969, 777.6), (1021, 828.3), (1076, 878.9), (1127, 929.6), (1183, 983.2), (1236, 1000.0)]

STYLE = '''<style>
.ink{fill:#222} .muted{fill:#666} .grid{stroke:#e5e5e5} .axis{stroke:#999}
.solid{stroke:#222;stroke-width:3;fill:none} .dash{stroke:#222;stroke-width:3;fill:none;stroke-dasharray:10 7}
.dot{fill:#222}
text{font-family:"Libre Franklin",-apple-system,"Helvetica Neue",Arial,sans-serif;font-size:24px}
@media (prefers-color-scheme: dark){.ink{fill:#ddd}.muted{fill:#aaa}.grid{stroke:#333}.axis{stroke:#666}.solid,.dash{stroke:#ddd}.dot{fill:#ddd}}
</style>'''

title = 'Bytes acknowledged over time, 1 MB over a 50 ms round trip, with no loss and with one lost segment'
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title}">', STYLE]
for kb in range(0, 1001, 250):
    s.append(f'<line class="grid" x1="{L}" x2="{W-R}" y1="{y(kb):.1f}" y2="{y(kb):.1f}"/>')
    s.append(f'<text class="muted" x="{L-12}" y="{y(kb)+8:.1f}" text-anchor="end">{kb}</text>')
for ms in range(0, 1201, 200):
    s.append(f'<text class="muted" x="{x(ms):.1f}" y="{H-B+32}" text-anchor="middle">{ms}</text>')
s.append(f'<line class="axis" x1="{L}" x2="{W-R}" y1="{H-B}" y2="{H-B}"/>')
s.append(f'<text class="muted" x="{L}" y="{H-6}">KB acknowledged, by ms after the SYN</text>')
for cls, pts in (('solid', clean), ('dash', lossy)):
    d = ' '.join(f'{x(t):.1f},{y(v):.1f}' for t, v in pts)
    s.append(f'<polyline class="{cls}" points="{d}"/>')
s.append(f'<circle class="dot" cx="{x(404):.1f}" cy="{y(1000):.1f}" r="7"/>')
s.append(f'<text class="ink" x="{x(404)+16:.1f}" y="{y(1000)+34:.1f}">no loss: done at 404 ms</text>')
s.append(f'<circle class="dot" cx="{x(1236):.1f}" cy="{y(1000):.1f}" r="7"/>')
s.append(f'<text class="ink" x="{x(560):.1f}" y="{y(200):.1f}">one segment lost: done at 1,236 ms</text>')
s.append(f'<text class="ink" x="{x(560):.1f}" y="{y(200)+34:.1f}">after the loss, the window grows slowly</text>')
s.append('</svg>')
open(f'{out}/transfer.svg', 'w').write('\n'.join(s) + '\n')
