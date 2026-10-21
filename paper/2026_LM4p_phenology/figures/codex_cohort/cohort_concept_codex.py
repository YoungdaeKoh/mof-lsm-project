#!/usr/bin/env python3
"""Draw the LM4.1/PPA conceptual schematic using only matplotlib.

Scientific content follows codex_cohort_figure_brief_2026-10-20.md.
Tree sizes, crown shapes and patch areas are schematic, not measurements.
Run with /opt/homebrew/bin/python3 cohort_concept_codex.py.
"""
from pathlib import Path
import os

# Keep matplotlib's cache, as well as the deliverable, beside this script.
HERE = Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR'] = str(HERE / '.mplconfig')
os.environ['XDG_CACHE_HOME'] = str(HERE / '.cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon, Ellipse

INK = '#233846'
MUTED = '#566b76'
SPRUCE = '#28796f'
MAPLE = '#aa713b'
GRASS = '#8caa47'
BLUE = '#eaf3f8'


def box(ax, x, y, w, h, fc='white', ec='#d5e0e4', radius=1.3, lw=1):
    p = FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={radius}',
                       facecolor=fc,edgecolor=ec,linewidth=lw)
    ax.add_patch(p)
    return p


def text(ax, x, y, s, size=12, color=INK, weight='normal', ha='left', va='top', **kw):
    return ax.text(x,y,s,fontsize=size,color=color,weight=weight,ha=ha,va=va,**kw)


def arrow(ax, start, end, color=INK, lw=1.6, style='-|>'):
    ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle=style,color=color,lw=lw))


def tree(ax,x,base,height,kind='spruce',width=9):
    c = SPRUCE if kind == 'spruce' else MAPLE
    ax.plot([x,x],[base,base+height*.82],color='#796755',lw=2.3,zorder=3)
    if kind == 'spruce':
        for frac in [.44,.61,.78]:
            top=base+height*(frac+.22)
            ax.add_patch(Polygon([(x-width/2,base+height*(frac-.12)),
                                  (x,top),(x+width/2,base+height*(frac-.12))],
                                 facecolor=c,edgecolor='white',lw=.7,zorder=4))
    else:
        ax.add_patch(Ellipse((x,base+height*.79),width,height*.43,
                            facecolor=c,edgecolor='white',lw=.8,zorder=4))


def grass(ax,x,y,w=9,h=6):
    for dx,lean in [(-.38,-.18),(-.18,.08),(0,-.1),(.2,.12),(.38,.2)]:
        ax.plot([x+dx*w,x+(dx+lean)*w],[y,y+h*(1-abs(dx))],color=GRASS,lw=2,zorder=4)


def panel(fig, rect, label, title):
    ax=fig.add_axes(rect)
    ax.set(xlim=(0,100),ylim=(0,100))
    ax.axis('off')
    box(ax,0,0,100,100,fc='#fbfcfc')
    text(ax,3,96,label,18,weight='bold')
    text(ax,10,96,title,17,weight='bold')
    return ax


def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,
                         'mathtext.fontset':'dejavusans','savefig.facecolor':'white'})
    fig=plt.figure(figsize=(20,13),facecolor='white')
    fig.text(.035,.958,'From land patches to a vertically structured canopy',fontsize=25,weight='bold',color=INK)
    fig.text(.035,.922,'LM4.1 • Perfect Plasticity Approximation (PPA)',fontsize=16,color=MUTED)

    a=panel(fig,[.035,.395,.275,.495],'a','Grid cell → tiles')
    text(a,6,85,'C96 cubed sphere • ~1°',14)
    text(a,6,79,'Patches differ in land-use history\nand time since disturbance.',12,color=MUTED,linespacing=1.5)
    # Patch sizes are deliberately unquantified.
    box(a,6,32,88,36,fc='white',ec=INK,radius=0,lw=1.3)
    for x,y,w,h,fc in [(6,32,48,36,'#deede5'),(54,51,40,17,'#edf2d8'),
                       (54,32,22,19,'#f4e6ca'),(76,32,18,19,'#e5edc9')]:
        a.add_patch(Rectangle((x,y),w,h,facecolor=fc,edgecolor='white',lw=2))
    text(a,10,64,'Primary forest',12,weight='bold')
    tree(a,18,39,15,width=10); tree(a,33,39,19,width=11)
    text(a,58,64,'Secondary / gap',11,weight='bold')
    text(a,58,58,'e.g. after treefall',10,color=MUTED)
    text(a,65,44,'Crop-\nland',11,ha='center',linespacing=1.3)
    text(a,85,44,'Pasture',10,ha='center')
    text(a,6,26,'Up to 18 tiles per grid cell',13,weight='bold')
    text(a,6,19,'One soil column per tile',13)
    text(a,6,10,'Patch areas shown schematically.',10,color=MUTED)

    b=panel(fig,[.325,.395,.64,.495],'b','One forest tile → cohorts → canopy layers')
    text(b,3,86,'Cohort = same species + similar size (height / DBH)',14,weight='bold')
    text(b,3,80,'Each cohort represents many individuals; the same species can occupy several cohorts.',12,color=MUTED)
    box(b,3,68,77,8,fc=BLUE,ec='#cadfe9')
    text(b,41.5,72,'Shared canopy air: one temperature + one humidity per tile',12,ha='center',va='center')
    # Height-order diagram: icons stand for cohorts, not spatially located trees.
    b.add_patch(Rectangle((3,43),66,22,facecolor='#fff3cb',edgecolor='none'))
    b.add_patch(Rectangle((3,29),66,14,facecolor='#e6eee9',edgecolor='none'))
    b.plot([3,69],[43,43],ls=(0,(4,3)),color='#91a59a',lw=1.3)
    b.add_patch(Rectangle((3,26),66,3,facecolor='#b7a38b',edgecolor='none'))
    tree(b,12,29,35,width=11)
    tree(b,29,29,29,kind='acer',width=12)
    tree(b,46,29,13,width=8)
    grass(b,62,29,w=8,h=7)
    text(b,70.5,61,'Layer 1',13,weight='bold')
    text(b,70.5,55,'Receives light first',11,color=MUTED)
    text(b,70.5,41,'Layer 2',13,weight='bold')
    text(b,70.5,35,'Shaded below',11,color=MUTED)
    arrow(b,(93,66),(93,48),color='#c99c29',lw=3)
    text(b,93,68,'Sunlight',11,ha='center',color='#9b7517')
    for x,name,h,n in [(12,'Spruce · tall','h_a','n_a'),(29,'Maple','h_b','n_b'),
                       (46,'Spruce · small','h_c','n_c'),(62,'C3 grass','h_d','n_d')]:
        text(b,x,24,name,11,weight='bold',ha='center')
        text(b,x,19,rf'${h}$; ${n}$ indiv. m$^{{-2}}$',10,ha='center',color=MUTED)
    text(b,3,12,'Height order → fill crown area to ground area in layer 1; overflow → layer 2, etc.',12,weight='bold')
    text(b,3,6,'Plastic crowns fill gaps; only height order matters. Positions are illustrative; h = height, n = density.',11,color=MUTED)

    c=panel(fig,[.035,.108,.93,.266],'c','Why cohorts differ from an average PFT individual')
    # Three parallel blocks keep the conceptual contrast and state ownership clear.
    text(c,3,79,'CLM4 CNDV',14,weight='bold')
    text(c,3,68,'PFTs share area side by side',12,color=MUTED)
    for x,w,col in [(3,8,'#deede5'),(11,8,'#f0e3d6'),(19,8,'#e5edc9')]:
        c.add_patch(Rectangle((x,27),w,32,facecolor=col,edgecolor='white',lw=2))
    tree(c,7,30,25,width=4)
    tree(c,15,30,25,kind='acer',width=4)
    grass(c,23,30,w=4,h=12)
    text(c,3,20,'One average individual per PFT\nNo height layering',12,linespacing=1.5)
    c.plot([30,30],[10,80],color='#d5e0e4',lw=1)
    text(c,33,79,'LM4.1 PPA',14,weight='bold')
    text(c,33,68,'Many cohorts; sorted by height',12,color=MUTED)
    for x,w,col in [(33,12,SPRUCE),(45,10,MAPLE)]:
        c.add_patch(Rectangle((x,44),w,12,facecolor=col,edgecolor='white',lw=1))
    for x,w,col in [(33,9,SPRUCE),(42,4,GRASS)]:
        c.add_patch(Rectangle((x,29),w,12,facecolor=col,edgecolor='white',lw=1))
    text(c,56,50,'Layer 1',10,va='center')
    text(c,56,35,'Layer 2',10,va='center')
    text(c,33,20,'Up to 65 cohorts per tile\nDensity = nindivs (individuals m⁻²)',12,linespacing=1.5)
    c.plot([64,64],[10,80],color='#d5e0e4',lw=1)
    text(c,67,79,'Shared forcing, individual responses',14,weight='bold')
    text(c,67,65,'Per tile',12,weight='bold',color='#39718b')
    text(c,67,56,'Phenology temperature: 20-day smoothed\ncanopy-air temperature',12,linespacing=1.4)
    text(c,67,36,'Per cohort',12,weight='bold',color=SPRUCE)
    text(c,67,27,'Leaf temperature • photosynthesis\nLeaf ON/OFF status • GDD',12,linespacing=1.5)

    fig.text(.04,.081,'Leaf area scaling',fontsize=12,weight='bold',color=INK)
    fig.text(.145,.081,'Cohort LAI = leaf carbon / LMA / crown area;   grid LAI ≈ Σ (cohort LAI × fraction of grid ground covered).',fontsize=12,color=INK)
    fig.text(.04,.057,'Run example · July 2010, 50–70°N · cohorts per species in tiles containing that species:  picea 7.9 mean (19 max);  acer 5.8 (19);  c3grass 1.0.',fontsize=11,color=MUTED)
    fig.text(.04,.035,'18 tiles and 65 cohorts are restart-dimension limits. All geometry is schematic.  PPA: Purves et al. (2007/2008); Strigul et al. (2008); Weng et al. (2015).',fontsize=10,color=MUTED)
    out=HERE/'cohort_concept_codex.png'
    fig.savefig(out,dpi=240)
    plt.close(fig)
    explanations=[
        '1. The hierarchy runs from a grid-cell patch mosaic to cohorts within one forest tile.',
        '2. Repeated spruce icons distinguish species identity from cohort size; heights and densities stay symbolic.',
        '3. Shaded height bands and crown-area bars explain PPA layering without implying spatial tree positions.',
        '4. Shared tile air and phenology forcing are separated from each cohort’s leaf and phenology responses.',
        '5. The CNDV comparison, LAI relation, and supplied run statistics connect the schematic to model interpretation.',
    ]
    print('\n'.join(explanations))


if __name__=='__main__':
    main()
